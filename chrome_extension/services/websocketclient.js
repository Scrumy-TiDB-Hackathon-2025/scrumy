// websocket-client.js - WebSocket client for real-time audio streaming
class WebSocketClient {
    constructor() {
      this.ws = null;
      this.isConnected = false;
      this.reconnectAttempts = 0;
      this.maxReconnectAttempts = 5;
      this.reconnectDelay = 1000;
      
      // Use environment-specific WebSocket URL
      this.serverUrl = window.SCRUMBOT_CONFIG?.WEBSOCKET_URL || 'ws://localhost:8080/ws';
      
      if (window.SCRUMBOT_CONFIG?.DEBUG) {
        console.log('[WebSocket] Using server URL:', this.serverUrl);
      }
    }
  
    connect() {
      try {
        if (window.SCRUMBOT_CONFIG?.DEBUG) {
          console.log('[ScrumBot] Connecting to WebSocket server...');
        }
        this.ws = new WebSocket(this.serverUrl);
        
        this.ws.onopen = () => {
          if (window.SCRUMBOT_CONFIG?.DEBUG) {
            console.log('[ScrumBot] WebSocket connected');
          }
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.sendHandshake();
        };
  
        this.ws.onmessage = (event) => {
          this.handleMessage(JSON.parse(event.data));
        };
  
        this.ws.onclose = () => {
          if (window.SCRUMBOT_CONFIG?.DEBUG) {
            console.log('[ScrumBot] WebSocket disconnected');
          }
          this.isConnected = false;
          this.attemptReconnect();
        };
  
        this.ws.onerror = (error) => {
          console.error('[ScrumBot] WebSocket error:', error);
        };
  
      } catch (error) {
        console.error('[ScrumBot] WebSocket connection failed:', error);
      }
    }
  
    sendHandshake() {
      this.send({
        type: 'HANDSHAKE',
        clientType: 'chrome-extension',
        version: '1.0',
        capabilities: ['audio-capture', 'meeting-detection']
      });
    }
  
    send(data) {
      if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify(data));
        return true;
      } else {
        console.warn('[ScrumBot] WebSocket not connected, message queued');
        return false;
      }
    }
  
    sendAudioChunk(audioData, metadata = {}) {
      return this.send({
        type: 'AUDIO_CHUNK',
        data: audioData,
        timestamp: Date.now(),
        metadata: {
          platform: metadata.platform || 'unknown',
          meetingUrl: metadata.meetingUrl || window.location.href,
          chunkSize: audioData.length,
          ...metadata
        }
      });
    }
  
    sendMeetingEvent(eventType, data = {}) {
      return this.send({
        type: 'MEETING_EVENT',
        eventType: eventType, // 'started', 'ended', 'participant_joined', etc.
        timestamp: Date.now(),
        data: data
      });
    }
  
    handleMessage(message) {
      if (window.SCRUMBOT_CONFIG?.DEBUG) {
        console.log('[ScrumBot] Received message:', message.type);
      }
      
      switch(message.type) {
        case 'HANDSHAKE_ACK':
          if (window.SCRUMBOT_CONFIG?.DEBUG) {
            console.log('[ScrumBot] Handshake acknowledged');
          }
          break;
        case 'TRANSCRIPTION_RESULT':
          this.handleTranscriptionResult(message.data);
          break;
        case 'ERROR':
          console.error('[ScrumBot] Server error:', message.error);
          break;
      }
    }
  
    handleTranscriptionResult(data) {
      // Forward to content script for display
      chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
        chrome.tabs.sendMessage(tabs[0].id, {
          type: 'TRANSCRIPTION_UPDATE',
          data: data
        });
      });
    }
  
    attemptReconnect() {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        console.log(`[ScrumBot] Reconnecting... Attempt ${this.reconnectAttempts}`);
        
        setTimeout(() => {
          this.connect();
        }, this.reconnectDelay * this.reconnectAttempts);
      } else {
        console.error('[ScrumBot] Max reconnection attempts reached');
      }
    }
  
    disconnect() {
      if (this.ws) {
        this.ws.close();
        this.ws = null;
      }
      this.isConnected = false;
    }
  }
  
  // Make available globally
  window.scrumBotWebSocket = new WebSocketClient();