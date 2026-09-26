import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it } from 'vitest';
import { getStoredSessionId, getStoredUsername } from '@/lib/session';
import { wireArenaFlow } from './fakeBackend';
import { renderArena, waitForArenaReady } from './renderArena';
import { resetStoredSession, seedStoredSession, STORED_SESSION_ID } from './testSession';

describe('Wyloguj ends the stored Session', () => {
  beforeEach(() => {
    resetStoredSession();
    seedStoredSession();
  });

  it('calls endSession for the stored id and clears credentials without waiting on it', async () => {
    const client = wireArenaFlow({
      // Never settles, so the assertions below can only pass if logging out
      // cleared credentials and navigated without awaiting endSession.
      endSession: () => new Promise<void>(() => {}),
    });

    renderArena(client);
    await waitForArenaReady(client);

    const user = userEvent.setup();
    await user.click(await screen.findByText('Wyloguj'));

    expect(client.endSession).toHaveBeenCalledWith({ session_id: STORED_SESSION_ID });
    expect(getStoredUsername()).toBeNull();
    expect(getStoredSessionId()).toBeNull();
  });

  it('does not call endSession when no session id is stored', async () => {
    const client = wireArenaFlow();

    renderArena(client);
    await waitForArenaReady(client);

    resetStoredSession();
    const user = userEvent.setup();
    await user.click(await screen.findByText('Wyloguj'));

    expect(client.endSession).not.toHaveBeenCalled();
  });
});
