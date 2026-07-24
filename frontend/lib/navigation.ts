'use client';

import { useRouter } from 'next/navigation';
import { ROUTES } from './routes';

const SESSION_KEYS = ['username', 'session_id'] as const;

export function clearSessionStorage() {
  for (const key of SESSION_KEYS) {
    localStorage.removeItem(key);
  }
}

export function useAppNavigation() {
  const router = useRouter();

  return {
    prefetchArena: () => router.prefetch(ROUTES.arena),
    prefetchLogin: () => router.prefetch(ROUTES.login),

    enterArena: () => router.replace(ROUTES.arena),

    exitToLogin: () => router.replace(ROUTES.login),
  };
}
