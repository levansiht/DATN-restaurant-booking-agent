import axios from 'axios';
import { ADMIN_LOGIN_PATH } from "../constants/routes.js";

const ADMIN_ACCESS_TOKEN_KEY = 'admin_access_token';
const ADMIN_REFRESH_TOKEN_KEY = 'admin_refresh_token';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(ADMIN_ACCESS_TOKEN_KEY);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh and errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 errors (unauthorized)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem(ADMIN_REFRESH_TOKEN_KEY);
        if (refreshToken) {
          const refreshResponse = await axios.post(
            `${api.defaults.baseURL}/auth/token/refresh`,
            { refresh: refreshToken }
          );

          const access =
            refreshResponse.data?.data?.access ||
            refreshResponse.data?.data?.access_token;
          if (!access) {
            throw new Error('Refresh token response is missing access token');
          }
          localStorage.setItem(ADMIN_ACCESS_TOKEN_KEY, access);

          // Retry the original request with new token
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem(ADMIN_ACCESS_TOKEN_KEY);
        localStorage.removeItem(ADMIN_REFRESH_TOKEN_KEY);
        window.location.href = ADMIN_LOGIN_PATH;
        return Promise.reject(refreshError);
      }
    }

    // Handle other errors
    if (error.response) {
      // Server responded with error status
      const errorMessage = error.response.data?.message || 
                          error.response.data?.detail || 
                          `Server error: ${error.response.status}`;
      console.error('API Error:', errorMessage);
    } else if (error.request) {
      // Request was made but no response received
      console.error('Network Error:', 'No response from server');
    } else {
      // Something else happened
      console.error('Request Error:', error.message);
    }

    return Promise.reject(error);
  }
);

export default api;
