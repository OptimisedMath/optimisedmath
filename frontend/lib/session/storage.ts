import { SESSION_STORAGE_KEYS } from './constants';

const USERNAME_KEY = SESSION_STORAGE_KEYS[0];
const SESSION_ID_KEY = SESSION_STORAGE_KEYS[1];

export function getStoredUsername(): string | null {
  return localStorage.getItem(USERNAME_KEY);
}

export function getStoredSessionId(): string | null {
  return localStorage.getItem(SESSION_ID_KEY);
}

export function setSessionCredentials(username: string, sessionId: string): void {
  localStorage.setItem(USERNAME_KEY, username);
  localStorage.setItem(SESSION_ID_KEY, sessionId);
}

export function setStoredSessionId(sessionId: string): void {
  localStorage.setItem(SESSION_ID_KEY, sessionId);
}

export function clearSessionStorage(): void {
  for (const key of SESSION_STORAGE_KEYS) {
    localStorage.removeItem(key);
  }
}
