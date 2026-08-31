import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
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

describe('resuming a session mid-Deconstruction', () => {
  beforeEach(() => {
    resetStoredSession();
    seedStoredSession();
  });

  it('arms the takeover without asking for a next Problem the backend would refuse', async () => {
    // `/problem/next` is 403 while a Deconstruction runs; bootstrapping into one
    // must not spend that request, nor paint its error over the walkthrough.
    const running = withProblem(
      {
        ...baseSession(),
        can_submit: false,
        can_next_problem: false,
        deconstruction_running: true,
      },
      withoutCorrectAnswer(baseProblem({ problem_id: 'prob-trigger' }))
    );
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
    const user = userEvent.setup();
    await user.click(await screen.findByLabelText('Przejdź dalej'));
    await screen.findByText('Zatrzymajmy się na chwilę');
    expect(getNextProblem).not.toHaveBeenCalled();
    expect(
      screen.queryByText(/Next problem is unavailable/)
    ).not.toBeInTheDocument();
  });
});
