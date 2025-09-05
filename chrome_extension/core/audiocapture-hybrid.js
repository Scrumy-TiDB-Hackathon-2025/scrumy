/**
 * Hybrid Audio Capture - Captures both tab audio (participants) and microphone (host)
 * Based on expert system recommendations
 */

class AudioCaptureHybrid {
  constructor() {
    this.context = null;
    this.tabStream = null;
    this.micStream = null;
    this.mixedStream = null;
    this.processor = null;
    this.isCapturing = false;
    this.currentMode = 'hybrid';
    this.retryCount = 0;
    this.maxRetries = 3;
    this.audioChunks = [];
    this.sampleRate = 16000;
    this.channels = 1;
    this.startTime = null;
  }

  async initialize() {
    console.log('🎤 AudioCaptureHybrid: Initializing hybrid capture');
    
    try {
      this.context = new AudioContext({ sampleRate: 16000 });
      this.processor = new AudioProcessor(this.context);
      
      // Try hybrid mode first
      await this.initializeHybridMode();
      
      console.log('✅ AudioCaptureHybrid: Initialized successfully in', this.currentMode, 'mode');
      return true;
      
    } catch (error) {
      console.error('❌ AudioCaptureHybrid: Initialization failed:', error);
      return false;
    }
  }

  async initializeHybridMode() {
    try {
      // Request both streams
      const [tabStream, micStream] = await Promise.all([
        this.captureTabAudio(),
        this.captureMicAudio()
      ]);

      this.tabStream = tabStream;
      this.micStream = micStream;
      this.currentMode = 'hybrid';
      
      console.log('✅ AudioCaptureHybrid: Both streams captured successfully');
      
    } catch (error) {
      console.log('⚠️ AudioCaptureHybrid: Hybrid mode failed, trying fallback');
      await this.handleFallback(error);
    }
  }

  async captureTabAudio() {
    return await navigator.mediaDevices.getDisplayMedia({
      video: true, // Required by Chrome
      audio: {
        echoCancellation: false,
        noiseSuppression: false,
        autoGainControl: false,
        sampleRate: 16000
      }
    });
  }

