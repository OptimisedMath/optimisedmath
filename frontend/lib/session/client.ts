import type {
  ProblemResponse,
  SessionNavigateRequest,
  SessionResetRequest,
  SessionStartRequest,
  SessionState,
  SubmissionResponse,
  ProblemSubmissionRequest,
} from './types';

/**
 * The operations the app performs on a Session, in domain terms. Production
 * is wired to `httpSessionClient`; tests supply an in-memory adapter — see
 * frontend/docs/session.md.
 */
export interface SessionClient {
  startSession(request: SessionStartRequest): Promise<SessionState>;
  navigateSession(request: SessionNavigateRequest): Promise<SessionState>;
  resetSession(request: SessionResetRequest): Promise<SessionState>;
  getNextProblem(sessionId: string): Promise<ProblemResponse>;
  submitAnswer(request: ProblemSubmissionRequest): Promise<SubmissionResponse>;
}
