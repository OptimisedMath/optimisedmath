import api from '@/lib/api';
import type { SessionClient } from './client';
import type {
  DeconstructionStepResponse,
  DeconstructionSubmissionResponse,
  ProblemResponse,
  SessionResponse,
  SubmissionResponse,
} from './types';

/** Production adapter: talks to the FastAPI backend over HTTP. */
export const httpSessionClient: SessionClient = {
  startSession: async (request) => {
    const response = await api.post<SessionResponse>('/session/start', request);
    return response.data;
  },

  navigateSession: async (request) => {
    const response = await api.post<SessionResponse>('/session/navigate', request);
    return response.data;
  },

  resetSession: async (request) => {
    const response = await api.post<SessionResponse>('/session/reset', request);
    return response.data;
  },

  getNextProblem: async (sessionId) => {
    const response = await api.get<ProblemResponse>('/problem/next', {
      params: { session_id: sessionId },
    });
    return response.data;
  },

  submitAnswer: async (request) => {
    const response = await api.post<SubmissionResponse>('/problem/submit', request);
    return response.data;
  },

  getDeconstructionStep: async (sessionId) => {
    const response = await api.get<DeconstructionStepResponse>(
      `/deconstruction/next?session_id=${encodeURIComponent(sessionId)}`
    );
    return response.data;
  },

  submitDeconstructionStep: async (request) => {
    const response = await api.post<DeconstructionSubmissionResponse>(
      '/deconstruction/submit',
      request
    );
    return response.data;
  },

  abandonDeconstruction: async (request) => {
    const response = await api.post<SessionResponse>('/deconstruction/abandon', request);
    return response.data;
  },
};
