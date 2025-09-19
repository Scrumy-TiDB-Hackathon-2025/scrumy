// audiocapture.js - Handles audio capture from browser tab
class AudioCapture {
    constructor() {
      this.mediaRecorder = null;
      this.audioStream = null;
      this.isRecording = false;
      this.audioChunks = [];
      this.audioContext = null;
      this.processor = null;
      this.recordedPCMData = [];
      this.sampleRate = 16000;
      this.silenceThreshold = 0.01;
      this.minAudioLevel = 0.001;
    }
  
    async startCapture() {
      try {
        console.log('[ScrumBot] Starting enhanced audio capture...');
        
        // Check if browser supports the required APIs
        if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) {
          throw new Error('getDisplayMedia not supported in this browser');
        }

        console.log('[ScrumBot] Requesting screen/audio sharing permissions...');
        
        // Request tab audio capture with enhanced settings
        this.audioStream = await navigator.mediaDevices.getDisplayMedia({
          video: true, // Required by Chrome API
          audio: {
            echoCancellation: false,  // Disable for meeting audio
            noiseSuppression: false,  // Disable for meeting audio
            autoGainControl: false,   // Disable for meeting audio
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

        // Initialize enhanced audio processing
        await this.initializeEnhancedProcessing();
  
        // Create MediaRecorder for backup
        this.mediaRecorder = new MediaRecorder(this.audioStream, {
          mimeType: 'audio/webm;codecs=opus'
        });
  
        this.setupRecorderEvents();
        
        // Use environment-specific chunk interval
        const chunkInterval = window.SCRUMBOT_CONFIG?.AUDIO_CHUNK_INTERVAL || 1000;
        this.mediaRecorder.start(chunkInterval);
        this.isRecording = true;
        
        if (window.SCRUMBOT_CONFIG?.DEBUG) {
          console.log(`[AudioCapture] Enhanced recording started with ${chunkInterval}ms chunks`);
        }
        
        console.log('[ScrumBot] Enhanced audio capture started');
        return true;
      } catch (error) {
        console.error('[ScrumBot] Enhanced audio capture failed:', error);
        
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

    async initializeEnhancedProcessing() {
      console.log('[AudioCapture] Initializing enhanced audio processing...');
      
      // Create audio context for real-time processing
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: this.sampleRate
      });

      const source = this.audioContext.createMediaStreamSource(this.audioStream);
      
      // Create script processor for real-time analysis and PCM capture
      this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);
      
      this.processor.onaudioprocess = (event) => {
        if (!this.isRecording) return;
        
        const inputBuffer = event.inputBuffer;
        const inputData = inputBuffer.getChannelData(0);
        
        // Analyze audio level
        const audioLevel = this.analyzeAudioLevel(inputData);
        
        // Store PCM data for file generation
        const pcmData = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          pcmData[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32768));
        }
        this.recordedPCMData.push(pcmData);
        
        // Log audio levels for debugging
        if (audioLevel.peak > this.minAudioLevel) {
          console.log(`🎵 Audio detected - Peak: ${audioLevel.peak.toFixed(4)}, RMS: ${audioLevel.rms.toFixed(4)}`);
        }
      };

      source.connect(this.processor);
      this.processor.connect(this.audioContext.destination);
      
