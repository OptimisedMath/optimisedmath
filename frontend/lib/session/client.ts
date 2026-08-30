import type {
  DeconstructionAbandonRequest,
  DeconstructionStepResponse,
  DeconstructionSubmissionRequest,
  DeconstructionSubmissionResponse,
  ProblemResponse,
  SessionNavigateRequest,
  SessionResetRequest,
  SessionStartRequest,
  SessionResponse,
  SubmissionResponse,
  ProblemSubmissionRequest,
} from './types';

/**
 * The operations the app performs on a Session, in domain terms. Production
 * is wired to `httpSessionClient`; tests supply an in-memory adapter — see
 * frontend/docs/session.md.
 */
export interface SessionClient {
  startSession(request: SessionStartRequest): Promise<SessionResponse>;
  navigateSession(request: SessionNavigateRequest): Promise<SessionResponse>;
  resetSession(request: SessionResetRequest): Promise<SessionResponse>;
  getNextProblem(sessionId: string): Promise<ProblemResponse>;
  submitAnswer(request: ProblemSubmissionRequest): Promise<SubmissionResponse>;
  getDeconstructionStep(sessionId: string): Promise<DeconstructionStepResponse>;
  submitDeconstructionStep(
    request: DeconstructionSubmissionRequest
  ): Promise<DeconstructionSubmissionResponse>;
  abandonDeconstruction(request: DeconstructionAbandonRequest): Promise<SessionResponse>;
}
