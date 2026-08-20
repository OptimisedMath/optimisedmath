import api from '@/lib/api';
import type { SessionClient } from './client';
import type { ProblemResponse, SessionState, SubmissionResponse } from './types';

/** Production adapter: talks to the FastAPI backend over HTTP. */
export const httpSessionClient: SessionClient = {
  startSession: async (request) => {
    const response = await api.post<SessionState>('/session/start', request);
    return response.data;
  },

  navigateSession: async (request) => {
    const response = await api.post<SessionState>('/session/navigate', request);
    return response.data;
  },

  resetSession: async (request) => {
    const response = await api.post<SessionState>('/session/reset', request);
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
};
