// Environment Configuration Module
// Provides type-safe access to environment variables and configuration

export type Environment = 'dev' | 'staging' | 'prod';

export interface EnvironmentConfig {
  // Environment Info
  ENVIRONMENT: Environment;
  VERSION: string;

  // API URLs
  BACKEND_URL: string;
  WEBSOCKET_URL: string;
  FRONTEND_URL: string;

  // API Endpoints
  ENDPOINTS: {
    health: string;
    saveTranscript: string;
    getMeetings: string;
    getModelConfig: string;
    processTranscript: string;
    transcribe: string;
    identifySpeakers: string;
    generateSummary: string;
    extractTasks: string;
    processTranscriptWithTools: string;
    getAvailableTools: string;
  };

  // Settings
  DEBUG: boolean;
  MOCK_DATA: boolean;
  LOG_LEVEL: 'debug' | 'info' | 'warn' | 'error';

  // Feature Flags
  FEATURE_FLAGS: {
    enableWebSocket: boolean;
    enableRealTimeUpdates: boolean;
    enableMockTranscription: boolean;
  };

  // Performance Settings
  PERFORMANCE: {
    refreshInterval: number;
    timeout: number;
  };
}

// Helper function to get environment variable with fallback
function getEnvVar(key: string, fallback: string = ''): string {
  if (typeof window !== 'undefined') {
    return (window as any).__ENV__?.[key] || process.env[key] || fallback;
  }
  return process.env[key] || fallback;
}

// Helper function to get boolean environment variable
function getBooleanEnvVar(key: string, fallback: boolean = false): boolean {
  const value = getEnvVar(key).toLowerCase();
  return value === 'true' || value === '1';
}

// Helper function to get number environment variable
function getNumberEnvVar(key: string, fallback: number): number {
  const value = getEnvVar(key);
  const parsed = parseInt(value, 10);
  return isNaN(parsed) ? fallback : parsed;
}

// Create configuration based on environment variables
function createConfig(): EnvironmentConfig {
  const environment = (getEnvVar('NEXT_PUBLIC_ENVIRONMENT', 'dev') as Environment);

  return {
    ENVIRONMENT: environment,
    VERSION: getEnvVar('NEXT_PUBLIC_VERSION', '1.0.0'),

    // API URLs
    BACKEND_URL: getEnvVar('NEXT_PUBLIC_BACKEND_URL', 'http://localhost:8000'),
    WEBSOCKET_URL: getEnvVar('NEXT_PUBLIC_WEBSOCKET_URL', 'ws://localhost:8000/ws/audio'),
    FRONTEND_URL: getEnvVar('NEXT_PUBLIC_FRONTEND_URL', 'http://localhost:3000'),

    // API Endpoints
    ENDPOINTS: {
      health: getEnvVar('NEXT_PUBLIC_API_HEALTH', '/health'),
      saveTranscript: getEnvVar('NEXT_PUBLIC_API_SAVE_TRANSCRIPT', '/save-transcript'),
      getMeetings: getEnvVar('NEXT_PUBLIC_API_GET_MEETINGS', '/get-meetings'),
      getModelConfig: getEnvVar('NEXT_PUBLIC_API_GET_MODEL_CONFIG', '/get-model-config'),
      processTranscript: getEnvVar('NEXT_PUBLIC_API_PROCESS_TRANSCRIPT', '/process-transcript'),
      transcribe: getEnvVar('NEXT_PUBLIC_API_TRANSCRIBE', '/transcribe'),
      identifySpeakers: getEnvVar('NEXT_PUBLIC_API_IDENTIFY_SPEAKERS', '/identify-speakers'),
      generateSummary: getEnvVar('NEXT_PUBLIC_API_GENERATE_SUMMARY', '/generate-summary'),
      extractTasks: getEnvVar('NEXT_PUBLIC_API_EXTRACT_TASKS', '/extract-tasks'),
      processTranscriptWithTools: getEnvVar('NEXT_PUBLIC_API_PROCESS_TRANSCRIPT_WITH_TOOLS', '/process-transcript-with-tools'),
      getAvailableTools: getEnvVar('NEXT_PUBLIC_API_AVAILABLE_TOOLS', '/available-tools'),
    },

    // Settings
    DEBUG: getBooleanEnvVar('NEXT_PUBLIC_DEBUG', false),
    MOCK_DATA: getBooleanEnvVar('NEXT_PUBLIC_MOCK_DATA', false),
    LOG_LEVEL: (getEnvVar('NEXT_PUBLIC_LOG_LEVEL', 'info') as 'debug' | 'info' | 'warn' | 'error'),

    // Feature Flags
    FEATURE_FLAGS: {
      enableWebSocket: getBooleanEnvVar('NEXT_PUBLIC_ENABLE_WEBSOCKET', true),
      enableRealTimeUpdates: getBooleanEnvVar('NEXT_PUBLIC_ENABLE_REAL_TIME_UPDATES', true),
      enableMockTranscription: getBooleanEnvVar('NEXT_PUBLIC_ENABLE_MOCK_TRANSCRIPTION', false),
    },

    // Performance Settings
    PERFORMANCE: {
      refreshInterval: getNumberEnvVar('NEXT_PUBLIC_REFRESH_INTERVAL', 1000),
      timeout: getNumberEnvVar('NEXT_PUBLIC_TIMEOUT', 30000),
    },
  };
}

