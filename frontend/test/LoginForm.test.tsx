import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it } from 'vitest';
import {
  SessionClientProvider,
  getStoredSessionId,
  getStoredUsername,
  setSessionCredentials,
} from '@/lib/session';
import LoginForm from '@/components/LoginForm';
import { baseSession, createFakeSessionClient } from './fakeBackend';
import { resetStoredSession } from './testSession';

async function submitUsername(username: string) {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText('Twoje imię:'), username);
  await user.click(screen.getByRole('button', { name: /Rozpocznij naukę/ }));
}

describe('logging in ends any stored Session', () => {
  beforeEach(() => {
    resetStoredSession();
  });

  it('calls endSession for a stored id before starting the new Session', async () => {
    setSessionCredentials('old-user', 'stale-sess');
    const calls: string[] = [];
    const session = baseSession({ session_id: 'fresh-sess' });
    const client = createFakeSessionClient({
      endSession: async () => {
        calls.push('endSession');
      },
      startSession: async () => {
        calls.push('startSession');
        return session;
      },
    });

    render(
      <SessionClientProvider client={client}>
        <LoginForm />
      </SessionClientProvider>
    );
    await submitUsername('Janek');

    expect(client.endSession).toHaveBeenCalledWith({ session_id: 'stale-sess' });
    expect(calls).toEqual(['endSession', 'startSession']);
    expect(getStoredSessionId()).toBe('fresh-sess');
    expect(getStoredUsername()).toBe('Janek');
  });

  it('does not call endSession when no session id is stored', async () => {
    const session = baseSession({ session_id: 'fresh-sess' });
    const client = createFakeSessionClient({
      startSession: async () => session,
    });

    render(
      <SessionClientProvider client={client}>
        <LoginForm />
      </SessionClientProvider>
    );
    await submitUsername('Janek');

    expect(client.endSession).not.toHaveBeenCalled();
    expect(client.startSession).toHaveBeenCalledWith({ username: 'Janek' });
  });
});
