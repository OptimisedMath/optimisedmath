import { waitFor } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import type { SessionClient } from '@/lib/session';
import { baseProblem, baseSession, wireArenaFlow } from './fakeBackend';
import { renderArena } from './renderArena';
import { resetStoredSession, seedStoredSession } from './testSession';

async function waitForArenaReady(client: SessionClient) {
  await waitFor(() => {
    expect(client.startSession).toHaveBeenCalled();
    expect(client.getNextProblem).toHaveBeenCalled();
  });
}

describe('session bootstrap', () => {
  it('starts a session with only the stored username, no chapter id', async () => {
    resetStoredSession();
    seedStoredSession();

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

    expect(client.startSession).toHaveBeenCalledWith({ username: 'testuser' });
  });
});
