// capture.js - Helper tab for multi-tab audio capture
console.log('🎬 ScrumBot Capture Helper loaded');

class CaptureHelper {
  constructor() {
    this.audioCapture = null;
    this.isCapturing = false;
    this.meetingTabId = null;
    
    this.initializeElements();
    this.setupEventListeners();
    this.parseURLParams();
  }

  initializeElements() {
    this.captureBtn = document.getElementById('captureBtn');
    this.statusDiv = document.getElementById('status');
  }

  setupEventListeners() {
    this.captureBtn.addEventListener('click', () => this.startCapture());
    
    // Listen for messages from meeting tab
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      this.handleMessage(message, sender, sendResponse);
    });
  }

  parseURLParams() {
    const urlParams = new URLSearchParams(window.location.search);
    this.meetingTabId = urlParams.get('meetingTabId');
    
    if (window.SCRUMBOT_CONFIG?.DEBUG) {
      console.log('[CaptureHelper] Meeting tab ID:', this.meetingTabId);
    }
  }

  async startCapture() {
    try {
      this.showStatus('Starting capture...', 'info');
      this.captureBtn.disabled = true;
      this.captureBtn.textContent = '⏳ Starting...';

      // Initialize audio capture if not already done
      if (!this.audioCapture) {
        this.audioCapture = new AudioCapture();
      }

      // Start the capture process
      const success = await this.audioCapture.startCapture();
      
      if (success) {
        this.handleCaptureSuccess();
      } else {
        this.handleCaptureFailure('Failed to start audio capture');
      }

    } catch (error) {
      console.error('[CaptureHelper] Capture error:', error);
      this.handleCaptureFailure(error.message);
    }
  }

  handleCaptureSuccess() {
    this.isCapturing = true;
    this.recordingStartTime = Date.now();
    this.showStatus('✅ Recording started! Audio is being captured.', 'success');
    this.captureBtn.textContent = '✅ Recording Active';
    
    // Send meeting start signal via WebSocket
    if (window.scrumBotWebSocket && window.scrumBotWebSocket.isConnected) {
      window.scrumBotWebSocket.sendMeetingEvent('started', {
        meetingUrl: window.location.href,
        participants: [{ id: 'user1', name: 'Meeting Participant' }]
      });
      console.log('[CaptureHelper] 🔄 Meeting start signal sent via WebSocket');
    }
    
    // Notify the meeting tab that capture started
    this.notifyMeetingTab('CAPTURE_STARTED', {
      success: true,
      helperTabId: chrome.runtime.id
    });

    // Set up audio stream forwarding
    this.setupAudioForwarding();

    // Keep tab open for user control
    this.showStatus('Recording active. Keep this tab open during recording.', 'info');
  }

  handleCaptureFailure(errorMessage) {
    this.showStatus(`❌ Capture failed: ${errorMessage}`, 'error');
    this.captureBtn.disabled = false;
    this.captureBtn.textContent = '📹 Try Again';
    
    // Notify the meeting tab about the failure
    this.notifyMeetingTab('CAPTURE_FAILED', {
      success: false,
      error: errorMessage
    });
  }

  setupAudioForwarding() {
    // Override the audio capture's sendAudioToBackend method
    // to also forward to the meeting tab
    const originalSendAudio = this.audioCapture.sendAudioToBackend.bind(this.audioCapture);
    
    this.audioCapture.sendAudioToBackend = (audioData) => {
      // Send to backend as usual
      originalSendAudio(audioData);
      
      // Also forward to meeting tab
      this.notifyMeetingTab('AUDIO_DATA', {
        audioData: audioData,
        timestamp: Date.now()
      });
    };
  }

  notifyMeetingTab(type, data) {
    chrome.runtime.sendMessage({
      type: 'HELPER_TO_MEETING',
      targetTabId: this.meetingTabId,
      messageType: type,
      data: data
    });
  }

  handleMessage(message, sender, sendResponse) {
    switch(message.type) {
      case 'MEETING_TO_HELPER':
        this.handleMeetingMessage(message.messageType, message.data);
        break;
        
      case 'STOP_CAPTURE':
        this.stopCapture();
        break;
    }
  }

  handleMeetingMessage(messageType, data) {
    switch(messageType) {
      case 'STOP_RECORDING':
        this.stopCapture();
        break;
        
      case 'GET_STATUS':
        this.notifyMeetingTab('STATUS_RESPONSE', {
          isCapturing: this.isCapturing,
          hasAudioStream: !!this.audioCapture?.audioStream
        });
        break;
    }
  }

  stopCapture() {
    if (this.audioCapture && this.isCapturing) {
      // Send meeting end signal via WebSocket
      if (window.scrumBotWebSocket && window.scrumBotWebSocket.isConnected) {
        window.scrumBotWebSocket.sendMeetingEvent('ended', {
          meetingUrl: window.location.href,
          participants: [{ id: 'user1', name: 'Meeting Participant' }],
          duration: Date.now() - (this.recordingStartTime || Date.now())
        });
        console.log('[CaptureHelper] 🔄 Meeting end signal sent via WebSocket');
      }
      
      this.audioCapture.stopCapture();
      this.isCapturing = false;
      
      this.showStatus('Recording stopped', 'info');
      this.captureBtn.textContent = '⏹️ Stopped';
      this.captureBtn.disabled = true;
      
      // Notify meeting tab
      this.notifyMeetingTab('CAPTURE_STOPPED', {
        success: true
      });
      
      // Keep tab open for user to manually close
      this.showStatus('Recording stopped. You can close this tab.', 'info');
    }
  }

  showStatus(message, type = 'info') {
    this.statusDiv.textContent = message;
    this.statusDiv.className = `status ${type}`;
    this.statusDiv.style.display = 'block';
    
    console.log(`[CaptureHelper] ${type.toUpperCase()}: ${message}`);
  }

  // Validate that the selected tab is actually a meeting
  validateMeetingTab(stream) {
    // This is called after successful capture
    // We can add validation logic here
    
    const audioTracks = stream.getAudioTracks();
    if (audioTracks.length === 0) {
      throw new Error('No audio tracks found in selected tab');
    }
    
    // Additional validation could include:
    // - Check if tab URL matches meeting platforms
    // - Verify audio content (not just silence)
    // - Detect meeting-specific audio patterns
    
    return true;
  }
}

// Initialize capture helper when page loads
document.addEventListener('DOMContentLoaded', () => {
  window.captureHelper = new CaptureHelper();
});

// Handle page unload
window.addEventListener('beforeunload', () => {
  if (window.captureHelper && window.captureHelper.isCapturing) {
    window.captureHelper.stopCapture();
  }
});