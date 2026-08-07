import axios from 'axios';
import type { CurriculumResponse } from './types';

// Same-origin /api is proxied to the backend by Next.js (see next.config.ts).
// This avoids WiFi/corporate proxy settings intercepting direct localhost:8000 calls.
const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || '/api';

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

export default api;
