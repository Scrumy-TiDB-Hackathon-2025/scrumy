// audiocapture.js - Handles audio capture from browser tab
class AudioCapture {
    constructor() {
      this.mediaRecorder = null;
      this.audioStream = null;
      this.isRecording = false;
      this.audioChunks = [];
    }
  
    async startCapture() {
      try {
        console.log('[ScrumBot] Starting audio capture...');
        
        // Check if browser supports the required APIs
        if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) {
          throw new Error('getDisplayMedia not supported in this browser');
        }

        console.log('[ScrumBot] Requesting screen/audio sharing permissions...');
        
        // Request tab audio capture
        // Note: Chrome requires video to be requested even if we only want audio
        this.audioStream = await navigator.mediaDevices.getDisplayMedia({
          video: true, // Required by Chrome API
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            sampleRate: 16000
          }
        });

        // Check what tracks we got
        const videoTracks = this.audioStream.getVideoTracks();
        const audioTracks = this.audioStream.getAudioTracks();
        
        console.log(`[ScrumBot] Stream tracks: ${videoTracks.length} video, ${audioTracks.length} audio`);

        // Stop the video track since we only want audio
        videoTracks.forEach(track => {
          console.log('[ScrumBot] Stopping video track:', track.label);
          track.stop();
          this.audioStream.removeTrack(track);
        });

        // Verify we still have audio tracks
        if (audioTracks.length === 0) {
          throw new Error('No audio tracks available in the stream');
        }

        console.log('[ScrumBot] Video tracks removed, keeping only audio');
  
        // Create MediaRecorder
        this.mediaRecorder = new MediaRecorder(this.audioStream, {
          mimeType: 'audio/webm;codecs=opus'
        });
  
        this.setupRecorderEvents();
        
        // Use environment-specific chunk interval
        const chunkInterval = window.SCRUMBOT_CONFIG?.AUDIO_CHUNK_INTERVAL || 1000;
        this.mediaRecorder.start(chunkInterval);
        this.isRecording = true;
        
        if (window.SCRUMBOT_CONFIG?.DEBUG) {
          console.log(`[AudioCapture] Recording started with ${chunkInterval}ms chunks`);
        }
        
