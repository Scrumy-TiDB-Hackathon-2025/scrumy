// Environment configuration
const getApiUrl = () => {
  if (process.env.NEXT_PUBLIC_ENV === 'production') {
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
  }
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
};

const getWebSocketUrl = () => {
  if (process.env.NEXT_PUBLIC_ENV === 'production') {
    return process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8080';
  }
  return process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8080';
};

export const config = {
  apiUrl: getApiUrl(),
  websocketUrl: getWebSocketUrl(),
  environment: process.env.NEXT_PUBLIC_ENV || 'development',
  
  // API endpoints
  endpoints: {
    health: process.env.NEXT_PUBLIC_HEALTH_ENDPOINT || '/health',
    meetings: process.env.NEXT_PUBLIC_MEETINGS_ENDPOINT || '/api/meetings',
    tasks: process.env.NEXT_PUBLIC_TASKS_ENDPOINT || '/api/tasks',
    transcripts: process.env.NEXT_PUBLIC_TRANSCRIPTS_ENDPOINT || '/api/transcripts',
    integrationStatus: process.env.NEXT_PUBLIC_INTEGRATION_STATUS_ENDPOINT || '/api/integration-status',
    integrations: process.env.NEXT_PUBLIC_INTEGRATIONS_ENDPOINT || '/api/integrations',
    projects: process.env.NEXT_PUBLIC_PROJECTS_ENDPOINT || '/api/projects'
  },
  
  // Development settings
  isDevelopment: process.env.NEXT_PUBLIC_ENV === 'development',
  isProduction: process.env.NEXT_PUBLIC_ENV === 'production',
  
  // API call configuration
  apiDefaults: {
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'ngrok-skip-browser-warning': 'true'
    },
    mode: 'cors',
    credentials: 'omit'
  }
};