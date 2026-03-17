import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.log('API Error:', error.response?.status, error.response?.data);
    
    if (error.response?.status === 401) {
      // Only redirect if we're not already on the login page
      if (window.location.pathname !== '/login') {
        console.log('401 error detected, redirecting to login');
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Get WebSocket URL based on API base URL or current window location
export const getWebSocketUrl = (path = '/ws/resume-sync') => {
  let apiBase = import.meta.env.VITE_API_BASE;
  
  // If no API base is set or it's localhost, use current window location
  if (!apiBase || apiBase.includes('localhost')) {
    // Use current window location to determine WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    apiBase = `${protocol}//${host}`;
  } else {
    // Convert HTTP/HTTPS to WS/WSS
    apiBase = apiBase.replace(/^http:/, 'ws:').replace(/^https:/, 'wss:');
  }
  
  // Remove trailing slash if present
  apiBase = apiBase.replace(/\/$/, '');
  
  // Add the WebSocket path
  return `${apiBase}${path}`;
};

export default api;