        console.log('[ScrumBot] Audio capture started');
        return true;
      } catch (error) {
        console.error('[ScrumBot] Audio capture failed:', error);
        
        // Provide specific error messages
        if (error.name === 'NotAllowedError') {
          console.error('[ScrumBot] User denied permission for screen/audio sharing');
          alert('Please allow screen sharing with audio to start recording');
        } else if (error.name === 'NotFoundError') {
          console.error('[ScrumBot] No audio source found');
        } else if (error.name === 'NotSupportedError') {
          console.error('[ScrumBot] Audio capture not supported');
        } else {
          console.error('[ScrumBot] Unknown audio capture error:', error.message);
        }
        
        return false;
      }
    }
  
    setupRecorderEvents() {
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
          this.processAudioChunk(event.data);
        }
      };
  
      this.mediaRecorder.onstop = () => {
        console.log('[ScrumBot] Recording stopped');
        this.isRecording = false;
      };
  
      // Set up audio track ended handler safely
      const audioTracks = this.audioStream.getAudioTracks();
      if (audioTracks.length > 0) {
        audioTracks[0].onended = () => {
          console.log('[ScrumBot] Audio stream ended');
          this.stopCapture();
        };
      } else {
        console.warn('[ScrumBot] No audio tracks found in stream');
      }
    }
  
    processAudioChunk(audioBlob) {
      // Convert blob to base64 for transmission
      const reader = new FileReader();
      reader.onload = () => {
        const base64Audio = reader.result.split(',')[1];
        console.log('[AudioCapture] Processing audio chunk:', base64Audio.length, 'bytes');
        this.sendAudioToBackend(base64Audio);
      };
      reader.readAsDataURL(audioBlob);
    }
  
    sendAudioToBackend(audioData) {
      console.log('[ScrumBot] Audio chunk ready:', audioData.length, 'bytes');
      
      // Get participant context from meeting detector
      const participants = window.meetingDetector?.getParticipants() || [];
      const participantCount = participants.length;
      
      // Send enhanced audio chunk with participant context
      chrome.runtime.sendMessage({
        type: 'AUDIO_CHUNK_ENHANCED',
        data: audioData,
        timestamp: Date.now(),
        platform: window.meetingDetector?.platform || 'unknown',
        meetingUrl: window.location.href,
        participants: participants,
        participant_count: participantCount,
        metadata: {
          chunk_size: audioData.length,
          sample_rate: 16000,
          channels: 1,
          format: 'webm'
        }
      });

      // Send via WebSocket if available
      this.sendViaWebSocket(audioData, participants, participantCount);
    }

    sendToRestAPI(audioData) {
      if (!window.SCRUMBOT_CONFIG) return;

      // In development mode, use mock transcription
      if (window.SCRUMBOT_CONFIG.MOCK_TRANSCRIPTION) {
        this.handleMockTranscription(audioData);
        return;
      }

      // Convert base64 to blob for REST API
      const binaryString = atob(audioData);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      const audioBlob = new Blob([bytes], { type: 'audio/webm' });

      const formData = new FormData();
      formData.append('audio', audioBlob, 'audio-chunk.webm');
      formData.append('timestamp', Date.now().toString());
      formData.append('platform', window.meetingDetector?.platform || 'unknown');

      fetch(`${window.SCRUMBOT_CONFIG.BACKEND_URL}${window.SCRUMBOT_CONFIG.ENDPOINTS.transcribe}`, {
        method: 'POST',
        headers: {
          'ngrok-skip-browser-warning': 'true'
        },
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        console.log('[ScrumBot] Transcription result:', data);
        if (data.text) {
          this.handleTranscriptionResult(data);
        }
      })
      .catch(error => {
        console.error('[ScrumBot] REST API transcription failed:', error);
      });
    }

    handleMockTranscription(audioData) {
      // Generate mock transcription for development
      const mockPhrases = [
        "Hello everyone, welcome to our team meeting.",
        "Let's start by reviewing the agenda for today.",
        "I think we should focus on the key deliverables.",
        "The project is progressing well according to schedule.",
        "Does anyone have questions about the requirements?",
        "We need to coordinate with the backend team.",
        "The testing phase should begin next week.",
        "Let's make sure we're all aligned on the timeline."
      ];
      
      const randomPhrase = mockPhrases[Math.floor(Math.random() * mockPhrases.length)];
      const mockData = {
        text: randomPhrase,
        confidence: 0.85 + Math.random() * 0.15, // 0.85-1.0
        timestamp: new Date().toISOString(),
        audioLength: audioData.length,
        mock: true
      };

      if (window.SCRUMBOT_CONFIG.DEBUG) {
        console.log('[AudioCapture] Mock transcription:', mockData);
      }

      // Simulate API delay
      setTimeout(() => {
        this.handleTranscriptionResult(mockData);
      }, 200 + Math.random() * 300); // 200-500ms delay
    }

    sendViaWebSocket(audioData, participants, participantCount) {
      if (!window.websocket || window.websocket.readyState !== WebSocket.OPEN) {
        console.log('[AudioCapture] WebSocket not available, initializing...');
        this.initializeWebSocket();
        return;
      }
      
      const message = {
        type: 'AUDIO_CHUNK_ENHANCED',
        data: audioData,
        timestamp: Date.now(),
        platform: window.meetingDetector?.platform || 'unknown',
        meetingUrl: window.location.href,
        participants: participants,
        participant_count: participantCount,
        metadata: {
          chunk_size: audioData.length,
          sample_rate: 16000,
          channels: 1,
          format: 'webm'
        }
      };
      
      window.websocket.send(JSON.stringify(message));
      console.log('[AudioCapture] Audio chunk sent via WebSocket');
    }
    
    initializeWebSocket() {
      if (window.websocket && window.websocket.readyState === WebSocket.OPEN) {
        return;
      }
      
      const wsUrl = window.SCRUMBOT_CONFIG?.WEBSOCKET_URL;
      if (!wsUrl) {
        console.error('[AudioCapture] No WebSocket URL configured');
        return;
      }
      
      console.log('[AudioCapture] Connecting to WebSocket:', wsUrl);
      
      window.websocket = new WebSocket(wsUrl);
      
      window.websocket.onopen = () => {
        console.log('[AudioCapture] WebSocket connected');
      };
      
      window.websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'transcription_result') {
            this.handleTranscriptionResult(data.data);
          }
        } catch (error) {
          console.error('[AudioCapture] WebSocket message parse error:', error);
        }
      };
      
      window.websocket.onerror = (error) => {
        console.error('[AudioCapture] WebSocket error:', error);
      };
      
      window.websocket.onclose = () => {
        console.log('[AudioCapture] WebSocket disconnected');
        setTimeout(() => this.initializeWebSocket(), 5000);
      };
    }

    handleTranscriptionResult(data) {
      console.log('[AudioCapture] Transcription result:', data);
      // Dispatch event for UI updates
      window.dispatchEvent(new CustomEvent('scrumbot-transcription', {
        detail: data
      }));
    }
  
    stopCapture() {
      if (this.mediaRecorder && this.isRecording) {
        this.mediaRecorder.stop();
      }
      
      if (this.audioStream) {
        this.audioStream.getTracks().forEach(track => track.stop());
        this.audioStream = null;
      }
      
      this.audioChunks = [];
      this.isRecording = false;
      console.log('[ScrumBot] Audio capture stopped');
    }
  }
  
  // Make available globally
  window.scrumBotAudioCapture = new AudioCapture();
  