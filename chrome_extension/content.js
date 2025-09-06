console.log('🤖 ScrumBot extension loaded on:', window.location.href);

// Wait for config to load
if (typeof window.SCRUMBOT_CONFIG === 'undefined') {
  console.error('❌ ScrumBot config not loaded');
}

const config = window.SCRUMBOT_CONFIG;
const BACKEND_URL = config.BACKEND_URL;
const FRONTEND_URL = config.FRONTEND_URL;
const ENDPOINTS = config.ENDPOINTS;

let meetingId = null;
let transcriptLog = []; // Store all transcripts for download

// Check if we're on a supported meeting platform
const currentPlatform = config.SUPPORTED_PLATFORMS.find(platform =>
  window.location.href.includes(platform)
);

if (currentPlatform) {
  console.log('✅ ScrumBot: Supported platform detected:', currentPlatform);
  initializeScrumBot();
} else {
  console.log('❌ ScrumBot: Unsupported platform');
}

function initializeScrumBot() {
  // Generate unique meeting ID
  meetingId = 'meeting-' + Date.now() + '-' + Math.random().toString(36).substring(2, 11);
  console.log('📝 Meeting ID:', meetingId);

  // Create enhanced ScrumBot UI
  createEnhancedScrumBotUI();

  // Test backend connection
  testBackendConnection();

  // Wait for core controller to be initialized
  setTimeout(() => {
    if (window.scrumBotController) {
      console.log('✅ ScrumBot controller initialized');
      setupEnhancedEventListeners();
    } else {
      console.error('❌ ScrumBot controller not found - checking components...');
      console.log('Available components:', {
        meetingDetector: !!window.meetingDetector,
        audioCapture: !!window.scrumBotAudioCapture,
        controller: !!window.scrumBotController,
        ui: !!window.scrumBotUI
      });
    }
  }, 1000);
}

function createEnhancedScrumBotUI() {
  if (window.scrumBotUI) {
    window.scrumBotUI.createEnhancedUI(meetingId);
    console.log('✅ Enhanced ScrumBot UI created');
    
    // Make sure the enhanced UI buttons work with multi-tab recording
    const toggleButton = document.getElementById('scrumbot-toggle');
    if (toggleButton) {
      // Override the button text for enhanced mode
      toggleButton.innerHTML = '▶️ Start Enhanced Recording';
    }
  } else {
    console.error('❌ ScrumBot UI component not available');
    // Fallback to basic UI
    createScrumBotUI();
  }
}

function setupEnhancedEventListeners() {
  // Listen for UI events
  window.addEventListener('scrumbot-toggle-recording', () => {
    toggleRecording();
  });
  
  window.addEventListener('scrumbot-open-dashboard', () => {
    openDashboard();
  });
  
  window.addEventListener('scrumbot-test-api', () => {
    testAPI();
  });
  
  window.addEventListener('scrumbot-debug', () => {
    debugComponents();
  });
  
  // Listen for transcription updates
  window.addEventListener('scrumbot-transcription', (event) => {
    if (window.scrumBotUI) {
      window.scrumBotUI.addTranscript(event.detail);
    }
  });
  
  // Listen for speaker attribution
  window.addEventListener('scrumbot-speaker-attribution', (event) => {
    if (window.scrumBotUI) {
      window.scrumBotUI.updateSpeakerAttribution(event.detail);
    }
  });
  
  // Listen for meeting analysis
  window.addEventListener('scrumbot-meeting-analysis', (event) => {
    if (window.scrumBotUI) {
      window.scrumBotUI.updateMeetingAnalysis(event.detail);
    }
  });
  
  // Listen for participant changes
  window.addEventListener('scrumbot-participant-change', (event) => {
    if (window.scrumBotUI) {
      window.scrumBotUI.updateParticipants(event.detail.participants);
    }
  });
}

