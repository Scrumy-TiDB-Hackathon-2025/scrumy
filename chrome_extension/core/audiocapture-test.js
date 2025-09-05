/**
 * Test Audio Capture - Saves audio to downloadable WAV file
 * Use this to verify Chrome is capturing proper audio before WebSocket transmission
 */

class AudioCaptureTest {
  constructor() {
    this.audioChunks = [];
    this.isRecording = false;
    this.sampleRate = 16000;
    this.channels = 1;
    this.startTime = null;
  }

  async initialize() {
    console.log('🧪 AudioCaptureTest: Initializing test mode');
    return true;
  }

  async startCapture(stream) {
    if (this.isRecording) return;
    
    this.isRecording = true;
    this.audioChunks = [];
    this.startTime = Date.now();
    
    console.log('🧪 AudioCaptureTest: Starting audio capture for file download');
    
    try {
      // Create audio context
      const audioContext = new AudioContext({ sampleRate: this.sampleRate });
      const source = audioContext.createMediaStreamSource(stream);
      
      // Create script processor
      const processor = audioContext.createScriptProcessor(4096, this.channels, this.channels);
      
      processor.onaudioprocess = (event) => {
        if (!this.isRecording) return;
        
        const inputBuffer = event.inputBuffer;
        const channelData = inputBuffer.getChannelData(0);
        
        // Convert to 16-bit PCM
        const pcmData = new Int16Array(channelData.length);
        for (let i = 0; i < channelData.length; i++) {
          pcmData[i] = Math.max(-32768, Math.min(32767, channelData[i] * 32768));
        }
        
        this.audioChunks.push(pcmData);
        
        // Log progress every 2 seconds
        const elapsed = (Date.now() - this.startTime) / 1000;
        if (Math.floor(elapsed) % 2 === 0 && elapsed > 0) {
          console.log(`🧪 AudioCaptureTest: Recording ${elapsed.toFixed(1)}s, ${this.audioChunks.length} chunks`);
        }
      };
      
      source.connect(processor);
      processor.connect(audioContext.destination);
      
      // Store references for cleanup
      this.audioContext = audioContext;
      this.processor = processor;
      this.source = source;
      
      console.log('🧪 AudioCaptureTest: Audio capture started successfully');
      
    } catch (error) {
      console.error('🧪 AudioCaptureTest: Error starting capture:', error);
      this.isRecording = false;
    }
  }

  stopCapture() {
    if (!this.isRecording) return;
    
    this.isRecording = false;
    
    console.log('🧪 AudioCaptureTest: Stopping capture and generating WAV file');
    
    // Cleanup audio context
    if (this.processor) {
      this.processor.disconnect();
    }
    if (this.source) {
      this.source.disconnect();
    }
    if (this.audioContext) {
      this.audioContext.close();
    }
    
    // Generate and download WAV file
    this.generateWAVFile();
  }

  generateWAVFile() {
    if (this.audioChunks.length === 0) {
      console.log('🧪 AudioCaptureTest: No audio chunks to save');
      return;
    }
    
    // Calculate total samples
    const totalSamples = this.audioChunks.reduce((sum, chunk) => sum + chunk.length, 0);
    const duration = totalSamples / this.sampleRate;
    
    console.log(`🧪 AudioCaptureTest: Generating WAV file:`);
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
    const filename = `scrumbot-test-audio-${timestamp}.wav`;
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    
    URL.revokeObjectURL(url);
    
    console.log(`🧪 AudioCaptureTest: WAV file downloaded: ${filename}`);
    console.log(`🧪 AudioCaptureTest: File size: ${(blob.size / 1024).toFixed(1)}KB`);
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

  // Dummy methods to match AudioCapture interface
  async sendAudioToBackend() {
    // No-op in test mode
  }

  initializeWebSocket() {
    // No-op in test mode
  }
}

// Export for use
window.AudioCaptureTest = AudioCaptureTest;

console.log('🧪 AudioCaptureTest: Test audio capture module loaded');