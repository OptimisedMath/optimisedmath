import { clearSessionStorage, setSessionCredentials } from '@/lib/session';

export function seedStoredSession(
  username = 'testuser',
  sessionId = 'sess-test'
) {
  setSessionCredentials(username, sessionId);
}

export function resetStoredSession() {
  clearSessionStorage();
}
