/**
 * Admin API service for managing monitored services, users, and configuration
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class AdminApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  // Helper method for API requests
  async apiRequest(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // ===== SERVICES MANAGEMENT =====
  
  async getAvailableServices() {
    return this.apiRequest('/api/admin/services');
  }

  async getMonitoredServices() {
    return this.apiRequest('/api/admin/monitored-services');
  }

  async addMonitoredService(service) {
    return this.apiRequest('/api/admin/monitored-services', {
      method: 'POST',
      body: JSON.stringify(service),
    });
  }

  async updateMonitoredService(serviceId, service) {
    return this.apiRequest(`/api/admin/monitored-services/${serviceId}`, {
      method: 'PUT',
      body: JSON.stringify(service),
    });
  }

  async removeMonitoredService(serviceId) {
    return this.apiRequest(`/api/admin/monitored-services/${serviceId}`, {
      method: 'DELETE',
    });
  }

  // ===== USERS MANAGEMENT =====
  
  async getAvailableUsers() {
    return this.apiRequest('/api/admin/users');
  }

  async getMonitoredUsers() {
    return this.apiRequest('/api/admin/monitored-users');
  }

  async addMonitoredUser(user) {
    return this.apiRequest('/api/admin/monitored-users', {
      method: 'POST',
      body: JSON.stringify(user),
    });
  }

  async updateMonitoredUser(userId, user) {
    return this.apiRequest(`/api/admin/monitored-users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(user),
    });
  }

  async removeMonitoredUser(userId) {
    return this.apiRequest(`/api/admin/monitored-users/${userId}`, {
      method: 'DELETE',
    });
  }

  // ===== TIME WINDOWS MANAGEMENT =====
  
  async getTimeWindows() {
    return this.apiRequest('/api/admin/time-windows');
  }

  async updateTimeWindows(timeWindows) {
    return this.apiRequest('/api/admin/time-windows', {
      method: 'PUT',
      body: JSON.stringify(timeWindows),
    });
  }

  // ===== SLA METRICS =====
  
  async getSlaMetrics(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const endpoint = `/api/admin/sla-metrics${queryString ? `?${queryString}` : ''}`;
    return this.apiRequest(endpoint);
  }

  // ===== CONFIGURATION =====
  
  async getAdminConfig() {
    return this.apiRequest('/api/admin/config');
  }

  // ===== THEME MANAGEMENT =====
  
  async getCurrentTheme() {
    return this.apiRequest('/api/theme/current');
  }

  async getThemeStatus() {
    return this.apiRequest('/api/theme/status');
  }

  async setManualThemeOverride(theme) {
    return this.apiRequest('/api/theme/manual-override', {
      method: 'POST',
      body: JSON.stringify(theme),
    });
  }

  async clearManualOverride() {
    return this.apiRequest('/api/theme/manual-override', {
      method: 'DELETE',
    });
  }

  async getThemeSchedules() {
    return this.apiRequest('/api/admin/theme-schedule');
  }

  async updateThemeSchedules(schedules) {
    return this.apiRequest('/api/admin/theme-schedule', {
      method: 'PUT',
      body: JSON.stringify(schedules),
    });
  }

  async getThemeSettings(themeType = null) {
    const endpoint = themeType ? 
      `/api/admin/theme-settings?theme_type=${themeType}` : 
      '/api/admin/theme-settings';
    return this.apiRequest(endpoint);
  }

  async updateThemeSettings(settings) {
    return this.apiRequest('/api/admin/theme-settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  async initializeDefaults() {
    return this.apiRequest('/api/admin/initialize-defaults', {
      method: 'POST',
    });
  }
}

// Export singleton instance
export const adminApi = new AdminApiService();
export default adminApi;