  async captureMicAudio() {
    return await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: false,  // Disable to preserve voice quality
        noiseSuppression: false,  // Disable to preserve voice quality
        autoGainControl: false,   // Disable to prevent volume reduction
        sampleRate: 16000
      }
    });
  }

  async handleFallback(error) {
    if (this.retryCount >= this.maxRetries) {
      if (this.currentMode === 'hybrid') {
        console.log('🔄 AudioCaptureHybrid: Falling back to tab-only mode');
        this.currentMode = 'tab_only';
        this.tabStream = await this.captureTabAudio();
        this.micStream = null;
      } else {
        throw new Error('All capture modes failed');
      }
      this.retryCount = 0;
    } else {
      this.retryCount++;
      throw error;
    }
  }

  async startCapture() {
    if (this.isCapturing) return;
    
    console.log('🎬 AudioCaptureHybrid: Starting capture in', this.currentMode, 'mode');
    
    try {
      // Stop video tracks if present
      if (this.tabStream) {
        this.tabStream.getVideoTracks().forEach(track => track.stop());
      }

      // Create mixed stream based on mode
      if (this.currentMode === 'hybrid' && this.tabStream && this.micStream) {
        this.mixedStream = await this.processor.mixStreams(this.tabStream, this.micStream);
      } else if (this.tabStream) {
        this.mixedStream = this.tabStream;
      } else {
        throw new Error('No audio streams available');
      }

      // Reset audio chunks for file generation
      this.audioChunks = [];
      this.startTime = Date.now();

      // Start enhanced processing with WebSocket transmission
      await this.processor.startProcessing(this.mixedStream, (audioData) => {
        this.sendAudioToBackend(audioData);
      });

      this.isCapturing = true;
      console.log('✅ AudioCaptureHybrid: Capture started successfully');
      
    } catch (error) {
      console.error('❌ AudioCaptureHybrid: Start capture failed:', error);
      throw error;
    }
  }

  stopCapture() {
    if (!this.isCapturing) return;
    
    console.log('⏹️ AudioCaptureHybrid: Stopping capture');
    
    // Stop processing first
    if (this.processor) {
      this.processor.stopProcessing();
      this.processor = null;
    }
    
    // Stop all media tracks
    if (this.tabStream) {
      this.tabStream.getTracks().forEach(track => {
        track.stop();
        track.enabled = false;
      });
      this.tabStream = null;
    }
    
    if (this.micStream) {
      this.micStream.getTracks().forEach(track => {
        track.stop();
        track.enabled = false;
      });
      this.micStream = null;
    }
    
    if (this.mixedStream) {
      this.mixedStream.getTracks().forEach(track => {
        track.stop();
        track.enabled = false;
      });
      this.mixedStream = null;
    }
    
    // File download handled by MediaRecorder in processor
    
    // Close audio context
    if (this.context && this.context.state !== 'closed') {
      this.context.close().then(() => {
        console.log('✅ AudioContext closed');
      }).catch(err => {
        console.error('❌ Error closing AudioContext:', err);
      });
      this.context = null;
    }
    
    this.isCapturing = false;
    console.log('✅ AudioCaptureHybrid: Capture stopped and cleaned up');
  }

  sendAudioToBackend(audioData) {
    // This will be overridden by the capture helper
    console.log('🎵 AudioCaptureHybrid: Audio data ready:', audioData.length, 'bytes');
    
    // If no override, log warning
    if (this.sendAudioToBackend === AudioCaptureHybrid.prototype.sendAudioToBackend) {
      console.warn('⚠️ AudioCaptureHybrid: sendAudioToBackend not overridden by capture helper');
    }
  }

  generateWAVFile() {
    console.log(`🎤 AudioCaptureHybrid: Generating WAV file from ${this.audioChunks.length} chunks`);
    
    if (this.audioChunks.length === 0) {
      console.log('⚠️ AudioCaptureHybrid: No audio chunks to save - creating empty file');
      // Create a small dummy file so user knows something happened
      const dummyData = new Int16Array(16000); // 1 second of silence
      this.audioChunks = [dummyData];
    }
    
    // Calculate total samples
    const totalSamples = this.audioChunks.reduce((sum, chunk) => sum + chunk.length, 0);
    const duration = totalSamples / this.sampleRate;
    
    console.log(`🎤 AudioCaptureHybrid: Generating WAV file:`);
    console.log(`  - Mode: ${this.currentMode}`);
    console.log(`  - Duration: ${duration.toFixed(2)}s`);
    console.log(`  - Sample Rate: ${this.sampleRate}Hz`);
    console.log(`  - Channels: ${this.channels}`);
    console.log(`  - Total Samples: ${totalSamples}`);
    console.log(`  - Chunks: ${this.audioChunks.length}`);
    
    // Combine all chunks
    const combinedData = new Int16Array(totalSamples);
    let offset = 0;
    for (const chunk of this.audioChunks) {
      combinedData.set(chunk, offset);
      offset += chunk.length;
    }
    
    // Create WAV file
    const wavBuffer = this.createWAVBuffer(combinedData);
    const blob = new Blob([wavBuffer], { type: 'audio/wav' });
    
    // Download file
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `scrumbot-hybrid-${this.currentMode}-${timestamp}.wav`;
    
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
    
    console.log(`🎤 AudioCaptureHybrid: WAV file downloaded: ${filename}`);
    console.log(`🎤 AudioCaptureHybrid: File size: ${(blob.size / 1024).toFixed(1)}KB`);
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
    view.setUint16(22, this.channels, true);
    view.setUint32(24, this.sampleRate, true);
    view.setUint32(28, this.sampleRate * this.channels * 2, true);
    view.setUint16(32, this.channels * 2, true);
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

  async processRecordedChunks(onAudioData) {
    if (this.recordedChunks.length === 0) {
      console.log('⚠️ No recorded chunks to process');
      return;
    }
    
    console.log(`🔄 Processing ${this.recordedChunks.length} recorded chunks`);
    
    // Combine all chunks into single blob
    const blob = new Blob(this.recordedChunks, { type: 'audio/webm' });
    console.log(`📦 Combined blob size: ${blob.size} bytes`);
    
    // For now, create dummy PCM data to ensure file generation works
    const dummySize = Math.floor(blob.size / 4); // Rough estimate
    const pcmData = new Int16Array(dummySize);
    
    // Fill with some audio data (silence for now)
    for (let i = 0; i < pcmData.length; i++) {
      pcmData[i] = 0; // Silence, but file will be generated
    }
    
    console.log(`🎵 Generated PCM data: ${pcmData.length} samples`);
    onAudioData(pcmData);
  }

  getCurrentMode() {
    return this.currentMode;
  }
}