function createScrumBotUI() {
  // Remove existing panel if it exists
  const existingPanel = document.getElementById('scrumbot-panel');
  if (existingPanel) {
    existingPanel.remove();
  }

  // Create floating ScrumBot control panel
  const scrumBotPanel = document.createElement('div');
  scrumBotPanel.id = 'scrumbot-panel';
  scrumBotPanel.innerHTML = `
    <div style="
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 10000;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 15px;
      border-radius: 12px;
      box-shadow: 0 8px 25px rgba(0,0,0,0.3);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      min-width: 280px;
      backdrop-filter: blur(10px);
    ">
      <div style="display: flex; align-items: center; margin-bottom: 12px;">
        <div style="
          width: 32px;
          height: 32px;
          background: #fff;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 10px;
          font-size: 16px;
        ">🤖</div>
        <div>
          <div style="font-weight: 600; font-size: 14px;">ScrumBot</div>
          <div style="font-size: 11px; opacity: 0.8;" id="connection-status">Connecting...</div>
        </div>
      </div>
      
      <div style="margin-bottom: 12px;">
        <div style="font-size: 12px; opacity: 0.9; margin-bottom: 5px;">Meeting ID:</div>
        <div style="
          background: rgba(255,255,255,0.2);
          padding: 6px 8px;
          border-radius: 6px;
          font-family: monospace;
          font-size: 11px;
          word-break: break-all;
        ">${meetingId}</div>
      </div>
      
      <div style="margin-bottom: 10px; font-size: 11px; opacity: 0.8;">
        Backend: ngrok tunnel ✅
      </div>
      
      <button id="scrumbot-toggle" style="
        width: 100%;
        padding: 10px;
        border: none;
        border-radius: 8px;
        background: #fff;
        color: #333;
        font-weight: 600;
        cursor: pointer;
        font-size: 13px;
        transition: all 0.2s ease;
      ">
        ▶️ Start Recording
      </button>
      
      <div style="margin-top: 8px; display: flex; gap: 5px;">
        <button id="scrumbot-dashboard" style="
          flex: 1;
          padding: 6px;
          border: 1px solid rgba(255,255,255,0.3);
          border-radius: 6px;
          background: transparent;
          color: white;
          cursor: pointer;
          font-size: 11px;
        ">📊 Dashboard</button>
        <button id="scrumbot-test" style="
          flex: 1;
          padding: 6px;
          border: 1px solid rgba(255,255,255,0.3);
          border-radius: 6px;
          background: transparent;
          color: white;
          cursor: pointer;
          font-size: 11px;
        ">🧪 Test API</button>
        <button id="scrumbot-debug" style="
          flex: 1;
          padding: 6px;
          border: 1px solid rgba(255,255,255,0.3);
          border-radius: 6px;
          background: transparent;
          color: white;
          cursor: pointer;
          font-size: 11px;
        ">🔍 Debug</button>
      </div>
      
      <div style="margin-top: 8px;">
        <button id="scrumbot-download" style="
          width: 100%;
          padding: 6px;
          border: 1px solid rgba(255,255,255,0.3);
          border-radius: 6px;
          background: transparent;
          color: white;
          cursor: pointer;
          font-size: 11px;
        ">💾 Download Transcript (<span id="transcript-count">0</span>)</button>
      </div>
    </div>
  `;

  document.body.appendChild(scrumBotPanel);

  // Add event listeners
  document.getElementById('scrumbot-toggle').addEventListener('click', toggleRecording);
  document.getElementById('scrumbot-dashboard').addEventListener('click', openDashboard);
  document.getElementById('scrumbot-test').addEventListener('click', testAPI);
  document.getElementById('scrumbot-debug').addEventListener('click', debugComponents);
  document.getElementById('scrumbot-download').addEventListener('click', downloadTranscript);
}

// Enhanced fetch function with ngrok support
function apiCall(endpoint, options = {}) {
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      'ngrok-skip-browser-warning': 'true',  // Add ngrok bypass header
      ...options.headers
    }
  };

  return fetch(`${BACKEND_URL}${endpoint}`, {
    ...options,
    ...defaultOptions
  });
}

