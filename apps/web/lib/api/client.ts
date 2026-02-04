import axios from "axios";

// API Base URL - configure based on environment
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// Create axios instance with default config
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor (for future auth tokens)
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token here when implemented
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      const errorMessage = error.response.data?.error || error.message;
      console.error("API Error:", errorMessage);
      
      // Handle specific status codes
      if (error.response.status === 401) {
        // Handle unauthorized (future auth)
        console.error("Unauthorized access");
      } else if (error.response.status === 404) {
        console.error("Resource not found");
      } else if (error.response.status === 500) {
        console.error("Server error");
      }
    } else if (error.request) {
      // Request made but no response
      console.error("No response from server");
    } else {
      // Error in request setup
      console.error("Request error:", error.message);
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
