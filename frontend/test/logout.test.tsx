import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { SessionClient } from '@/lib/session';
import { getStoredSessionId, getStoredUsername } from '@/lib/session';
import { baseProblem, baseSession, wireArenaFlow } from './fakeBackend';
import { renderArena } from './renderArena';
import { resetStoredSession, seedStoredSession } from './testSession';

async function waitForArenaReady(client: SessionClient) {
  await waitFor(() => {
    expect(client.startSession).toHaveBeenCalled();
    expect(client.getNextProblem).toHaveBeenCalled();
  });
  await waitFor(() => {
    expect(screen.queryByText('Ładowanie zadania...')).not.toBeInTheDocument();
  });
}

describe('Wyloguj ends the stored Session', () => {
  beforeEach(() => {
    resetStoredSession();
    seedStoredSession();
  });

  it('calls endSession for the stored id and clears credentials without waiting on it', async () => {
    const session = baseSession();
    const problem = baseProblem();
    let resolveEndSession: () => void = () => {};
    const endSession = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          resolveEndSession = resolve;
        })
    );

    const client = wireArenaFlow({
      session,
      problem,
      onSubmit: () => {
        throw new Error('not exercised');
      },
    });
    client.endSession = endSession;

    renderArena(client);
    await waitForArenaReady(client);

    const user = userEvent.setup();
    await user.click(await screen.findByText('Wyloguj'));

    expect(endSession).toHaveBeenCalledWith({ session_id: session.session_id });
    // Navigation and credential-clearing never waited on endSession's promise.
    expect(getStoredUsername()).toBeNull();
    expect(getStoredSessionId()).toBeNull();

    resolveEndSession();
  });

  it('does not call endSession when no session id is stored', async () => {
    const session = baseSession();
    const problem = baseProblem();
    const client = wireArenaFlow({
      session,
      problem,
      onSubmit: () => {
        throw new Error('not exercised');
      },
    });

    renderArena(client);
    await waitForArenaReady(client);

    resetStoredSession();
    const user = userEvent.setup();
    await user.click(await screen.findByText('Wyloguj'));

    expect(client.endSession).not.toHaveBeenCalled();
  });
});
