import axios, { AxiosError } from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.trim() || "http://localhost:8000";

/**
 * Create Axios instance
 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // AI responses can take long
});

/**
 * REQUEST INTERCEPTOR
 */
apiClient.interceptors.request.use(
  (config) => {
    // Remove default JSON header for FormData requests
    if (config.data instanceof FormData) {
      delete config.headers["Content-Type"];
    }

    if (import.meta.env.DEV) {
      console.log(
        `%c[API REQUEST]`,
        "color:#22c55e;font-weight:bold",
        config.method?.toUpperCase(),
        config.url
      );
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/**
 * RESPONSE INTERCEPTOR
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const normalizedError = {
      status: error.response?.status || 500,
      message:
        (error.response?.data as any)?.detail ||
        error.message ||
        "Unknown API error",
    };

    if (import.meta.env.DEV) {
      console.error(
        "%c[API ERROR]",
        "color:#ef4444;font-weight:bold",
        normalizedError
      );
    }

    return Promise.reject(normalizedError);
  }
);
