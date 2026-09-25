import { clearSessionStorage, setSessionCredentials } from '@/lib/session';

/** The Username every arena test plays as, and the one its assertions name. */
export const STORED_USERNAME = 'testuser';

export function seedStoredSession(username = STORED_USERNAME, sessionId = 'sess-test') {
  setSessionCredentials(username, sessionId);
}

export function resetStoredSession() {
  clearSessionStorage();
}
