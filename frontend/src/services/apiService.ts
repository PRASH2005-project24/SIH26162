import axios from 'axios';

// Create axios instance with base URL from environment variable
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // You could add auth tokens here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle common error cases
    if (error.response) {
      const detail = error.response.data?.detail;
      const message = typeof detail === 'string'
        ? detail
        : `Request failed with status ${error.response.status}`;
      const apiError = new Error(message);
      Object.assign(apiError, { status: error.response.status });
      return Promise.reject(apiError);
    } else if (error.request) {
      const networkError = new Error('Network error - unable to reach server');
      Object.assign(networkError, { status: 0 });
      return Promise.reject(networkError);
    } else {
      // Error setting up request
      return Promise.reject(error);
    }
  }
);

export default apiClient;