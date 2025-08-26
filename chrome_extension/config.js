// ScrumBot Extension Configuration
// Environment-based configuration for dev/prod

const ENVIRONMENT = "dev"; // Change to 'prod' when backend is ready

const CONFIGS = {
  dev: {
    // Development - Mock servers for testing
    BACKEND_URL: "http://localhost:8000", // AI Processing server
    WEBSOCKET_URL: "ws://localhost:8000/ws/audio", // WebSocket server matching shared contract
    FRONTEND_URL: "http://localhost:3000", // Local frontend or use prod

    // Mock API Endpoints
    ENDPOINTS: {
      health: "/health",
      saveTranscript: "/save-transcript",
      getMeetings: "/get-meetings",
      getModelConfig: "/get-model-config",
      processTranscript: "/process-transcript",
      transcribe: "/transcribe",
      // New Epic B endpoints
      identifySpeakers: "/identify-speakers",
      generateSummary: "/generate-summary",
      extractTasks: "/extract-tasks",
      processTranscriptWithTools: "/process-transcript-with-tools",
      getAvailableTools: "/available-tools",
    },

    // Development settings
    DEBUG: true,
    MOCK_TRANSCRIPTION: true,
    AUDIO_CHUNK_INTERVAL: 2000, // 2 seconds for testing
  },

  prod: {
    // Production - Real backend services
    BACKEND_URL: "https://b5462b7bbb65.ngrok-free.app",
    WEBSOCKET_URL: "wss://b5462b7bbb65.ngrok-free.app/ws/audio-stream",
    FRONTEND_URL: "https://scrumy.vercel.app",

    // Production API Endpoints
    ENDPOINTS: {
      health: "/health",
      saveTranscript: "/save-transcript",
      getMeetings: "/get-meetings",
      getModelConfig: "/get-model-config",
      processTranscript: "/process-transcript",
      transcribe: "/transcribe",
      // Epic B endpoints
      identifySpeakers: "/identify-speakers",
      generateSummary: "/generate-summary",
      extractTasks: "/extract-tasks",
      processTranscriptWithTools: "/process-transcript-with-tools",
      getAvailableTools: "/available-tools",
    },

    // Production settings
    DEBUG: false,
    MOCK_TRANSCRIPTION: false,
    AUDIO_CHUNK_INTERVAL: 1000, // 1 second for production
  },
};

// Select configuration based on environment
const SCRUMBOT_CONFIG = {
  ...CONFIGS[ENVIRONMENT],

  // Common settings for both environments
  SUPPORTED_PLATFORMS: ["meet.google.com", "zoom.us", "teams.microsoft.com"],

  // Current environment info
  ENVIRONMENT: ENVIRONMENT,
  VERSION: "1.0.0",
};

// Debug logging
if (SCRUMBOT_CONFIG.DEBUG) {
  console.log("🔧 ScrumBot Config Loaded:", {
    environment: SCRUMBOT_CONFIG.ENVIRONMENT,
    backend: SCRUMBOT_CONFIG.BACKEND_URL,
    websocket: SCRUMBOT_CONFIG.WEBSOCKET_URL,
    mockMode: SCRUMBOT_CONFIG.MOCK_TRANSCRIPTION,
  });
}

// Make config globally available
window.SCRUMBOT_CONFIG = SCRUMBOT_CONFIG;
