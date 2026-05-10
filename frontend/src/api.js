import axios from 'axios';

// This tells React exactly where your Python server is living
const api = axios.create({
  baseURL: 'http://localhost:8000',
});

export default api;