class AudioProcessor {
  constructor(context) {
    this.context = context;
    this.mixer = null;
    this.analyzer = null;
    this.processor = null;
    this.isProcessing = false;
  }

  async mixStreams(tabStream, micStream) {
    console.log('🎛️ AudioProcessor: Mixing streams');
    
    // Create source nodes
    const tabSource = this.context.createMediaStreamSource(tabStream);
    const micSource = this.context.createMediaStreamSource(micStream);

    // Create gain nodes for volume control
    const tabGain = this.context.createGain();
    const micGain = this.context.createGain();

    // Boost tab audio and normalize mic
    tabGain.gain.value = 1.5;  // Boost participant audio
    micGain.gain.value = 2.0;  // Boost host mic audio

    // Create mixer and analyzer
    this.mixer = this.context.createGain();
    this.analyzer = this.context.createAnalyser();

    // Connect audio graph
    tabSource.connect(tabGain).connect(this.mixer);
    micSource.connect(micGain).connect(this.mixer);
    this.mixer.connect(this.analyzer);

    // Create output stream
    const destination = this.context.createMediaStreamDestination();
    this.mixer.connect(destination);

    console.log('✅ AudioProcessor: Streams mixed successfully');
    return destination.stream;
  }

  async startProcessing(stream, onAudioData) {
    if (this.isProcessing) return;
    
    console.log('🔄 AudioProcessor: Starting enhanced WebSocket processing');
    
    // Create script processor for real-time WebSocket transmission
    this.processor = this.context.createScriptProcessor(4096, 1, 1);
    
    const source = this.context.createMediaStreamSource(stream);
    source.connect(this.processor);
    this.processor.connect(this.context.destination);
    
    // Also start MediaRecorder for backup file
    this.mediaRecorder = new MediaRecorder(stream);
    this.recordedChunks = [];
    
    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) {
        this.recordedChunks.push(event.data);
      }
    };
    
    this.mediaRecorder.onstop = () => {
      const blob = new Blob(this.recordedChunks, { type: 'audio/webm' });
      this.downloadBlob(blob);
    };
    
    this.processor.onaudioprocess = (event) => {
      if (!this.isProcessing || !event || !event.inputBuffer) return;
      
      try {
        const inputBuffer = event.inputBuffer;
        const channelData = inputBuffer.getChannelData(0);
        
        if (!channelData || channelData.length === 0) return;
        
        // Convert to 16-bit PCM for WebSocket
        const pcmData = new Int16Array(channelData.length);
        for (let i = 0; i < channelData.length; i++) {
          pcmData[i] = Math.max(-32768, Math.min(32767, channelData[i] * 32768));
        }
        
        // Send to WebSocket via callback
        if (onAudioData) {
          const audioData = btoa(String.fromCharCode(...new Uint8Array(pcmData.buffer)));
          onAudioData(audioData);
        }
        
      } catch (error) {
        console.error('❌ AudioProcessor: Error in processing:', error);
      }
    };
    
    this.mediaRecorder.start(1000);
    this.isProcessing = true;
    
    console.log('✅ AudioProcessor: Enhanced processing started (WebSocket + File)');
  }

  stopProcessing() {
    if (!this.isProcessing) return;
    
    console.log('⏹️ AudioProcessor: Stopping enhanced processing');
    
    // Stop ScriptProcessor
    if (this.processor) {
      this.processor.onaudioprocess = null;
      this.processor.disconnect();
      this.processor = null;
    }
    
    // Stop MediaRecorder
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop();
    }
    
    // Disconnect all nodes
    if (this.mixer) {
      this.mixer.disconnect();
      this.mixer = null;
    }
    
    if (this.analyzer) {
      this.analyzer.disconnect();
      this.analyzer = null;
    }
    
    this.isProcessing = false;
    this.mediaRecorder = null;
    this.recordedChunks = [];
  }
  
  downloadBlob(blob) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `scrumbot-hybrid-direct-${timestamp}.webm`;
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    setTimeout(() => {
      URL.revokeObjectURL(url);
    }, 1000);
    
    console.log(`📥 Downloaded: ${filename} (${blob.size} bytes)`);
  }
}

// Export for use
window.AudioCaptureHybrid = AudioCaptureHybrid;
window.AudioProcessor = AudioProcessor;

console.log('✅ AudioCaptureHybrid: Hybrid audio capture module loaded');