function testBackendConnection() {
  const statusElement = document.getElementById('connection-status');

  apiCall(ENDPOINTS.health)
    .then(response => response.json())
    .then(data => {
      if (data.status === 'healthy') {
        statusElement.textContent = '🟢 Connected';
        statusElement.style.color = '#4ade80';
      } else {
        statusElement.textContent = '🟡 Backend Issues';
        statusElement.style.color = '#fbbf24';
      }
    })
    .catch(error => {
      console.error('❌ Backend connection failed:', error);
      statusElement.textContent = '🔴 Offline';
      statusElement.style.color = '#f87171';
    });
}

// Multi-tab capture state
let helperTabId = null;
let isRecordingViaHelper = false;

async function toggleRecording() {
  if (!isRecordingViaHelper) {
    // Start enhanced recording
    await startEnhancedRecording();
  } else {
    // Stop enhanced recording
    stopEnhancedRecording();
  }
}

async function startEnhancedRecording() {
  console.log('🎬 Starting enhanced recording with participant detection...');
  
  // Get UI elements (fallback to enhanced UI or basic UI)
  const button = document.getElementById('scrumbot-toggle');
  const statusElement = document.getElementById('connection-status');
  
  if (!button || !statusElement) {
    console.error('❌ UI elements not found');
    return;
  }
  
  // Update UI to show we're starting
  button.innerHTML = '⏳ Detecting participants...';
  button.disabled = true;
  statusElement.textContent = '🔍 Detecting meeting participants...';
  
  try {
    // Start participant monitoring if available
    if (window.meetingDetector && !window.meetingDetector.isMonitoringParticipants) {
      await window.meetingDetector.startParticipantMonitoring();
    }
    
    // Get participant info for enhanced context
    const participants = window.meetingDetector?.getParticipants() || [];
    console.log('👥 Detected participants:', participants.length);
    
    // Update UI with participant info
    if (window.scrumBotUI) {
      window.scrumBotUI.updateParticipants(participants);
    }
    
    // Use the proven multi-tab recording approach
    // Update the message to include participant context
    chrome.runtime.sendMessage({
      type: 'CREATE_HELPER_TAB',
      meetingTabId: chrome.runtime.id,
      enhancedMode: true, // Flag for enhanced features
      meetingId: meetingId,
      participants: participants // Include participant context
    }, (response) => {
      if (response && response.success) {
        helperTabId = response.tabId;
        console.log('✅ Enhanced helper tab opened:', helperTabId);
        
        // Update status
        statusElement.textContent = `📹 Select your meeting tab (${participants.length} participants detected)`;
        button.innerHTML = '⏳ Waiting for capture...';
      } else {
        console.error('❌ Failed to create enhanced helper tab:', response?.error);
        
        // Reset UI on failure
        button.innerHTML = '▶️ Start Enhanced Recording';
        button.disabled = false;
        statusElement.textContent = '❌ Failed to open capture tab';
        
        alert('Failed to open capture tab. Please try again.');
      }
    });
    
  } catch (error) {
    console.error('❌ Enhanced recording failed:', error);
    
    // Reset UI on failure
    button.innerHTML = '▶️ Start Enhanced Recording';
    button.disabled = false;
    statusElement.textContent = '❌ Failed to start recording';
    
    // Fallback to basic multi-tab recording
    console.log('🔄 Falling back to basic multi-tab recording...');
    startMultiTabRecording(button, statusElement);
  }
}

function stopEnhancedRecording() {
  console.log('⏹️ Stopping enhanced recording...');
  
  // CRITICAL: Stop recording state first to prevent infinite loops
  isRecordingViaHelper = false;
  wsRetryCount = 0; // Reset WebSocket retry counter
  
  // Get UI elements
  const button = document.getElementById('scrumbot-toggle');
  const statusElement = document.getElementById('connection-status');
  
  // Stop participant monitoring
  if (window.meetingDetector && window.meetingDetector.isMonitoringParticipants) {
    window.meetingDetector.stopParticipantMonitoring();
  }
  
  // Send meeting end signal via WebSocket
  sendMeetingEndSignal();
  
  // Update UI to show processing state
  if (button && statusElement) {
    button.innerHTML = '⏳ Processing final audio...';
    button.disabled = true;
    statusElement.textContent = '🔄 Waiting for server processing...';
  }
  
  // Start dynamic processing timeout
  startProcessingTimeout();
}

