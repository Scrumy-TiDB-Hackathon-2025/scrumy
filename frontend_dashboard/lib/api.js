import { config } from './config';

// Centralized API client
export class ApiClient {
  constructor() {
    this.baseUrl = config.apiUrl;
    this.defaultHeaders = config.apiDefaults.headers;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        ...config.apiDefaults,
        ...options,
        headers: {
          ...this.defaultHeaders,
          ...options.headers
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const text = await response.text();
        if (text.includes('ngrok')) {
          throw new Error('ngrok warning page detected - please visit the API URL directly first');
        }
        throw new Error(`Expected JSON but received: ${contentType}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API call failed for ${endpoint}:`, error);
      throw error;
    }
  }

  // Convenience methods
  async get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }

  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
}

// API service methods
export const api = new ApiClient();

export const apiService = {
  // Health check
  checkHealth: () => api.get(config.endpoints.health),
  
  // Meetings
  getMeetings: () => api.get(config.endpoints.meetings),
  getMeeting: (id) => api.get(`${config.endpoints.meetings}/${id}`),
  getMeetingDetail: (id) => api.get(`${config.endpoints.meetings}/${id}`),
  
  // Tasks
  getTasks: () => api.get(config.endpoints.tasks),
  getTasksByMeeting: (meetingId) => api.get(`${config.endpoints.tasks}?meeting_id=${meetingId}`),
  
  // Transcripts
  getTranscript: (meetingId) => api.get(`${config.endpoints.transcripts}/${meetingId}`),
  
  // Integrations
  getIntegrationStatus: () => api.get(config.endpoints.integrationStatus),
  getIntegrations: () => api.get(config.endpoints.integrations),
  
  // Projects
  getProjects: () => api.get(config.endpoints.projects)
};