      console.log('[AudioCapture] Enhanced audio processing initialized');
    }

    analyzeAudioLevel(samples) {
      let sum = 0;
      let peak = 0;
      
      for (let i = 0; i < samples.length; i++) {
        const sample = Math.abs(samples[i]);
        sum += sample * sample;
        peak = Math.max(peak, sample);
      }
      
      const rms = Math.sqrt(sum / samples.length);
      
      return {
        peak,
        rms,
        average: sum / samples.length,
        isLikelySpeech: peak > this.silenceThreshold && rms > this.minAudioLevel
      };
    }

    generateWAVFile() {
      console.log(`[AudioCapture] Generating WAV file from ${this.recordedPCMData.length} PCM chunks`);
      
      if (this.recordedPCMData.length === 0) {
        console.warn('[AudioCapture] No PCM data recorded - creating silence file');
        // Create 1 second of silence as fallback
        const silenceData = new Int16Array(this.sampleRate);
        this.recordedPCMData = [silenceData];
      }
      
      // Calculate total samples
      const totalSamples = this.recordedPCMData.reduce((sum, chunk) => sum + chunk.length, 0);
      const duration = totalSamples / this.sampleRate;
      
      console.log(`[AudioCapture] WAV file stats:`);
      console.log(`  - Duration: ${duration.toFixed(2)}s`);
      console.log(`  - Sample Rate: ${this.sampleRate}Hz`);
      console.log(`  - Total Samples: ${totalSamples}`);
      console.log(`  - PCM Chunks: ${this.recordedPCMData.length}`);
      
      // Combine all PCM chunks
      const combinedData = new Int16Array(totalSamples);
      let offset = 0;
      for (const chunk of this.recordedPCMData) {
        combinedData.set(chunk, offset);
        offset += chunk.length;
      }
      
      // Create WAV file
      const wavBuffer = this.createWAVBuffer(combinedData);
      const blob = new Blob([wavBuffer], { type: 'audio/wav' });
      
      // Download file
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `scrumbot-enhanced-${timestamp}.wav`;
      
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      
      // Clean up URL after a delay
      setTimeout(() => {
        URL.revokeObjectURL(url);
      }, 1000);
      
      console.log(`[AudioCapture] WAV file downloaded: ${filename}`);
      console.log(`[AudioCapture] File size: ${(blob.size / 1024).toFixed(1)}KB`);
      
      return filename;
    }

    createWAVBuffer(pcmData) {
      const length = pcmData.length;
      const buffer = new ArrayBuffer(44 + length * 2);
      const view = new DataView(buffer);
      
      // WAV header
      const writeString = (offset, string) => {
        for (let i = 0; i < string.length; i++) {
          view.setUint8(offset + i, string.charCodeAt(i));
        }
      };
      
      writeString(0, 'RIFF');
      view.setUint32(4, 36 + length * 2, true);
      writeString(8, 'WAVE');
      writeString(12, 'fmt ');
      view.setUint32(16, 16, true);
      view.setUint16(20, 1, true);
      view.setUint16(22, 1, true); // mono
      view.setUint32(24, this.sampleRate, true);
      view.setUint32(28, this.sampleRate * 2, true);
      view.setUint16(32, 2, true);
      view.setUint16(34, 16, true);
      writeString(36, 'data');
      view.setUint32(40, length * 2, true);
      
      // PCM data
      let offset = 44;
      for (let i = 0; i < length; i++) {
        view.setInt16(offset, pcmData[i], true);
        offset += 2;
      }
      
      return buffer;
    }

    handleTranscriptionResult(data) {
      console.log('[AudioCapture] Transcription result:', data);
      // Dispatch event for UI updates
      window.dispatchEvent(new CustomEvent('scrumbot-transcription', {
        detail: data
      }));
    }
  
    stopCapture() {
      console.log('[ScrumBot] Stopping enhanced audio capture...');
      
      if (this.mediaRecorder && this.isRecording) {
        this.mediaRecorder.stop();
      }
      
      // Stop enhanced processing
      if (this.processor) {
        this.processor.onaudioprocess = null;
        this.processor.disconnect();
        this.processor = null;
      }
      
      if (this.audioContext && this.audioContext.state !== 'closed') {
        this.audioContext.close().then(() => {
          console.log('[ScrumBot] AudioContext closed');
        }).catch(err => {
          console.error('[ScrumBot] Error closing AudioContext:', err);
        });
        this.audioContext = null;
      }
      
      if (this.audioStream) {
        this.audioStream.getTracks().forEach(track => track.stop());
        this.audioStream = null;
      }
      
      // Generate WAV file from recorded PCM data
      if (this.recordedPCMData.length > 0) {
        console.log('[ScrumBot] Generating enhanced WAV file...');
        this.generateWAVFile();
      } else {
        console.warn('[ScrumBot] No PCM data to generate WAV file');
      }
      
      // Reset state
      this.audioChunks = [];
      this.recordedPCMData = [];
      this.isRecording = false;
      
      console.log('[ScrumBot] Enhanced audio capture stopped and cleaned up');
    }
  }
  
  // Make available globally
  window.scrumBotAudioCapture = new AudioCapture();
  