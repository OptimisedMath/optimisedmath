'use client';

import { useEffect, useState } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import { useAppNavigation } from '@/lib/navigation';
import { useSessionClient } from './SessionClientContext';
import { reportError } from './errors';
import { getStoredSessionId, getStoredUsername, setStoredSessionId } from './storage';
import type { SessionResponse } from './types';

interface UseSessionBootstrapOptions {
  setSessionState: Dispatch<SetStateAction<SessionResponse | null>>;
  setError: Dispatch<SetStateAction<string | null>>;
  onSessionStarted: (sessionId: string) => void;
}

/**
 * A resumed session can come back mid-Deconstruction, and `/problem/next` is
 * shut while one runs — asking anyway only buys a 403 and an error banner over
 * the takeover that is about to arm off `deconstruction_running`.
 */
function shouldFetchProblem(session: SessionResponse): boolean {
  return !session.deconstruction_running;
}

/**
 * Reads stored credentials and starts a session on mount. Internal to
 * lib/session/ — composed by useSession().
 */
export function useSessionBootstrap({
  setSessionState,
  setError,
  onSessionStarted,
}: UseSessionBootstrapOptions) {
  const { exitToLogin, prefetchLogin } = useAppNavigation();
  const client = useSessionClient();
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
        // The stored Username and nothing else (#377): the profile owns Selected
        // chapter/topic/level (ADR-0006), so a chapter id here would read as
        // Navigation on the backend, moving the Student off the Chapter they were
        // playing and resetting Streak.
        const sessionResponse = await client.startSession({ username: storedUsername });
        if (!isMounted) return;

        setStoredSessionId(sessionResponse.session_id);
        setSessionState(sessionResponse);
        setError(null);
        if (shouldFetchProblem(sessionResponse)) {
          onSessionStarted(sessionResponse.session_id);
        }
      } catch (err) {
        if (!isMounted) return;

        reportError(setError, err, 'Failed to start session', 'Error starting session:');
      }
    };

    initializeGame();

    return () => {
      isMounted = false;
    };
  }, [setSessionState, setError, onSessionStarted, exitToLogin, client]);

  useEffect(() => {
    prefetchLogin();
  }, [prefetchLogin]);

  return { needsLogin };
}
