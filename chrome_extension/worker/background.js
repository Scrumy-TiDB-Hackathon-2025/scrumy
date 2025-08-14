// background.js - Extension service worker
console.log('[Background] ScrumBot service worker starting...');

// Import WebSocket client (note: in service worker context, we need to handle this differently)
let webSocketClient = null;

// Setup message handlers
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('[Background] Received message:', message.type);
  handleMessage(message, sender, sendResponse);
  return true; // Keep message channel open for async responses
});

function handleMessage(message, sender, sendResponse) {
  switch(message.type) {
    case 'AUDIO_CHUNK':
      handleAudioChunk(message, sender);
      break;
      
    case 'MEETING_STATE_CHANGE':
      handleMeetingStateChange(message, sender);
      break;
      
    case 'RECORDING_STATE_CHANGE':
      handleRecordingStateChange(message, sender);
      break;

    case 'INIT_WEBSOCKET':
      initializeWebSocket();
      sendResponse({ success: true });
      break;
      
    // Multi-tab capture communication
    case 'HELPER_TO_MEETING':
      handleHelperToMeeting(message, sender);
      break;
      
    case 'MEETING_TO_HELPER':
      handleMeetingToHelper(message, sender);
      break;
      
    // Helper tab creation
    case 'CREATE_HELPER_TAB':
      handleCreateHelperTab(message, sender, sendResponse);
      break;
  }
}

function handleHelperToMeeting(message, sender) {
  console.log('[Background] Helper to meeting:', message.messageType);
  
  // Forward message to the target meeting tab
  if (message.targetTabId) {
    chrome.tabs.sendMessage(parseInt(message.targetTabId), {
      type: 'HELPER_TO_MEETING',
      messageType: message.messageType,
      data: message.data
    });
  } else {
    // Broadcast to all tabs if no specific target
    chrome.tabs.query({}, (tabs) => {
      tabs.forEach(tab => {
        chrome.tabs.sendMessage(tab.id, {
          type: 'HELPER_TO_MEETING',
          messageType: message.messageType,
          data: message.data
        }).catch(() => {
          // Ignore errors for tabs that don't have the extension
        });
      });
    });
  }
}

function handleMeetingToHelper(message, sender) {
  console.log('[Background] Meeting to helper:', message.messageType);
  
  // If specific target tab ID provided, send to that tab
  if (message.targetTabId) {
    chrome.tabs.sendMessage(message.targetTabId, {
      type: 'MEETING_TO_HELPER',
      messageType: message.messageType,
      data: message.data
    }).catch((error) => {
      console.log('[Background] Helper tab already closed:', error.message);
    });
  } else {
    // Otherwise, broadcast to all helper tabs
    chrome.tabs.query({url: chrome.runtime.getURL('capture.html*')}, (tabs) => {
      tabs.forEach(tab => {
        chrome.tabs.sendMessage(tab.id, {
          type: 'MEETING_TO_HELPER',
          messageType: message.messageType,
          data: message.data
        }).catch(() => {
          // Ignore errors for closed tabs
        });
      });
    });
  }
}

function initializeWebSocket() {
  console.log('[Background] Initializing WebSocket connection...');
  
  // For now, we'll handle WebSocket in content script context
  // Service workers have limitations with WebSocket connections
  // We'll use the REST API as primary method and WebSocket as enhancement
}

function handleAudioChunk(message, sender) {
  console.log('[Background] Processing audio chunk:', message.data.length, 'bytes');
  
  // Forward to REST API (more reliable than WebSocket in service worker)
  forwardToRestAPI(message, sender);
}

function handleMeetingStateChange(message, sender) {
  console.log('[Background] Meeting state changed:', message.isInMeeting);
  
  // Store meeting state
  chrome.storage.local.set({
    [`meeting_${sender.tab.id}`]: {
      isInMeeting: message.isInMeeting,
      platform: message.platform,
      url: message.url,
      timestamp: Date.now()
    }
  });
}

function handleRecordingStateChange(message, sender) {
  console.log('[Background] Recording state changed:', message.isRecording);
  
  // Store recording state
  chrome.storage.local.set({
    [`recording_${sender.tab.id}`]: {
      isRecording: message.isRecording,
      timestamp: Date.now()
    }
  });
}

function handleCreateHelperTab(message, sender, sendResponse) {
  console.log('[Background] Creating helper tab for meeting tab:', sender.tab.id);
  
  // Check if this is enhanced mode
  const isEnhanced = message.enhancedMode;
  const participants = message.participants || [];
  const meetingId = message.meetingId;
  
  if (isEnhanced) {
    console.log('[Background] Enhanced mode - participants:', participants.length);
  }
  
  try {
    // Create the capture URL with meeting tab ID and enhanced parameters
    let captureUrl = chrome.runtime.getURL('capture.html') + `?meetingTabId=${sender.tab.id}`;
    
    if (isEnhanced) {
      captureUrl += `&enhanced=true&meetingId=${meetingId}&participantCount=${participants.length}`;
    }
    
    // Create the helper tab
    chrome.tabs.create({
      url: captureUrl,
      active: true // Make it the active tab so user sees it
    }, (tab) => {
      if (chrome.runtime.lastError) {
        console.error('[Background] Error creating helper tab:', chrome.runtime.lastError);
        sendResponse({ 
          success: false, 
          error: chrome.runtime.lastError.message 
        });
      } else {
        console.log('[Background] Helper tab created successfully:', tab.id);
        console.log('[Background] Enhanced mode:', isEnhanced);
        sendResponse({ 
          success: true, 
          tabId: tab.id,
          enhanced: isEnhanced
        });
      }
    });
    
  } catch (error) {
    console.error('[Background] Exception creating helper tab:', error);
    sendResponse({ 
      success: false, 
      error: error.message 
    });
  }
}

function forwardToRestAPI(message, sender) {
  // This will be handled by the content script's audio capture
  // Service worker limitations make direct API calls complex
  console.log('[Background] Audio chunk forwarded to content script for REST API processing');
}