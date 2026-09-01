'use client';

import { useEffect, useState } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import { useAppNavigation } from '@/lib/navigation';
import { PREFERRED_CHAPTER_ID } from './constants';
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
        const sessionResponse = await client.startSession({
          username: storedUsername,
          selected_chapter_id: PREFERRED_CHAPTER_ID,
        });
        if (!isMounted) return;

        setStoredSessionId(sessionResponse.session_id);
        setSessionState(sessionResponse);
        setError(null);
        if (shouldFetchProblem(sessionResponse)) {
          onSessionStarted(sessionResponse.session_id);
        }
      } catch (err) {
        if (!isMounted) return;

        try {
          const fallbackSession = await client.startSession({ username: storedUsername });
          if (!isMounted) return;

          setStoredSessionId(fallbackSession.session_id);
          setSessionState(fallbackSession);
          setError(null);
          if (shouldFetchProblem(fallbackSession)) {
            onSessionStarted(fallbackSession.session_id);
          }
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
  }, [setSessionState, setError, onSessionStarted, exitToLogin, client]);

  useEffect(() => {
    prefetchLogin();
  }, [prefetchLogin]);

  return { needsLogin };
}