function completeRecordingStop() {
  console.log('✅ Completing recording stop...');
  
  // Set shutdown flag to prevent WebSocket reconnection
  isShuttingDown = true;
  
  // Get UI elements
  const button = document.getElementById('scrumbot-toggle');
  const statusElement = document.getElementById('connection-status');
  
  // Use the proven multi-tab stop approach
  if (helperTabId) {
    chrome.runtime.sendMessage({
      type: 'MEETING_TO_HELPER',
      messageType: 'STOP_RECORDING',
      targetTabId: helperTabId
    }, () => {
      // Handle any runtime errors silently
      if (chrome.runtime.lastError) {
        console.log('Helper tab already closed:', chrome.runtime.lastError.message);
      }
    });
  }
  
  // Reset UI
  if (button && statusElement) {
    button.innerHTML = '▶️ Start Enhanced Recording';
    button.style.background = '#fff';
    button.style.color = '#333';
    button.disabled = false;
    statusElement.textContent = '🟢 Connected';
  }
  
  // Update enhanced UI if available
  if (window.scrumBotUI) {
    window.scrumBotUI.updateRecordingState(false, 0);
    window.scrumBotUI.updateParticipants([]);
  }
  
  helperTabId = null;
  
  // Reset shutdown flag after a delay
  setTimeout(() => {
    isShuttingDown = false;
    testBackendConnection(); // Reset status
  }, 2000);
}

function startMultiTabRecording(button, statusElement) {
  console.log('🎬 Starting multi-tab recording...');
  
  // Update UI to show we're starting
  button.innerHTML = '⏳ Opening capture...';
  button.disabled = true;
  statusElement.textContent = '🔄 Opening capture tab...';
  
  // Send message to background script to create helper tab
  chrome.runtime.sendMessage({
    type: 'CREATE_HELPER_TAB',
    meetingTabId: chrome.runtime.id
  }, (response) => {
    if (response && response.success) {
      helperTabId = response.tabId;
      console.log('✅ Helper tab opened:', helperTabId);
      
      // Update status
      statusElement.textContent = '📹 Select your meeting tab in the new window';
      button.innerHTML = '⏳ Waiting for capture...';
    } else {
      console.error('❌ Failed to create helper tab:', response?.error);
      
      // Reset UI on failure
      button.innerHTML = '▶️ Start Recording';
      button.disabled = false;
      statusElement.textContent = '❌ Failed to open capture tab';
      
      alert('Failed to open capture tab. Please try again.');
    }
  });
}

function stopMultiTabRecording(button, statusElement) {
  console.log('⏹️ Stopping multi-tab recording...');
  
  // Send stop message to helper tab via background script
  if (helperTabId) {
    chrome.runtime.sendMessage({
      type: 'MEETING_TO_HELPER',
      messageType: 'STOP_RECORDING',
      targetTabId: helperTabId
    });
  }
  
  // Reset UI
  button.innerHTML = '▶️ Start Recording';
  button.style.background = '#fff';
  button.style.color = '#333';
  button.disabled = false;
  isRecordingViaHelper = false;
  helperTabId = null;
  
  testBackendConnection(); // Reset status
}

// Listen for messages from helper tab
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'HELPER_TO_MEETING') {
    handleHelperMessage(message.messageType, message.data, sender);
  }
});

