import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { SessionResponse } from '@/lib/session';
import {
  baseDeconstructionStep,
  baseProblem,
  baseSession,
  createFakeSessionClient,
  withProblem,
  withoutCorrectAnswer,
} from './fakeBackend';
import { renderArena } from './renderArena';
import { resetStoredSession, seedStoredSession } from './testSession';

/**
 * The Session a page load gets back while a Deconstruction is already running:
 * both gates shut, and the triggering Problem stripped of its `correct_answer`
 * exactly as the backend serves it.
 */
function resumedMidDeconstruction(): SessionResponse {
  return withProblem(
    baseSession({
      can_submit: false,
      can_next_problem: false,
      deconstruction_running: true,
    }),
    withoutCorrectAnswer(baseProblem({ problem_id: 'prob-trigger' }))
  );
}

describe('resuming a session mid-Deconstruction', () => {
  beforeEach(() => {
    resetStoredSession();
    seedStoredSession();
  });

  it('arms the takeover without asking for a next Problem the backend would refuse', async () => {
    // `/problem/next` is 403 while a Deconstruction runs; bootstrapping into one
    // must not spend that request, nor paint its error over the walkthrough.
    const running = resumedMidDeconstruction();
    const getNextProblem = vi.fn(async () => {
      throw new Error('Next problem is unavailable while a Deconstruction is active');
    });
    const client = createFakeSessionClient({
      startSession: async () => running,
      getNextProblem,
      getDeconstructionStep: async () => baseDeconstructionStep(),
    });

    renderArena(client);

    await waitFor(() => {
      expect(client.startSession).toHaveBeenCalled();
    });
    await screen.findByText('Zatrzymajmy się na chwilę');
    expect(getNextProblem).not.toHaveBeenCalled();
    expect(
      screen.queryByText(/Next problem is unavailable/)
    ).not.toBeInTheDocument();
  });

  it('renders the intro card immediately, with no pause phase to tap through', async () => {
    // A Resume's pause moment already happened, before the refresh — see #382.
    const running = resumedMidDeconstruction();
    const client = createFakeSessionClient({
      startSession: async () => running,
      getDeconstructionStep: async () => baseDeconstructionStep(),
    });

    renderArena(client);

    await screen.findByText('Zatrzymajmy się na chwilę');
    expect(screen.queryByLabelText('Przejdź dalej')).not.toBeInTheDocument();
  });

  it('continues from the intro card onto the step the Student was on, not the first one', async () => {
    const running = resumedMidDeconstruction();
    const midStep = baseDeconstructionStep({ step_index: 2, total_steps: 4 });
    const client = createFakeSessionClient({
      startSession: async () => running,
      getDeconstructionStep: async () => midStep,
    });

    renderArena(client);

    await screen.findByText('Zatrzymajmy się na chwilę');
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /Zaczynajmy/ }));

    await screen.findByText('krok 3 z 4');
  });
});
