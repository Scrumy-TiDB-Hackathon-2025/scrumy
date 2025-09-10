// Environment configuration
export const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080',
  websocketUrl: process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8080',
  environment: process.env.NEXT_PUBLIC_ENV || 'development',
  
  // API endpoints
  endpoints: {
    health: process.env.NEXT_PUBLIC_HEALTH_ENDPOINT || '/health',
    meetings: process.env.NEXT_PUBLIC_MEETINGS_ENDPOINT || '/get-meetings',
    tasks: process.env.NEXT_PUBLIC_TASKS_ENDPOINT || '/api/tasks',
    transcripts: process.env.NEXT_PUBLIC_TRANSCRIPTS_ENDPOINT || '/api/transcripts',
    integrations: process.env.NEXT_PUBLIC_INTEGRATIONS_ENDPOINT || '/api/integration-status'
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