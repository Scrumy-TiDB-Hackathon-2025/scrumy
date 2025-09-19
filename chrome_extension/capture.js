// capture.js - Helper tab for multi-tab audio capture
console.log("🎬 ScrumBot Capture Helper loaded");

class CaptureHelper {
  constructor() {
    this.audioCapture = null;
    this.isCapturing = false;
    this.meetingTabId = null;
    this.isFlushing = false;
    this.pendingAudioChunks = [];
    this.flushTimeoutId = null;
    this.FLUSH_TIMEOUT_MS = 5000; // 5 seconds to flush all buffered audio

    this.initializeElements();
    this.setupEventListeners();
    this.parseURLParams();
  }

  initializeElements() {
    this.captureBtn = document.getElementById("captureBtn");
    this.statusDiv = document.getElementById("status");
  }

  setupEventListeners() {
    this.captureBtn.addEventListener("click", () => this.startCapture());

    // Add test button listener
    const testBtn = document.getElementById("testBtn");
    if (testBtn) {
      testBtn.addEventListener("click", () => this.startDirectTest());
    }

    // Listen for messages from meeting tab
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      this.handleMessage(message, sender, sendResponse);
    });
  }

  parseURLParams() {
    const urlParams = new URLSearchParams(window.location.search);
    this.meetingTabId = urlParams.get("meetingTabId");

    if (window.SCRUMBOT_CONFIG?.DEBUG) {
      console.log("[CaptureHelper] Meeting tab ID:", this.meetingTabId);
    }
  }

  async startCapture() {
    try {
      this.showStatus("Starting capture...", "info");
      this.captureBtn.disabled = true;
      this.captureBtn.textContent = "⏳ Starting...";

      console.log("🧪 [CaptureHelper] Starting test capture");

      // Initialize audio capture if not already done
      if (!this.audioCapture) {
        console.log("🎤 [CaptureHelper] Initializing AudioCaptureHybrid");
        this.audioCapture = new AudioCaptureHybrid();
        const initialized = await this.audioCapture.initialize();
        if (!initialized) {
          throw new Error("Failed to initialize hybrid audio capture");
        }
      }

      // Start hybrid capture (handles both tab and mic internally)
      console.log("🎤 [CaptureHelper] Starting hybrid audio capture");
      await this.audioCapture.startCapture();
      console.log(
        "🎤 [CaptureHelper] Hybrid audio capture started successfully",
      );
      this.handleCaptureSuccess();
    } catch (error) {
      console.error("🧪 [CaptureHelper] Capture error:", error);
      this.handleCaptureFailure(error.message);
    }
  }

  handleCaptureSuccess() {
    this.isCapturing = true;
    this.recordingStartTime = Date.now();
    this.showStatus(
      "🎤 Hybrid recording started! Capturing tab + microphone audio.",
      "success",
    );
    this.captureBtn.textContent = "🔴 Recording (Hybrid)";

    // Add stop button
    setTimeout(() => {
      this.captureBtn.textContent = "⏹️ Stop Recording";
      this.captureBtn.disabled = false;
      this.captureBtn.onclick = () => this.stopCapture();
    }, 1000);

    // Set up audio forwarding to WebSocket
    this.setupAudioForwarding();

    // Send meeting start signal
    this.sendMeetingStartSignal();

    // Notify meeting tab
    this.notifyMeetingTab("CAPTURE_STARTED", {
      success: true,
      mode: this.audioCapture.getCurrentMode(),
    });

    // Keep tab open for user control
    this.showStatus(
      "🎤 Hybrid mode: Recording tab + mic audio. Audio streaming to server.",
      "info",
    );
  }

  handleCaptureFailure(errorMessage) {
    this.showStatus(`❌ Capture failed: ${errorMessage}`, "error");
    this.captureBtn.disabled = false;
    this.captureBtn.textContent = "📹 Try Again";

    // Notify the meeting tab about the failure
    this.notifyMeetingTab("CAPTURE_FAILED", {
      success: false,
      error: errorMessage,
    });
  }

  setupAudioForwarding() {
    // Override the audio capture's sendAudioToBackend method
    // to forward to the meeting tab via WebSocket
    this.audioCapture.sendAudioToBackend = (audioData) => {
      console.log(
        "[CaptureHelper] Forwarding audio to meeting tab:",
        audioData.length,
        "bytes",
      );

      // If we're flushing, add to pending chunks for tracking
      if (this.isFlushing) {
        this.pendingAudioChunks.push({
          data: audioData,
          timestamp: Date.now(),
          id: Date.now() + Math.random(),
        });
        console.log(
          "[CaptureHelper] Added chunk to flush queue, total pending:",
          this.pendingAudioChunks.length,
        );
      }

      // Forward to meeting tab for WebSocket transmission
      this.notifyMeetingTab("AUDIO_DATA", {
        audioData: audioData,
        timestamp: Date.now(),
        chunkId: this.isFlushing
          ? this.pendingAudioChunks[this.pendingAudioChunks.length - 1].id
          : null,
        isFlushing: this.isFlushing,
      });
    };
  }

  notifyMeetingTab(type, data) {
    chrome.runtime.sendMessage({
      type: "HELPER_TO_MEETING",
      targetTabId: this.meetingTabId,
      messageType: type,
      data: data,
    });
  }

  handleMessage(message, sender, sendResponse) {
    switch (message.type) {
      case "MEETING_TO_HELPER":
        this.handleMeetingMessage(message.messageType, message.data);
        break;

      case "STOP_CAPTURE":
        this.stopCapture();
        break;
    }
  }

  handleMeetingMessage(messageType, data) {
    switch (messageType) {
      case "STOP_RECORDING":
        this.stopCapture();
        break;

      case "FLUSH_AND_STOP_RECORDING":
        this.flushAndStopRecording();
        break;

      case "CHUNK_PROCESSED":
        this.handleChunkProcessed(data);
        break;

      case "GET_STATUS":
        this.notifyMeetingTab("STATUS_RESPONSE", {
          isCapturing: this.isCapturing,
          hasAudioStream: !!this.audioCapture?.audioStream,
          isFlushing: this.isFlushing,
          pendingChunks: this.pendingAudioChunks.length,
        });
        break;
    }
  }

  flushAndStopRecording() {
    if (!this.audioCapture || !this.isCapturing) {
      console.log(
        "[CaptureHelper] Not capturing, sending immediate flush complete",
      );
      this.notifyMeetingTab("AUDIO_FLUSH_COMPLETE", {
        success: true,
        chunksRemaining: 0,
      });
      return;
    }

    console.log("[CaptureHelper] ⏳ Starting audio buffer flush...");
    this.isFlushing = true;
    this.pendingAudioChunks = [];

    // Update UI to show flushing state
    this.showStatus("⏳ Flushing audio buffers...", "info");
    this.captureBtn.textContent = "⏳ Flushing Buffers...";
    this.captureBtn.disabled = true;

    // Set a timeout to force completion if flush takes too long
    this.flushTimeoutId = setTimeout(() => {
      console.log("[CaptureHelper] ⏰ Flush timeout reached, force completing");
      this.completeFlushAndStop(true);
    }, this.FLUSH_TIMEOUT_MS);

    // Stop new audio capture but let existing buffers flush
    if (this.audioCapture) {
      // Give the audio capture system a moment to flush its internal buffers
      setTimeout(() => {
        this.audioCapture.stopCapture();
        console.log(
          "[CaptureHelper] Audio capture stopped, waiting for buffer flush completion",
        );

        // Check if we have pending chunks, if not complete immediately
        if (this.pendingAudioChunks.length === 0) {
          setTimeout(() => {
            if (this.pendingAudioChunks.length === 0) {
              console.log(
                "[CaptureHelper] No pending chunks detected, completing flush",
              );
              this.completeFlushAndStop(false);
            }
          }, 1000); // Wait 1 second to see if any chunks arrive
        }
      }, 500); // Allow 500ms for final chunks to be processed
    }
  }

  handleChunkProcessed(data) {
    if (!this.isFlushing || !data.chunkId) return;

    // Remove the processed chunk from pending list
    const index = this.pendingAudioChunks.findIndex(
      (chunk) => chunk.id === data.chunkId,
    );
    if (index !== -1) {
      this.pendingAudioChunks.splice(index, 1);
      console.log(
        "[CaptureHelper] Chunk processed, remaining:",
        this.pendingAudioChunks.length,
      );

      // If no more pending chunks, complete the flush
      if (this.pendingAudioChunks.length === 0) {
        console.log(
          "[CaptureHelper] ✅ All chunks processed, completing flush",
        );
        this.completeFlushAndStop(false);
      }
    }
  }

  completeFlushAndStop(timedOut = false) {
    if (!this.isFlushing) return; // Already completed

    console.log(
      "[CaptureHelper] ✅ Completing flush and stop, timed out:",
      timedOut,
    );

    // Clear flush timeout
    if (this.flushTimeoutId) {
      clearTimeout(this.flushTimeoutId);
      this.flushTimeoutId = null;
    }

    const remainingChunks = this.pendingAudioChunks.length;

    // Reset state
    this.isFlushing = false;
    this.isCapturing = false;
    this.pendingAudioChunks = [];

    // Update UI
    this.showStatus(
      timedOut
        ? "⚠️ Flush timeout - some audio may be lost"
        : "✅ All audio buffers flushed successfully",
      timedOut ? "warning" : "success",
    );
    this.captureBtn.textContent = "✅ Flush Complete";

    // Notify meeting tab with flush completion
    this.notifyMeetingTab("AUDIO_FLUSH_COMPLETE", {
      success: true,
      timedOut: timedOut,
      chunksRemaining: remainingChunks,
    });

    // Send meeting end signal
    this.sendMeetingEndSignal();
  }

  stopCapture() {
    if (this.audioCapture && this.isCapturing && !this.isFlushing) {
      this.audioCapture.stopCapture();
      this.isCapturing = false;

      this.showStatus(
        "🎤 Hybrid recording stopped - WAV file downloading...",
        "success",
      );
      this.captureBtn.textContent = "✅ File Generated";
      this.captureBtn.disabled = true;

      // Notify meeting tab
      this.notifyMeetingTab("CAPTURE_STOPPED", {
        success: true,
      });

      // Keep tab open for user to manually close
      this.showStatus(
        "🎤 Recording complete! Check downloads for hybrid audio file.",
        "success",
      );
    }
  }

  showStatus(message, type = "info") {
    this.statusDiv.textContent = message;
    this.statusDiv.className = `status ${type}`;
    this.statusDiv.style.display = "block";

    console.log(`[CaptureHelper] ${type.toUpperCase()}: ${message}`);
  }

  // WebSocket methods for meeting signals
  initializeWebSocket() {
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      return;
    }

    const wsUrl = window.SCRUMBOT_CONFIG?.WEBSOCKET_URL;
    if (!wsUrl) {
      console.log("[CaptureHelper] No WebSocket URL configured");
      return;
    }

    console.log("[CaptureHelper] 🔌 Connecting to WebSocket:", wsUrl);

    this.websocket = new WebSocket(wsUrl);

    this.websocket.onopen = () => {
      console.log("[CaptureHelper] ✅ WebSocket connected");
    };

    this.websocket.onerror = (error) => {
      console.error("[CaptureHelper] ❌ WebSocket error:", error);
    };

    this.websocket.onclose = () => {
      console.log("[CaptureHelper] 🔌 WebSocket disconnected");
    };
  }

  sendMeetingStartSignal() {
    this.initializeWebSocket();

    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      const message = {
        type: "MEETING_EVENT",
        eventType: "started",
        data: {
          meetingUrl: window.location.href,
          participants: [{ id: "user1", name: "Meeting Participant" }],
          timestamp: new Date().toISOString(),
        },
      };

      this.websocket.send(JSON.stringify(message));
      console.log("[CaptureHelper] 🔄 Meeting start signal sent via WebSocket");
    } else {
      console.log(
        "[CaptureHelper] ⚠️ WebSocket not connected, cannot send meeting start signal",
      );
    }
  }

  sendMeetingEndSignal() {
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      const message = {
        type: "MEETING_EVENT",
        eventType: "ended",
        data: {
          meetingUrl: window.location.href,
          participants: [{ id: "user1", name: "Meeting Participant" }],
          duration: Date.now() - (this.recordingStartTime || Date.now()),
          timestamp: new Date().toISOString(),
        },
      };

      this.websocket.send(JSON.stringify(message));
      console.log("[CaptureHelper] 🔄 Meeting end signal sent via WebSocket");
    } else {
      console.log(
        "[CaptureHelper] ⚠️ WebSocket not connected, cannot send meeting end signal",
      );
    }
  }

  async startDirectTest() {
    try {
      this.showStatus("🧪 Starting direct audio test...", "info");

      const testBtn = document.getElementById("testBtn");
      const captureBtn = document.getElementById("captureBtn");

      testBtn.disabled = true;
      captureBtn.disabled = true;
      testBtn.textContent = "⏳ Starting Test...";

      // Get display media stream
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: true,
        audio: {
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false,
          sampleRate: 16000,
        },
      });

      // Stop video tracks
      stream.getVideoTracks().forEach((track) => track.stop());

      // Initialize test audio capture
      const testCapture = new AudioCaptureTest();
      await testCapture.initialize();
      await testCapture.startCapture(stream);

      this.showStatus(
        "🔴 Test recording active! Speak for 10-30 seconds...",
        "success",
      );
      testBtn.textContent = "⏹️ Stop Test";
      testBtn.disabled = false;

      // Change button to stop function
      testBtn.onclick = () => {
        testCapture.stopCapture();
        this.showStatus(
          "✅ Test complete! Check downloads for WAV file.",
          "success",
        );
        testBtn.textContent = "✅ Test Complete";
        testBtn.disabled = true;
        captureBtn.disabled = false;
      };
    } catch (error) {
      console.error("🧪 Direct test error:", error);
      this.showStatus("❌ Test failed: " + error.message, "error");

      const testBtn = document.getElementById("testBtn");
      const captureBtn = document.getElementById("captureBtn");
      testBtn.disabled = false;
      captureBtn.disabled = false;
      testBtn.textContent = "🧪 Try Again";
    }
  }

  // Validate that the selected tab is actually a meeting
  validateMeetingTab(stream) {
    // This is called after successful capture
    // We can add validation logic here

    const audioTracks = stream.getAudioTracks();
    if (audioTracks.length === 0) {
      throw new Error("No audio tracks found in selected tab");
    }

    // Additional validation could include:
    // - Check if tab URL matches meeting platforms
    // - Verify audio content (not just silence)
    // - Detect meeting-specific audio patterns

    return true;
  }
}

// Initialize capture helper when page loads
document.addEventListener("DOMContentLoaded", () => {
  window.captureHelper = new CaptureHelper();
});

// Handle page unload
window.addEventListener("beforeunload", () => {
  if (window.captureHelper && window.captureHelper.isCapturing) {
    window.captureHelper.stopCapture();
  }
});