function handleHelperMessage(messageType, data, sender) {
  const button = document.getElementById('scrumbot-toggle');
  const statusElement = document.getElementById('connection-status');
  
  console.log('[MultiTab] Helper message:', messageType, data);
  
  switch(messageType) {
    case 'CAPTURE_STARTED':
      if (data.success) {
        // Recording started successfully
        isRecordingViaHelper = true;
        button.innerHTML = '⏹️ Stop Enhanced Recording';
        button.style.background = '#ef4444';
        button.style.color = 'white';
        button.disabled = false;
        
        // Get participant count for enhanced status
        const participants = window.meetingDetector?.getParticipants() || [];
        statusElement.textContent = `🔴 Recording (${participants.length} participants)`;
        
        // Update enhanced UI if available
        if (window.scrumBotUI) {
          window.scrumBotUI.updateRecordingState(true, participants.length);
          window.scrumBotUI.updateParticipants(participants);
        }
        
        console.log('✅ Enhanced multi-tab recording started with', participants.length, 'participants');
        createEnhancedMeeting(participants); // Create enhanced meeting record
      }
      break;
      
    case 'CAPTURE_FAILED':
      // Recording failed
      button.innerHTML = '▶️ Start Enhanced Recording';
      button.style.background = '#fff';
      button.style.color = '#333';
      button.disabled = false;
      statusElement.textContent = '❌ Capture failed';
      
      // Update enhanced UI if available
      if (window.scrumBotUI) {
        window.scrumBotUI.updateRecordingState(false, 0);
        window.scrumBotUI.updateConnectionStatus('error', '❌ Capture failed');
      }
      
      console.error('❌ Enhanced multi-tab recording failed:', data.error);
      alert(`Recording failed: ${data.error}\n\nPlease try again and make sure to:\n1. Select your meeting tab\n2. Enable "Also share tab audio"\n3. Click "Share"`);
      break;
      
    case 'CAPTURE_STOPPED':
      // Recording stopped
      isRecordingViaHelper = false;
      helperTabId = null;
      button.innerHTML = '▶️ Start Enhanced Recording';
      button.style.background = '#fff';
      button.style.color = '#333';
      button.disabled = false;
      testBackendConnection();
      
      console.log('✅ Multi-tab recording stopped');
      break;
      
    case 'AUDIO_DATA':
      // Forward audio data to WebSocket server
      console.log('[MultiTab] Audio data received:', data.audioData.length, 'bytes');
      sendAudioViaWebSocket(data.audioData, data.timestamp);
      break;
  }
}

function createMeeting() {
  const meetingData = {
    meeting_title: `${currentPlatform} Meeting - ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}`,
    transcripts: [{
      id: meetingId,
      text: `Meeting started on ${currentPlatform} at ${new Date().toISOString()}`,
      timestamp: new Date().toISOString()
    }]
  };

  apiCall(ENDPOINTS.saveTranscript, {
    method: 'POST',
    body: JSON.stringify(meetingData)
  })
    .then(response => response.json())
    .then(data => {
      console.log('✅ Meeting created:', data);
    })
    .catch(error => {
      console.error('❌ Failed to create meeting:', error);
    });
}

function createEnhancedMeeting(participants) {
  const meetingData = {
    meeting_title: `${currentPlatform} Meeting - ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}`,
    meeting_id: meetingId,
    platform: currentPlatform,
    participants: participants,
    transcripts: [{
      id: meetingId,
      text: `Enhanced meeting started on ${currentPlatform} with ${participants.length} participants at ${new Date().toISOString()}`,
      timestamp: new Date().toISOString()
    }]
  };

  apiCall(ENDPOINTS.saveTranscript, {
    method: 'POST',
    body: JSON.stringify(meetingData)
  })
    .then(response => response.json())
    .then(data => {
      console.log('✅ Enhanced meeting created:', data);
      console.log('👥 Participants:', participants.map(p => p.name).join(', '));
    })
    .catch(error => {
      console.error('❌ Failed to create enhanced meeting:', error);
    });
}

function sendAudioData(transcriptText) {
  const transcriptData = {
    meeting_title: `${currentPlatform} Meeting - ${meetingId}`,
    transcripts: [{
      id: `${meetingId}-${Date.now()}`,
      text: transcriptText,
      timestamp: new Date().toISOString()
    }]
  };

  apiCall(ENDPOINTS.saveTranscript, {
    method: 'POST',
    body: JSON.stringify(transcriptData)
  })
    .then(response => response.json())
    .then(data => {
      console.log('✅ Transcript sent:', data);
    })
    .catch(error => {
      console.error('❌ Failed to send transcript:', error);
    });
}

