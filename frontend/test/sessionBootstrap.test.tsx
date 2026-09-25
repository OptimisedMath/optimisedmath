import { waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { baseProblem, baseSession, wireArenaFlow } from './fakeBackend';
import { renderArena } from './renderArena';
import { resetStoredSession, seedStoredSession, STORED_USERNAME } from './testSession';

describe('session bootstrap', () => {
  beforeEach(() => {
    resetStoredSession();
    seedStoredSession();
  });

  /**
   * #377: the backend reads a chapter id on a start request as Navigation, which
   * moves the Student off the Chapter their profile holds and resets Streak.
   */
  it('starts a session with only the stored username, no chapter id', async () => {
    const client = wireArenaFlow({ session: baseSession(), problem: baseProblem() });

    renderArena(client);

    await waitFor(() => {
      expect(client.startSession).toHaveBeenCalledWith({ username: STORED_USERNAME });
    });
  });
});
