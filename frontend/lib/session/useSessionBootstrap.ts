'use client';

import { useEffect, useState } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import { useAppNavigation } from '@/lib/navigation';
import { PREFERRED_CHAPTER_ID } from './constants';
import { startSession } from './api';
import { reportError } from './errors';
import { getStoredSessionId, getStoredUsername, setStoredSessionId } from './storage';
import type { SessionState } from './types';

interface UseSessionBootstrapOptions {
  setSessionState: Dispatch<SetStateAction<SessionState | null>>;
  setError: Dispatch<SetStateAction<string | null>>;
  onSessionStarted: (sessionId: string) => void;
}

/**
 * Reads stored credentials and starts a session on mount, falling back to the
 * plain (no preferred-chapter) start request when the preferred chapter is
 * unavailable. Internal to lib/session/ — composed by useSession().
 */
export function useSessionBootstrap({
  setSessionState,
  setError,
  onSessionStarted,
}: UseSessionBootstrapOptions) {
  const { exitToLogin, prefetchLogin } = useAppNavigation();
  const [needsLogin, setNeedsLogin] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const initializeGame = async () => {
      const storedUsername = getStoredUsername();
      const storedSessionId = getStoredSessionId();

      if (!storedUsername || !storedSessionId) {
        setNeedsLogin(true);
        exitToLogin();
        return;
      }

      try {
        const sessionResponse = await startSession({
          username: storedUsername,
          selected_chapter_id: PREFERRED_CHAPTER_ID,
        });
        if (!isMounted) return;

        setStoredSessionId(sessionResponse.session_id);
        setSessionState(sessionResponse);
        setError(null);
        onSessionStarted(sessionResponse.session_id);
      } catch (err) {
        if (!isMounted) return;

        try {
          const fallbackSession = await startSession({ username: storedUsername });
          if (!isMounted) return;

          setStoredSessionId(fallbackSession.session_id);
          setSessionState(fallbackSession);
          setError(null);
          onSessionStarted(fallbackSession.session_id);
          return;
        } catch {
          // Fall through to the original error message.
        }

        reportError(setError, err, 'Failed to start session', 'Error starting session:');
      }
    };

    initializeGame();

    return () => {
      isMounted = false;
    };
  }, [setSessionState, setError, onSessionStarted, exitToLogin]);

  useEffect(() => {
    prefetchLogin();
  }, [prefetchLogin]);

  return { needsLogin };
}
