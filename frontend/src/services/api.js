/**
 * API service for HTTP requests to the backend
 */
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method.toUpperCase()} request to:`, config.url);
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.data);
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

class ApiService {
  // Get device status
  async getDevicesStatus() {
    try {
      const response = await apiClient.get('/devices/status');
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch devices status: ${error.message}`);
    }
  }

  // Get access logs
  async getAccessLogs(limit = 100) {
    try {
      const response = await apiClient.get('/access_logs', {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch access logs: ${error.message}`);
    }
  }

  // Simulate access attempt (for testing)
  async simulateAccessAttempt(deviceId, userCardId, command = 'open') {
    try {
      const response = await apiClient.post('/access_log', {
        device_id: deviceId,
        user_card_id: userCardId,
        command: command.toLowerCase() // Ensure lowercase to match backend enum
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to simulate access attempt: ${error.message}`);
    }
  }

  // Health check
  async healthCheck() {
    try {
      const response = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      throw new Error(`Health check failed: ${error.message}`);
    }
  }
}

// Export singleton instance
export const apiService = new ApiService();