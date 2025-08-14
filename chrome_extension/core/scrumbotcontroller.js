// Add to content.js after MeetingDetector class
class ScrumBotController {
  constructor() {
    // Use existing global instances instead of creating new ones
    this.detector = window.meetingDetector;
    this.audioCapture = window.scrumBotAudioCapture;
    this.isRecording = false;
    this.currentMeetingId = null;
    this.enhancedFeatures = {
      participantDetection: true,
      speakerAttribution: true,
      taskExtraction: true
    };

    if (!this.detector || !this.audioCapture) {
      console.error('[ScrumBotController] Missing dependencies:', {
        detector: !!this.detector,
        audioCapture: !!this.audioCapture
      });
    } else {
      console.log('[ScrumBotController] Initialized with enhanced features');
    }

    this.setupMessageListener();
    this.setupEnhancedEventListeners();
  }

  setupMessageListener() {
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      switch (message.type) {
        case 'START_RECORDING':
          this.startRecording();
          break;
        case 'STOP_RECORDING':
          this.stopRecording();
          break;
        case 'GET_STATUS':
          sendResponse({
            isInMeeting: this.detector.isInMeeting,
            isRecording: this.isRecording,
            platform: this.detector.platform,
            participants: this.detector.getParticipants(),
            participantCount: this.detector.getParticipantCount(),
            meetingId: this.currentMeetingId,
            enhancedFeatures: this.enhancedFeatures
          });
          break;
        case 'GET_PARTICIPANTS':
          sendResponse({
            participants: this.detector.getParticipants(),
            count: this.detector.getParticipantCount()
          });
          break;
      }
    });
  }

  setupEnhancedEventListeners() {
    // Listen for participant changes
    window.addEventListener('scrumbot-participant-change', (event) => {
      this.handleParticipantChange(event.detail);
    });
    
    // Listen for transcription updates
    window.addEventListener('scrumbot-transcription', (event) => {
      this.handleTranscriptionUpdate(event.detail);
    });
    
    // Listen for speaker attribution
    window.addEventListener('scrumbot-speaker-attribution', (event) => {
      this.handleSpeakerAttribution(event.detail);
    });
    
    // Listen for meeting analysis
    window.addEventListener('scrumbot-meeting-analysis', (event) => {
      this.handleMeetingAnalysis(event.detail);
    });
  }

  async startRecording() {
    // Generate unique meeting ID
    this.currentMeetingId = 'meeting-' + Date.now() + '-' + Math.random().toString(36).substring(2, 11);
    
    console.log('[ScrumBotController] Starting enhanced recording...', {
      meetingId: this.currentMeetingId,
      detectorAvailable: !!this.detector,
      audioCaptureAvailable: !!this.audioCapture,
      isInMeeting: this.detector?.isInMeeting,
      platform: this.detector?.platform,
      participantCount: this.detector?.getParticipantCount() || 0
    });

    // In development mode, allow recording even if not detected as "in meeting"
    if (!this.detector?.isInMeeting && window.SCRUMBOT_CONFIG?.ENVIRONMENT === 'prod') {
      console.log('[ScrumBot] Not in a meeting, cannot start recording');
      return false;
    }

    if (window.SCRUMBOT_CONFIG?.ENVIRONMENT === 'dev') {
      console.log('[ScrumBot] Development mode: allowing recording regardless of meeting status');
    }

    if (!this.audioCapture) {
      console.error('[ScrumBot] Audio capture not available');
      return false;
    }

    try {
      // Start participant monitoring if not already started
      if (this.detector && !this.detector.isMonitoringParticipants) {
        await this.detector.startParticipantMonitoring();
      }
      
      // Send meeting setup to backend
      this.sendMeetingSetup();
      
      const success = await this.audioCapture.startCapture();
      if (success) {
        this.isRecording = true;
        this.notifyRecordingStateChange();
        console.log('[ScrumBotController] Enhanced recording started successfully');
        
        // Create meeting record
        this.createMeetingRecord();
      } else {
        console.error('[ScrumBotController] Audio capture failed to start');
      }
      return success;
    } catch (error) {
      console.error('[ScrumBotController] Error starting enhanced recording:', error);
      return false;
    }
  }

  stopRecording() {
    this.audioCapture.stopCapture();
    this.isRecording = false;
    this.currentMeetingId = null;
    
    // Stop participant monitoring
    if (this.detector && this.detector.isMonitoringParticipants) {
      this.detector.stopParticipantMonitoring();
    }
    
    this.notifyRecordingStateChange();
  }

  notifyRecordingStateChange() {
    chrome.runtime.sendMessage({
      type: 'RECORDING_STATE_CHANGE',
      isRecording: this.isRecording,
      meetingId: this.currentMeetingId,
      participants: this.detector?.getParticipants() || [],
      participantCount: this.detector?.getParticipantCount() || 0
    });
  }

  sendMeetingSetup() {
    const participants = this.detector?.getParticipants() || [];
    
    chrome.runtime.sendMessage({
      type: 'MEETING_SETUP',
      meeting_id: this.currentMeetingId,
      platform: this.detector?.platform || 'unknown',
      timestamp: new Date().toISOString(),
      participants: participants,
      participant_count: participants.length,
      metadata: {
        url: window.location.href,
        user_agent: navigator.userAgent,
        setup_time: new Date().toISOString()
      }
    });
  }

  createMeetingRecord() {
    const participants = this.detector?.getParticipants() || [];
    const meetingData = {
      meeting_title: `${this.detector?.platform || 'Unknown'} Meeting - ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}`,
      meeting_id: this.currentMeetingId,
      platform: this.detector?.platform || 'unknown',
      participants: participants,
      transcripts: [{
        id: this.currentMeetingId,
        text: `Meeting started on ${this.detector?.platform || 'unknown'} at ${new Date().toISOString()}`,
        timestamp: new Date().toISOString()
      }]
    };

    // Send to backend
    if (window.SCRUMBOT_CONFIG) {
      fetch(`${window.SCRUMBOT_CONFIG.BACKEND_URL}${window.SCRUMBOT_CONFIG.ENDPOINTS.saveTranscript}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true'
        },
        body: JSON.stringify(meetingData)
      })
      .then(response => response.json())
      .then(data => {
        console.log('✅ Enhanced meeting record created:', data);
      })
      .catch(error => {
        console.error('❌ Failed to create meeting record:', error);
      });
    }
  }

  // Enhanced event handlers
  handleParticipantChange(event) {
    console.log('👥 Participant change in controller:', event);
    
    // Update UI if available
    if (window.scrumBotUI) {
      window.scrumBotUI.updateParticipants(event.participants);
    }
    
    // Send participant update to backend
    chrome.runtime.sendMessage({
      type: 'PARTICIPANT_UPDATE',
      meeting_id: this.currentMeetingId,
      timestamp: new Date().toISOString(),
      participants: event.participants,
      participant_count: event.current_count,
      platform: this.detector?.platform || 'unknown'
    });
  }

  handleTranscriptionUpdate(data) {
    console.log('📝 Transcription update:', data);
    
    // Update UI if available
    if (window.scrumBotUI) {
      window.scrumBotUI.addTranscript(data);
    }
  }

  handleSpeakerAttribution(data) {
    console.log('🗣️ Speaker attribution:', data);
    
    // Update UI if available
    if (window.scrumBotUI) {
      window.scrumBotUI.updateSpeakerAttribution(data);
    }
  }

  handleMeetingAnalysis(data) {
    console.log('📊 Meeting analysis:', data);
    
    // Update UI if available
    if (window.scrumBotUI) {
      window.scrumBotUI.updateMeetingAnalysis(data);
    }
  }
}

// Initialize controller after dependencies are available
function initializeController() {
  if (window.meetingDetector && window.scrumBotAudioCapture) {
    window.scrumBotController = new ScrumBotController();
    console.log('[ScrumBot] Controller initialized successfully');
  } else {
    console.log('[ScrumBot] Waiting for dependencies...');
    setTimeout(initializeController, 100);
  }
}

// Start initialization
initializeController();