import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it } from 'vitest';
import { onGet, onPost, resetFakeBackend, mockApi } from './apiMock';
import {
  baseProblem,
  baseSession,
  defaultNavigation,
  wireArenaFlow,
} from './fakeBackend';
import { renderArena } from './renderArena';
import { resetStoredSession, seedStoredSession } from './testSession';

async function submitTypedAnswer(answer: string) {
  const user = userEvent.setup();
  const input = await screen.findByPlaceholderText('Wpisz wynik...');
  await user.clear(input);
  await user.type(input, answer);
  expect(input).toHaveValue(answer);
  await user.click(screen.getByRole('button', { name: /Sprawdź odpowiedź/ }));
}

async function waitForArenaReady() {
  await waitFor(() => {
    expect(mockApi.post).toHaveBeenCalledWith('/session/start', expect.anything());
    expect(mockApi.get).toHaveBeenCalledWith('/problem/next', expect.anything());
  });
  await waitFor(() => {
    expect(screen.queryByText('Ładowanie zadania...')).not.toBeInTheDocument();
  });
}

describe('ADR-0002 leak locks', () => {
  beforeEach(() => {
    resetFakeBackend();
    resetStoredSession();
    seedStoredSession();
  });

  it('renders full streak meter from payload during level-completion feedback', async () => {
    const session = baseSession({
      current_input_mode: 'input',
      streak: 0,
      streak_meter: 2,
      max_streak: 3,
    });
    const problem = baseProblem();

    wireArenaFlow({
      session,
      problem,
      onSubmit: () => ({
        is_correct: true,
        feedback: 'Poziom ukończony!',
        state: {
          ...session,
          problem_answered: true,
          level_completed: true,
          streak: 0,
          streak_meter: 3,
          can_submit: false,
          can_next_problem: true,
          feedback_type: 'success',
          feedback_msg: 'Poziom ukończony!',
          current_problem: problem,
        },
      }),
    });

    renderArena();
    await waitForArenaReady();
    await submitTypedAnswer('4');

    await waitFor(() => {
      expect(screen.getByText('Poziom ukończony!')).toBeInTheDocument();
    });

    const scoreboard = screen.getByText('Postęp do kolejnego poziomu:').parentElement as HTMLElement;
    expect(within(scoreboard).getAllByText('⭐').length).toBe(3);
    expect(screen.getByText('3/3 gwiazdek')).toBeInTheDocument();
  });

  it('renders radio mode from session payload alone for radio-only topics', async () => {
    const session = baseSession({
      current_input_mode: 'radio',
      navigation: {
        ...defaultNavigation()!,
        radio_only: true,
      },
    });
    const problem = baseProblem({
      answer_options: ['1', '2', '3', '4'],
      correct_answer: '2',
    });

    wireArenaFlow({
      session,
      problem,
      onSubmit: () => ({
        is_correct: true,
        feedback: 'OK',
        state: {
          ...session,
          problem_answered: true,
          can_submit: false,
          can_next_problem: true,
          feedback_type: 'success',
          feedback_msg: 'OK',
          current_problem: problem,
        },
      }),
    });

    renderArena();
    await waitForArenaReady();

    const problemCard = screen.getByText('Zadanie').closest('.glass-card-strong') as HTMLElement;
    await waitFor(() => {
      expect(screen.queryByPlaceholderText('Wpisz wynik...')).not.toBeInTheDocument();
      expect(within(problemCard).getAllByRole('button').length).toBeGreaterThanOrEqual(4);
    });
  });

  it('styles correct feedback from payload feedback_type', async () => {
    const session = baseSession();
    const problem = baseProblem();

    wireArenaFlow({
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

    renderArena();
    await waitForArenaReady();
    await submitTypedAnswer('4');

    const badge = await screen.findByText('Brawo!');
    expect(badge).toHaveAttribute('data-feedback-type', 'success');
    expect(badge.className).toContain('bg-emerald-100');
  });

  it('styles trap feedback from payload feedback_type', async () => {
    const session = baseSession();
    const problem = baseProblem();

    wireArenaFlow({
      session,
      problem,
      onSubmit: () => ({
        is_correct: false,
        feedback: 'Trap feedback',
        state: {
          ...session,
          problem_answered: true,
          can_submit: false,
          can_next_problem: true,
          feedback_type: 'warning',
          feedback_msg: 'Trap feedback',
          current_problem: problem,
        },
      }),
    });

    renderArena();
    await waitForArenaReady();
    await submitTypedAnswer('3');

    const trapBadge = await screen.findByText('Trap feedback');
    expect(trapBadge).toHaveAttribute('data-feedback-type', 'warning');
    expect(trapBadge.className).toContain('bg-red-100');
  });

  it('styles wrong feedback from payload feedback_type', async () => {
    const session = baseSession({ session_id: 'sess-wrong' });
    const problem = baseProblem({ problem_id: 'prob-2' });

    wireArenaFlow({
      session,
      problem,
      onSubmit: () => ({
        is_correct: false,
        feedback: 'Wrong feedback',
        state: {
          ...session,
          problem_answered: true,
          can_submit: false,
          can_next_problem: true,
          feedback_type: 'warning',
          feedback_msg: 'Wrong feedback',
          current_problem: problem,
        },
      }),
    });

    renderArena();
    await waitForArenaReady();
    await submitTypedAnswer('3');

    const wrongBadge = await screen.findByText('Wrong feedback');
    expect(wrongBadge).toHaveAttribute('data-feedback-type', 'warning');
    expect(wrongBadge.className).toContain('bg-red-100');
  });

  it('styles soft error feedback from payload feedback_type without inventing a fallback', async () => {
    const session = baseSession();
    const problem = baseProblem();

    wireArenaFlow({
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

    renderArena();
    await waitForArenaReady();
    await submitTypedAnswer('4/');

    const softError = await screen.findByText('Zły format odpowiedzi');
    expect(softError).toHaveAttribute('data-feedback-type', 'info');
    expect(softError.className).toContain('border-amber-200');
    expect(softError.className).toContain('text-amber-700');
  });

  it('clears feedback and canNextProblem immediately after navigating, before the new state loads', async () => {
    const session = baseSession();
    const problem = baseProblem();

    wireArenaFlow({
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

    renderArena();
    await waitForArenaReady();
    await submitTypedAnswer('4');

    await screen.findByText('Brawo!');
    expect(screen.getByRole('button', { name: /Następne zadanie/ })).toBeInTheDocument();

    const levelSelect = screen.getByLabelText('Poziom');
    fireEvent.change(levelSelect, { target: { value: '2' } });

    expect(screen.queryByText('Brawo!')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Następne zadanie/ })).not.toBeInTheDocument();

    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalledWith('/session/navigate', expect.anything());
    });
  });

  it('derives Feedback purely from SessionState.feedback_type/feedback_msg without any separate hook-state trigger', async () => {
    const session = baseSession({
      can_next_problem: true,
      problem_answered: true,
      feedback_type: 'success',
      feedback_msg: 'Zaliczone od razu!',
    });
    const problem = baseProblem();

    onPost('/session/start', () => session);
    onGet('/problem/next', () => ({
      problem,
      state: {
        ...session,
        current_problem: problem,
        can_submit: false,
        can_next_problem: true,
      },
    }));

    renderArena();
    await waitForArenaReady();

    const badge = await screen.findByText('Zaliczone od razu!');
    expect(badge).toHaveAttribute('data-feedback-type', 'success');
    expect(badge.className).toContain('bg-emerald-100');
    expect(screen.getByRole('button', { name: /Następne zadanie/ })).toBeInTheDocument();
  });
});
