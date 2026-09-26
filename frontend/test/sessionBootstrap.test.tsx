import { screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { baseProblem, baseSession, createFakeSessionClient, wireArenaFlow } from './fakeBackend';
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
   * #378: the stored session id rides along so the backend can resume it.
   */
  it('starts a session with the stored username and session id, no chapter id', async () => {
    const client = wireArenaFlow({ session: baseSession(), problem: baseProblem() });

    renderArena(client);

    await waitFor(() => {
      expect(client.startSession).toHaveBeenCalledWith({
        username: STORED_USERNAME,
        session_id: 'sess-test',
      });
    });
  });

  /**
   * #377: the second attempt that used to retry without the chapter id is gone
   * along with the chapter id, so a failed start surfaces its error directly.
   */
  it('surfaces a failed start without attempting a second one', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const client = createFakeSessionClient({
      startSession: async () => {
        throw new Error('Session start failed');
      },
    });

    renderArena(client);

    await screen.findByText('Session start failed');
    expect(client.startSession).toHaveBeenCalledTimes(1);
    consoleErrorSpy.mockRestore();
  });
});
