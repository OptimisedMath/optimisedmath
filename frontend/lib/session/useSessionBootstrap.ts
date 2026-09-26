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
 * A resumed session already carries its active Problem, and asking for a next
 * one would discard exactly what the Resume recovered (#378). The
 * `deconstruction_running` half is redundant — a running Deconstruction always
 * has an active Problem — and kept anyway: `/problem/next` is shut while one
 * runs, and mirroring that backend rule explicitly is cheaper than relying on
 * the two facts staying in sync by coincidence (ADR-0002).
 */
function shouldFetchProblem(session: SessionResponse): boolean {
  return !session.deconstruction_running && !session.current_problem;
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
        // The stored Username and session id, nothing else (#377): the profile
        // owns Selected chapter/topic/level (ADR-0006), so a chapter id here
        // would read as Navigation on the backend, moving the Student off the
        // Chapter they were playing and resetting Streak. The session id is
        // what lets the backend resume rather than start over (#378).
        const sessionResponse = await client.startSession({
          username: storedUsername,
          session_id: storedSessionId,
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
