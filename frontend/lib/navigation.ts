'use client';

import { useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { ROUTES } from './routes';

export function useAppNavigation() {
  const router = useRouter();

  const prefetchArena = useCallback(() => {
    router.prefetch(ROUTES.arena);
  }, [router]);

  const prefetchLogin = useCallback(() => {
    router.prefetch(ROUTES.login);
  }, [router]);

  const enterArena = useCallback(() => {
    router.replace(ROUTES.arena);
  }, [router]);

  const exitToLogin = useCallback(() => {
    router.replace(ROUTES.login);
  }, [router]);

  return {
    prefetchArena,
    prefetchLogin,
    enterArena,
    exitToLogin,
  };
}
