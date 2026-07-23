import axios from 'axios';
import type {
  AutoSolveRequest,
  CurriculumResponse,
  GameState,
  ProblemResponse,
  SubmissionResponse,
  SessionStartRequest,
  SessionNavigateRequest,
  SessionResetRequest,
  ProblemSubmissionRequest,
} from './types';

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: apiBaseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const errorMessage = error.response?.data?.detail || error.message || 'An error occurred';
    console.error('API Error:', errorMessage);
    console.error('Full error details:', {
      message: error.message,
      code: error.code,
      response: error.response?.data,
      config: error.config?.url,
      status: error.response?.status
    });
    return Promise.reject(new Error(errorMessage));
  }
);

export const getCurriculum = async (): Promise<CurriculumResponse> => {
  const response = await api.get<CurriculumResponse>('/curriculum');
  return response.data;
};

export const startSession = async (request: SessionStartRequest): Promise<GameState> => {
  const response = await api.post<GameState>('/session/start', request);
  return response.data;
};

export const navigateSession = async (request: SessionNavigateRequest): Promise<GameState> => {
  const response = await api.post<GameState>('/session/navigate', request);
  return response.data;
};

export const resetSession = async (request: SessionResetRequest): Promise<GameState> => {
  const response = await api.post<GameState>('/session/reset', request);
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

export default api;