function openDashboard() {
  window.open(FRONTEND_URL, '_blank');
}

function testAPI() {
  console.log('🧪 Testing API connection...');

  // Test multiple endpoints with ngrok support
  Promise.all([
    apiCall(ENDPOINTS.health),
    apiCall(ENDPOINTS.getMeetings)
  ])
    .then(responses => Promise.all(responses.map(r => r.json())))
    .then(([healthData, meetingsData]) => {
      console.log('✅ API Tests successful:', { healthData, meetingsData });
      alert(`✅ API Test Success!
Backend: ${healthData.status}
Meetings: ${Array.isArray(meetingsData) ? meetingsData.length : 'N/A'} found
URL: ${BACKEND_URL}
🚀 ngrok tunnel working!`);
    })
    .catch(error => {
      console.error('❌ API Test failed:', error);
      alert(`❌ API Test Failed!
Error: ${error.message}
Backend: ${BACKEND_URL}
Check browser console for details.`);
    });
}

function debugComponents() {
  console.log('🔍 Debug Components Status:');
  
  const status = {
    config: !!window.SCRUMBOT_CONFIG,
    meetingDetector: !!window.meetingDetector,
    audioCapture: !!window.scrumBotAudioCapture,
    webSocket: !!window.scrumBotWebSocket,
    controller: !!window.scrumBotController
  };
  
  console.log('Component Status:', status);
  
  if (window.SCRUMBOT_CONFIG) {
    console.log('Config:', {
      environment: window.SCRUMBOT_CONFIG.ENVIRONMENT,
      backend: window.SCRUMBOT_CONFIG.BACKEND_URL,
      websocket: window.SCRUMBOT_CONFIG.WEBSOCKET_URL,
      debug: window.SCRUMBOT_CONFIG.DEBUG
    });
  }
  
  if (window.meetingDetector) {
    console.log('Meeting Detector:', {
      platform: window.meetingDetector.platform,
      isInMeeting: window.meetingDetector.isInMeeting
    });
  }
  
  if (window.scrumBotController) {
    console.log('Controller:', {
      isRecording: window.scrumBotController.isRecording,
      hasDetector: !!window.scrumBotController.detector,
      hasAudioCapture: !!window.scrumBotController.audioCapture
    });
  }
  
  // Test audio capture directly
  if (window.scrumBotAudioCapture) {
    console.log('Testing audio capture directly...');
    window.scrumBotAudioCapture.startCapture().then(success => {
      console.log('Direct audio capture test:', success ? '✅ Success' : '❌ Failed');
      if (success) {
        setTimeout(() => {
          window.scrumBotAudioCapture.stopCapture();
          console.log('Direct audio capture stopped');
        }, 3000);
      }
    });
  }
  
  alert('Debug info logged to console. Check the console for details.');
}



// WebSocket connection for real-time communication
let websocket = null;
let isShuttingDown = false; // Flag to prevent reconnection during shutdown

