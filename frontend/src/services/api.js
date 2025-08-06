/**
 * API service for Trio Monitor frontend
 * Handles all communication with the backend API
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Response Error:', error);
    
    if (error.response?.status === 503) {
      console.warn('Service temporarily unavailable - using cached data');
    } else if (error.response?.status >= 500) {
      console.error('Server error occurred');
    } else if (error.code === 'ECONNABORTED') {
      console.error('Request timeout');
    }
    
    return Promise.reject(error);
  }
);

/**
 * API service class with all endpoint methods
 */
class ApiService {
  /**
   * Get complete dashboard data
   */
  async getDashboardData() {
    try {
      const response = await api.get('/api/dashboard');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      throw error;
    }
  }

  /**
   * Get current agent states
   */
  async getAgents() {
    try {
      const response = await api.get('/api/agents');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch agents:', error);
      throw error;
    }
  }

  /**
   * Get current queue metrics
   */
  async getQueues() {
    try {
      const response = await api.get('/api/queues');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch queues:', error);
      throw error;
    }
  }

  /**
   * Get service level metrics
   */
  async getServiceLevel() {
    try {
      const response = await api.get('/api/service-level');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch service level:', error);
      throw error;
    }
  }

  /**
   * Get current alerts
   */
  async getAlerts() {
    try {
      const response = await api.get('/api/alerts');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
      throw error;
    }
  }

  /**
   * Get system statistics
   */
  async getStats() {
    try {
      const response = await api.get('/api/stats');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      throw error;
    }
  }

  /**
   * Get historical data for a queue
   */
  async getHistoricalData(queueId, hours = 24) {
    try {
      const response = await api.get(`/api/historical/${queueId}?hours=${hours}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch historical data:', error);
      throw error;
    }
  }

  /**
   * Acknowledge an alert
   */
  async acknowledgeAlert(alertId) {
    try {
      const response = await api.post(`/api/alerts/${alertId}/acknowledge`);
      return response.data;
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
      throw error;
    }
  }

  /**
   * Health check
   */
  async healthCheck() {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }
}

// Export singleton instance
export default new ApiService();
