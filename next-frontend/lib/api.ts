import axios from 'axios';
import type {
  CurriculumResponse,
  GameState,
  ProblemResponse,
  SubmissionResponse,
  SessionStartRequest,
  SessionNavigateRequest,
  ProblemSubmissionRequest,
} from './types';

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: apiBaseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for error handling
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const errorMessage = error.response?.data?.detail || error.message || 'An error occurred';
    console.error('API Error:', errorMessage);
    return Promise.reject(new Error(errorMessage));
  }
);

// API Functions
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

export default api;