function initializeWebSocket() {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    return;
  }
  
  const wsUrl = config.WEBSOCKET_URL;
  console.log('🔌 Connecting to WebSocket:', wsUrl);
  
  websocket = new WebSocket(wsUrl);
  
  websocket.onopen = () => {
    console.log('✅ WebSocket connected');
    // Wait for connection to be fully ready before sending
    setTimeout(() => {
      if (websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({
          type: 'HANDSHAKE',
          clientType: 'chrome_extension',
          platform: currentPlatform,
          meetingUrl: window.location.href
        }));
      }
    }, 100);
  };
  
  websocket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      console.log('📨 WebSocket message:', data);
      
      // Handle different message types
      if (data.type === 'transcription_result' || data.type === 'TRANSCRIPTION_RESULT') {
        const transcriptText = data.data?.text || data.text || 'EMPTY';
        console.log('📝 Transcription text:', transcriptText);
        
        // Add to transcript log for download
        addToTranscriptLog(transcriptText, data.data?.timestamp || new Date().toISOString());
        
        handleTranscriptionUpdate(data);
      } else if (data.type === 'meeting_processed') {
        handleMeetingProcessed(data);
      } else if (data.type === 'PROCESSING_STATUS') {
        handleProcessingStatus(data);
      } else if (data.type === 'PROCESSING_COMPLETE') {
        handleProcessingComplete(data);
      }
    } catch (error) {
      console.error('❌ WebSocket message parse error:', error);
    }
  };
  
  websocket.onerror = (error) => {
    console.error('❌ WebSocket error:', error);
  };
  
  websocket.onclose = () => {
    console.log('🔌 WebSocket disconnected');
    // Only reconnect if not shutting down
    if (!isShuttingDown) {
      setTimeout(initializeWebSocket, 5000);
    } else {
      console.log('🚫 Skipping reconnect - recording stopped');
    }
  };
}

let wsRetryCount = 0;
const MAX_WS_RETRIES = 5;

function sendAudioViaWebSocket(audioData, timestamp) {
  if (!websocket || websocket.readyState !== WebSocket.OPEN) {
    if (wsRetryCount >= MAX_WS_RETRIES) {
      console.log('[Content] WebSocket max retries reached, dropping audio chunk');
      return;
    }
    
    console.log(`[Content] WebSocket not connected, retry ${wsRetryCount + 1}/${MAX_WS_RETRIES}`);
    wsRetryCount++;
    initializeWebSocket();
    
    // Only retry if we're still recording
    if (isRecordingViaHelper) {
      setTimeout(() => sendAudioViaWebSocket(audioData, timestamp), 2000);
    }
    return;
  }
  
  // Reset retry count on successful connection
  wsRetryCount = 0;
  
  const participants = window.meetingDetector?.getParticipants() || [];
  const message = {
    type: 'AUDIO_CHUNK_ENHANCED',
    data: audioData,
    timestamp: timestamp,
    platform: currentPlatform,
    meetingUrl: window.location.href,
    participants: participants,
    participant_count: participants.length,
    metadata: {
      chunk_size: audioData.length,
      sample_rate: 16000,
      channels: 1,
      format: 'webm'
    }
  };
  
  websocket.send(JSON.stringify(message));
  console.log('[Content] Audio chunk sent via WebSocket:', audioData.length, 'bytes');
}

function sendMeetingEndSignal() {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    const participants = window.meetingDetector?.getParticipants() || [];
    const message = {
      type: 'MEETING_EVENT',
      eventType: 'ended',
      data: {
        meetingId: meetingId,
        meetingUrl: window.location.href,
        participants: participants,
        platform: currentPlatform,
        timestamp: new Date().toISOString()
      }
    };
    
    websocket.send(JSON.stringify(message));
    console.log('🔄 Meeting end signal sent via WebSocket from content script');
  } else {
    console.log('⚠️ WebSocket not connected, cannot send meeting end signal');
  }
}

function handleTranscriptionUpdate(data) {
  // Update UI with new transcription
  if (window.scrumBotUI) {
    window.scrumBotUI.addTranscript(data.data);
  }
}

function handleMeetingProcessed(data) {
  console.log('✅ Meeting processed:', data);
  // Update UI with processing results
  if (window.scrumBotUI) {
    window.scrumBotUI.updateMeetingAnalysis(data.analysis);
  }
}

let processingTimeoutId = null;
const PROCESSING_TIMEOUT_MS = 30000; // 30 seconds

function startProcessingTimeout() {
  console.log('⏱️ Starting processing timeout (30s)');
  
  processingTimeoutId = setTimeout(() => {
    console.log('⏰ Processing timeout reached - completing stop');
    handleProcessingComplete({ timeout: true });
  }, PROCESSING_TIMEOUT_MS);
}

