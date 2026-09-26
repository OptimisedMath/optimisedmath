import { clearSessionStorage, setSessionCredentials } from '@/lib/session';

/** The Username every arena test plays as, and the one its assertions name. */
export const STORED_USERNAME = 'testuser';

/** The stored session id every arena test resumes from, and its assertions name. */
export const STORED_SESSION_ID = 'sess-test';

export function seedStoredSession(username = STORED_USERNAME, sessionId = STORED_SESSION_ID) {
  setSessionCredentials(username, sessionId);
}

export function resetStoredSession() {
  clearSessionStorage();
}
