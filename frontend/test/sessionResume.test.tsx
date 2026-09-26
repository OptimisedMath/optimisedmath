import { screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { baseProblem, baseSession, createFakeSessionClient, withProblem } from './fakeBackend';
import { renderArena, waitForArenaReady } from './renderArena';
import { resetStoredSession, seedStoredSession } from './testSession';

describe('resuming a session (#378)', () => {
  beforeEach(() => {
    resetStoredSession();
    seedStoredSession();
  });

  it('renders the revived Problem and Feedback without asking for a next Problem', async () => {
    const problem = baseProblem({ question: 'Resumed question' });
    const resumed = withProblem(
      { ...baseSession(), can_submit: false, can_next_problem: true, feedback_type: 'success', feedback_msg: 'Resumed feedback' },
      problem
    );
    const getNextProblem = vi.fn(async () => {
      throw new Error('Next problem should not be requested on a resume with an active Problem');
    });
    const client = createFakeSessionClient({
      startSession: async () => resumed,
      getNextProblem,
    });

    renderArena(client);

    await waitFor(() => {
      expect(client.startSession).toHaveBeenCalled();
    });
    await screen.findByText('Resumed feedback');
    expect(getNextProblem).not.toHaveBeenCalled();
  });

  it('still requests a Problem when the resumed Session has none', async () => {
    const client = createFakeSessionClient({
      startSession: async () => baseSession(),
      getNextProblem: async () => ({
        problem: baseProblem(),
        state: { ...withProblem(baseSession(), baseProblem()), can_submit: true, can_next_problem: false },
      }),
    });

    renderArena(client);

    await waitForArenaReady(client);
    expect(client.getNextProblem).toHaveBeenCalled();
  });
});