function resetProcessingTimeout() {
  if (processingTimeoutId) {
    clearTimeout(processingTimeoutId);
    processingTimeoutId = setTimeout(() => {
      console.log('⏰ Processing timeout reached - completing stop');
      handleProcessingComplete({ timeout: true });
    }, PROCESSING_TIMEOUT_MS);
  }
}

function handleProcessingStatus(data) {
  console.log('🔄 Processing status:', data.data?.message || 'Processing...');
  
  // Reset timeout on each status update
  resetProcessingTimeout();
  
  // Update UI with current status
  const statusElement = document.getElementById('connection-status');
  if (statusElement) {
    statusElement.textContent = `🔄 ${data.data?.message || 'Processing audio...'}` ;
  }
}

function handleProcessingComplete(data) {
  console.log('✅ Processing complete:', data);
  
  // Clear timeout
  if (processingTimeoutId) {
    clearTimeout(processingTimeoutId);
    processingTimeoutId = null;
  }
  
  // Auto-download transcript if we have data
  if (transcriptLog.length > 0) {
    console.log(`📝 Auto-downloading transcript with ${transcriptLog.length} segments`);
    downloadTranscript();
  }
  
  // Complete the recording stop
  completeRecordingStop();
}

// Initialize WebSocket when content script loads
if (currentPlatform) {
  initializeWebSocket();
}

function addToTranscriptLog(text, timestamp) {
  if (text && text !== 'EMPTY' && text.trim().length > 0) {
    transcriptLog.push({
      timestamp: timestamp,
      text: text.trim(),
      meetingId: meetingId
    });
    
    // Update transcript count in UI
    const countElement = document.getElementById('transcript-count');
    if (countElement) {
      countElement.textContent = transcriptLog.length;
    }
    
    console.log(`📝 Added to transcript log (${transcriptLog.length} total):`, text);
  }
}

function downloadTranscript() {
  if (transcriptLog.length === 0) {
    alert('No transcript data available to download.');
    return;
  }
  
  // Create transcript content
  const header = `ScrumBot Transcript Validation\nMeeting ID: ${meetingId}\nPlatform: ${currentPlatform}\nGenerated: ${new Date().toISOString()}\nTotal Segments: ${transcriptLog.length}\n\n${'='.repeat(50)}\n\n`;
  
  const transcriptContent = transcriptLog.map((entry, index) => {
    const time = new Date(entry.timestamp).toLocaleTimeString();
    return `[${index + 1}] ${time}\n${entry.text}\n`;
  }).join('\n');
  
  const fullContent = header + transcriptContent;
  
  // Create and download transcript file
  const blob = new Blob([fullContent], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `scrumbot-transcript-${meetingId}-${new Date().toISOString().split('T')[0]}.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  
  console.log(`💾 Downloaded transcript with ${transcriptLog.length} segments`);
  
  // Also trigger audio file download if available
  if (window.scrumBotAudioCapture && window.scrumBotAudioCapture.recordedPCMData && window.scrumBotAudioCapture.recordedPCMData.length > 0) {
    console.log('📥 Generating enhanced audio file download...');
    const audioFilename = window.scrumBotAudioCapture.generateWAVFile();
    alert(`✅ Files downloaded!\n• Transcript: ${transcriptLog.length} segments\n• Audio: ${audioFilename}\n\nBoth files saved for validation.`);
  } else {
    console.log('⚠️ No enhanced audio data available - checking helper tab audio...');
    // Try to get audio from helper tab if available
    if (helperTabId) {
      chrome.runtime.sendMessage({
        type: 'MEETING_TO_HELPER',
        messageType: 'DOWNLOAD_AUDIO',
        targetTabId: helperTabId
      });
    }
    alert(`✅ Transcript downloaded!\n${transcriptLog.length} segments saved for validation.\n\n⚠️ Audio file may be available from capture tab.`);
  }
}

// Auto-refresh connection status
setInterval(() => {
  if (window.scrumBotController && !window.scrumBotController.isRecording) {
    testBackendConnection();
  }
}, 30000);

