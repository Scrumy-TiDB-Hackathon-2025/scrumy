/**
 * WebSocket Events Constants
 * Centralized event type definitions for consistent communication across the ScrumBot Chrome extension.
 * This file mirrors the Python constants in shared/websocket_events.py
 */

export const WebSocketEventTypes = {
  // Connection Events
  HANDSHAKE: "HANDSHAKE",
  HANDSHAKE_ACK: "HANDSHAKE_ACK",
  CONNECTION_ERROR: "CONNECTION_ERROR",

  // Audio Processing Events
  AUDIO_CHUNK: "AUDIO_CHUNK",
  AUDIO_BUFFER_FULL: "AUDIO_BUFFER_FULL",
  AUDIO_PROCESSING_START: "AUDIO_PROCESSING_START",
  AUDIO_PROCESSING_COMPLETE: "AUDIO_PROCESSING_COMPLETE",

  // Transcription Events (STANDARDIZED - uppercase only)
  TRANSCRIPTION_RESULT: "TRANSCRIPTION_RESULT",
  TRANSCRIPTION_ERROR: "TRANSCRIPTION_ERROR",
  TRANSCRIPTION_TIMEOUT: "TRANSCRIPTION_TIMEOUT",

  // Meeting Events
  MEETING_EVENT: "MEETING_EVENT",
  MEETING_STARTED: "MEETING_STARTED",
  MEETING_ENDED: "MEETING_ENDED",
  MEETING_UPDATE: "MEETING_UPDATE",
  MEETING_PROCESSED: "MEETING_PROCESSED",

  // Participant Events
  PARTICIPANT_JOINED: "PARTICIPANT_JOINED",
  PARTICIPANT_LEFT: "PARTICIPANT_LEFT",
  PARTICIPANT_UPDATED: "PARTICIPANT_UPDATED",

  // Processing Status Events
  PROCESSING_STATUS: "PROCESSING_STATUS",
  PROCESSING_START: "PROCESSING_START",
  PROCESSING_COMPLETE: "PROCESSING_COMPLETE",
  PROCESSING_ERROR: "PROCESSING_ERROR",

  // System Events
  ERROR: "ERROR",
  WARNING: "WARNING",
  SYSTEM_STATUS: "SYSTEM_STATUS",

  // Authentication Events
  AUTH_REQUIRED: "AUTH_REQUIRED",
  AUTH_SUCCESS: "AUTH_SUCCESS",
  AUTH_FAILURE: "AUTH_FAILURE"
};

export const WebSocketEventData = {
  /**
   * Standard transcription result event data structure
   */
  transcriptionResult: (text, confidence, timestamp, speaker = "Unknown", chunkId = null, isFinal = false, extraData = {}) => ({
    text,
    confidence,
    timestamp,
    speaker,
    chunkId,
    is_final: isFinal,
    ...extraData
  }),

  /**
   * Standard meeting event data structure
   */
  meetingEvent: (meetingId, eventType, timestamp, data = {}) => ({
    meetingId,
    eventType,
    timestamp,
    data
  }),

  /**
   * Standard processing status event data structure
   */
  processingStatus: (meetingId, status, progress = null, message = null, extraData = {}) => ({
    meetingId,
    status,
    progress,
    message,
    ...extraData
  }),

  /**
   * Standard error event data structure
   */
  errorEvent: (errorType, message, details = {}) => ({
    errorType,
    message,
    details,
    timestamp: new Date().toISOString()
  })
};

export const WebSocketMessageTypes = {
  CHROME_EXTENSION: "chrome_extension",
  FRONTEND_DASHBOARD: "frontend_dashboard",
  INTEGRATION_SERVICE: "integration_service",
  AI_PROCESSOR: "ai_processor"
};

export const WebSocketEventValidator = {
  REQUIRED_FIELDS: {
    [WebSocketEventTypes.TRANSCRIPTION_RESULT]: ["text", "confidence", "timestamp"],
    [WebSocketEventTypes.MEETING_EVENT]: ["meetingId", "eventType", "timestamp"],
    [WebSocketEventTypes.PROCESSING_STATUS]: ["meetingId", "status"],
    [WebSocketEventTypes.ERROR]: ["errorType", "message"],
    [WebSocketEventTypes.HANDSHAKE]: ["clientType"]
  },

  /**
   * Validate event data structure
   * @param {string} eventType - The event type to validate
   * @param {Object} data - The event data dictionary
   * @returns {Object} {isValid: boolean, errorMessage: string}
   */
  validateEvent: (eventType, data) => {
    if (!WebSocketEventValidator.REQUIRED_FIELDS[eventType]) {
      return { isValid: true, errorMessage: "" }; // No validation rules defined
    }

    const requiredFields = WebSocketEventValidator.REQUIRED_FIELDS[eventType];
    const missingFields = requiredFields.filter(field => !(field in data));

    if (missingFields.length > 0) {
      return {
        isValid: false,
        errorMessage: `Missing required fields: ${missingFields.join(', ')}`
      };
    }

    return { isValid: true, errorMessage: "" };
  }
};

// Deprecated event names (for migration reference)
export const DEPRECATED_EVENT_NAMES = {
  "transcription_result": WebSocketEventTypes.TRANSCRIPTION_RESULT,  // Use uppercase
  "meeting_update": WebSocketEventTypes.MEETING_UPDATE,
  "processing_complete": WebSocketEventTypes.PROCESSING_COMPLETE
};

// Event detection helper
export const isDeprecatedEvent = (eventType) => {
  return Object.keys(DEPRECATED_EVENT_NAMES).includes(eventType);
};

export const getStandardEventType = (eventType) => {
  return DEPRECATED_EVENT_NAMES[eventType] || eventType;
};

// Logging utility for event debugging
export const logEventProcessing = (eventType, data, source = 'unknown') => {
  if (window.SCRUMBOT_CONFIG?.DEBUG) {
    const isDeprecated = isDeprecatedEvent(eventType);
    const standardType = getStandardEventType(eventType);

    console.log(`[WebSocket Event] ${source}:`, {
      eventType,
      standardType: isDeprecated ? standardType : 'N/A',
      isDeprecated,
      dataKeys: Object.keys(data || {}),
      timestamp: new Date().toISOString()
    });

    if (isDeprecated) {
      console.warn(`[WebSocket Event] DEPRECATED event type "${eventType}" used. Use "${standardType}" instead.`);
    }
  }
};

// Export default for backwards compatibility
export default {
  WebSocketEventTypes,
  WebSocketEventData,
  WebSocketMessageTypes,
  WebSocketEventValidator,
  DEPRECATED_EVENT_NAMES,
  isDeprecatedEvent,
  getStandardEventType,
  logEventProcessing
};
