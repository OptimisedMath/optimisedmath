import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it } from 'vitest';
import type { SessionClient } from '@/lib/session';
import { baseProblem, baseSession, wireArenaFlow } from './fakeBackend';
import { renderArena } from './renderArena';
import { resetStoredSession, seedStoredSession } from './testSession';

async function submitTypedAnswer(answer: string) {
  const user = userEvent.setup();
  const input = await screen.findByPlaceholderText('Wpisz wynik...');
  await user.clear(input);
  await user.type(input, answer);
  await user.click(screen.getByRole('button', { name: /Sprawdź odpowiedź/ }));
}

async function waitForArenaReady(client: SessionClient) {
  await waitFor(() => {
    expect(client.startSession).toHaveBeenCalled();
    expect(client.getNextProblem).toHaveBeenCalled();
  });
  await waitFor(() => {
    expect(screen.queryByText('Ładowanie zadania...')).not.toBeInTheDocument();
  });
}

describe('answerLocked derived from feedbackPhase', () => {
  beforeEach(() => {
    resetStoredSession();
    seedStoredSession();
  });

  it('keeps inputs and auto-solve interactive during soft_error phase', async () => {
    const session = baseSession({ admin_mode: true });
    const problem = baseProblem();

    const client = wireArenaFlow({
      session,
      problem,
      onSubmit: () => ({
        is_correct: false,
        feedback: 'Zły format odpowiedzi',
        state: {
          ...session,
          problem_answered: false,
          can_submit: true,
          can_next_problem: false,
          feedback_type: 'info',
          feedback_msg: 'Zły format odpowiedzi',
          current_problem: problem,
        },
      }),
    });

    renderArena(client);
    await waitForArenaReady(client);
    await submitTypedAnswer('4/');

    await screen.findByText('Zły format odpowiedzi');

    const input = screen.getByPlaceholderText('Wpisz wynik...');
    expect(input).not.toBeDisabled();
    expect(screen.getByRole('button', { name: /Sprawdź odpowiedź/ })).toBeEnabled();
    expect(screen.getByRole('button', { name: /Auto-Solve/ })).toBeEnabled();
  });

  it('locks inputs and hides auto-solve during answer_locked phase', async () => {
    const session = baseSession({ admin_mode: true });
    const problem = baseProblem();

    const client = wireArenaFlow({
      session,
      problem,
      onSubmit: () => ({
        is_correct: true,
        feedback: 'Brawo!',
        state: {
          ...session,
          problem_answered: true,
          can_submit: false,
          can_next_problem: true,
          feedback_type: 'success',
          feedback_msg: 'Brawo!',
          current_problem: problem,
        },
      }),
    });

    renderArena(client);
    await waitForArenaReady(client);
    await submitTypedAnswer('4');

    await screen.findByText('Brawo!');

    expect(screen.queryByPlaceholderText('Wpisz wynik...')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Sprawdź odpowiedź/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Auto-Solve/ })).not.toBeInTheDocument();
  });
});
