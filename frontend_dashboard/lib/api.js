import { config } from './config';

// Centralized API client with caching
export class ApiClient {
  constructor() {
    this.baseUrl = config.apiUrl;
    this.defaultHeaders = config.apiDefaults.headers;
    this.cache = new Map();
    this.cacheTimeout = 30000; // 30 seconds
  }

  _getCacheKey(endpoint, options) {
    return `${endpoint}_${JSON.stringify(options || {})}`;
  }

  _isValidCache(cacheEntry) {
    return cacheEntry && (Date.now() - cacheEntry.timestamp) < this.cacheTimeout;
  }

  async request(endpoint, options = {}) {
    const cacheKey = this._getCacheKey(endpoint, options);
    const useCache = !options.skipCache && (options.method === 'GET' || !options.method);
    
    // Check cache for GET requests
    if (useCache) {
      const cached = this.cache.get(cacheKey);
      if (this._isValidCache(cached)) {
        return cached.data;
      }
    }

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

      const data = await response.json();
      
      // Cache GET requests
      if (useCache) {
        this.cache.set(cacheKey, {
          data,
          timestamp: Date.now()
        });
      }

      return data;
    } catch (error) {
      console.error(`API call failed for ${endpoint}:`, error);
      throw error;
    }
  }

  clearCache(pattern) {
    if (pattern) {
      for (const key of this.cache.keys()) {
        if (key.includes(pattern)) {
          this.cache.delete(key);
        }
      }
    } else {
      this.cache.clear();
    }
  }

  // Convenience methods
  async get(endpoint, options = {}) {
    return this.request(endpoint, { method: 'GET', ...options });
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
  getMeetings: (options = {}) => api.get(config.endpoints.meetings, options),
  getMeeting: (id, options = {}) => api.get(`${config.endpoints.meetings}/${id}`, options),
  getMeetingDetail: (id, options = {}) => api.get(`${config.endpoints.meetings}/${id}`, options),
  
  // Batch meeting data (optimized for detail page)
  getMeetingWithDetails: async (id, options = {}) => {
    try {
      // Get meeting detail and tasks separately since we don't have a combined endpoint
      const [meetingResponse, tasksResponse] = await Promise.all([
        api.get(`${config.endpoints.meetings}/${id}`, options),
        api.get(`${config.endpoints.tasks}?meeting_id=${id}`, options)
      ]);
      
      // Combine the responses
      return {
        status: 'success',
        data: {
          ...meetingResponse.data,
          tasks: tasksResponse.data || []
        }
      };
    } catch (error) {
      console.error('Failed to get meeting with details:', error);
      throw error;
    }
  },
  
  // Tasks
  getTasks: (meetingId) => {
    if (meetingId) {
      return api.get(`${config.endpoints.tasks}?meeting_id=${meetingId}`);
    }
    return api.get(config.endpoints.tasks);
  },
  getTasksByMeeting: (meetingId) => api.get(`${config.endpoints.tasks}?meeting_id=${meetingId}`),
  
  // Transcripts
  getTranscript: (meetingId) => api.get(`${config.endpoints.transcripts}/${meetingId}`),
  
  // Integrations
  getIntegrationStatus: () => api.get(config.endpoints.integrationStatus),
  getIntegrations: () => api.get(config.endpoints.integrations),
  
  // Projects
  getProjects: () => api.get(config.endpoints.projects),
  
  // Recording status
  getRecordingStatus: (meetingId) => {
    if (meetingId) {
      return api.get(`/recording-status?meeting_id=${meetingId}`);
    }
    return api.get('/recording-status');
  },
  
  // Chatbot integration
  chatWithBot: (message, sessionId = null, context = null) => {
    return fetch('http://127.0.0.1:8001/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId, context })
    }).then(res => res.json());
  },
  
  getChatbotHealth: () => {
    return fetch('http://127.0.0.1:8001/health').then(res => res.json());
  },
  
  searchKnowledge: (query, topK = 5) => {
    return fetch(`http://127.0.0.1:8001/knowledge/search?query=${encodeURIComponent(query)}&top_k=${topK}`)
      .then(res => res.json());
  }
};