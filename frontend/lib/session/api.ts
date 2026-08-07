import api from '@/lib/api';
import type {
  AutoSolveRequest,
  ProblemResponse,
  SessionNavigateRequest,
  SessionResetRequest,
  SessionStartRequest,
  SessionState,
  SubmissionResponse,
  ProblemSubmissionRequest,
} from './types';

export const startSession = async (request: SessionStartRequest): Promise<SessionState> => {
  const response = await api.post<SessionState>('/session/start', request);
  return response.data;
};

export const navigateSession = async (request: SessionNavigateRequest): Promise<SessionState> => {
  const response = await api.post<SessionState>('/session/navigate', request);
  return response.data;
};

export const resetSession = async (request: SessionResetRequest): Promise<SessionState> => {
  const response = await api.post<SessionState>('/session/reset', request);
  return response.data;
};

export const getNextProblem = async (sessionId: string): Promise<ProblemResponse> => {
  const response = await api.get<ProblemResponse>('/problem/next', {
    params: { session_id: sessionId },
  });
  return response.data;
};

export const submitAnswer = async (request: ProblemSubmissionRequest): Promise<SubmissionResponse> => {
  const response = await api.post<SubmissionResponse>('/problem/submit', request);
  return response.data;
};

export const autoSolve = async (request: AutoSolveRequest): Promise<SubmissionResponse> => {
  const response = await api.post<SubmissionResponse>('/problem/auto-solve', request);
  return response.data;
};