// Export the configuration
export const config: EnvironmentConfig = createConfig();

// Utility functions
export const isProduction = (): boolean => config.ENVIRONMENT === 'prod';
export const isStaging = (): boolean => config.ENVIRONMENT === 'staging';
export const isDevelopment = (): boolean => config.ENVIRONMENT === 'dev';

// API URL builders
export const buildApiUrl = (endpoint: keyof EnvironmentConfig['ENDPOINTS']): string => {
  return `${config.BACKEND_URL}${config.ENDPOINTS[endpoint]}`;
};

export const buildWebSocketUrl = (): string => {
  return config.WEBSOCKET_URL;
};

// Logging utility
export const log = {
  debug: (...args: any[]) => {
    if (config.DEBUG && ['debug'].includes(config.LOG_LEVEL)) {
      console.log(`[${config.ENVIRONMENT.toUpperCase()}] DEBUG:`, ...args);
    }
  },
  info: (...args: any[]) => {
    if (config.DEBUG && ['debug', 'info'].includes(config.LOG_LEVEL)) {
      console.info(`[${config.ENVIRONMENT.toUpperCase()}] INFO:`, ...args);
    }
  },
  warn: (...args: any[]) => {
    if (config.DEBUG && ['debug', 'info', 'warn'].includes(config.LOG_LEVEL)) {
      console.warn(`[${config.ENVIRONMENT.toUpperCase()}] WARN:`, ...args);
    }
  },
  error: (...args: any[]) => {
    console.error(`[${config.ENVIRONMENT.toUpperCase()}] ERROR:`, ...args);
  },
};

// Environment validation
export const validateConfig = (): void => {
  const requiredFields = [
    'BACKEND_URL',
    'WEBSOCKET_URL',
    'FRONTEND_URL',
  ];

  const missingFields = requiredFields.filter(field => !config[field as keyof EnvironmentConfig]);

  if (missingFields.length > 0) {
    log.error('Missing required configuration fields:', missingFields);
    throw new Error(`Missing required environment configuration: ${missingFields.join(', ')}`);
  }

  log.info('Environment configuration loaded:', {
    environment: config.ENVIRONMENT,
    backend: config.BACKEND_URL,
    websocket: config.WEBSOCKET_URL,
    debug: config.DEBUG,
    mockData: config.MOCK_DATA,
  });
};

// Initialize configuration validation
if (typeof window !== 'undefined') {
  validateConfig();
}

// Default export
export default config;
