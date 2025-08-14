class MeetingDetector {
  constructor() {
    this.isInMeeting = false;
    this.platform = this.detectPlatform();
    this.participants = new Map();
    this.isMonitoringParticipants = false;
    this.participantObservers = [];
    this.debugMode = false; // Set to true to enable DOM logging to files
    this.init();
  }

  detectPlatform() {
    const url = window.location.href;
    if (url.includes('meet.google.com')) return 'google-meet';
    if (url.includes('zoom.us')) return 'zoom';
    if (url.includes('teams.microsoft.com')) return 'teams';
    return 'unknown';
  }

  init() {
    console.log(`[ScrumBot] Detected platform: ${this.platform}`);
    this.checkMeetingStatus();

    // Monitor for meeting state changes
    setInterval(() => this.checkMeetingStatus(), 2000);
  }

  checkMeetingStatus() {
    let inMeeting = false;

    switch (this.platform) {
      case 'google-meet':
        inMeeting = this.isInGoogleMeet();
        break;
      case 'zoom':
        inMeeting = this.isInZoom();
        break;
      case 'teams':
        inMeeting = this.isInTeams();
        break;
    }

    if (inMeeting !== this.isInMeeting) {
      this.isInMeeting = inMeeting;
      this.notifyMeetingStateChange();
    }
  }

  isInGoogleMeet() {
    // Check for Google Meet indicators
    return document.querySelector('[data-call-id]') !== null ||
      document.querySelector('[jsname="HlFzId"]') !== null;
  }

  isInZoom() {
    // Check for Zoom indicators  
    return document.querySelector('#zoom-ui-frame') !== null ||
      document.querySelector('.zm-video-container') !== null;
  }

  isInTeams() {
    // Check for Teams indicators
    return document.querySelector('[data-tid="call-roster"]') !== null ||
      document.querySelector('.ts-calling-screen') !== null;
  }

  notifyMeetingStateChange() {
    console.log(`[ScrumBot] Meeting state changed: ${this.isInMeeting}`);

    // Start/stop participant monitoring based on meeting state
    if (this.isInMeeting && !this.isMonitoringParticipants) {
      this.startParticipantMonitoring();
    } else if (!this.isInMeeting && this.isMonitoringParticipants) {
      this.stopParticipantMonitoring();
    }

    // Send message to popup/background
    chrome.runtime.sendMessage({
      type: 'MEETING_STATE_CHANGE',
      isInMeeting: this.isInMeeting,
      platform: this.platform,
      url: window.location.href,
      participants: Array.from(this.participants.values())
    });
  }

  // Participant Detection Methods
  async startParticipantMonitoring() {
    if (this.isMonitoringParticipants) return;

    this.isMonitoringParticipants = true;
    console.log('👥 Starting participant monitoring for', this.platform);

    // Initial participant extraction
    await this.extractParticipants();

    // Set up continuous monitoring
    this.setupParticipantObservers();

    // Periodic refresh every 3 seconds for more responsive detection
    this.participantInterval = setInterval(() => {
      this.extractParticipants();
    }, 3000);
  }

  stopParticipantMonitoring() {
    this.isMonitoringParticipants = false;

    // Clear observers
    this.participantObservers.forEach(observer => observer.disconnect());
    this.participantObservers = [];

    // Clear interval
    if (this.participantInterval) {
      clearInterval(this.participantInterval);
    }

    console.log('⏹️ Participant monitoring stopped');
  }

  async extractParticipants() {
    let participants = [];

    try {
      switch (this.platform) {
        case 'google-meet':
          participants = await this.extractGoogleMeetParticipants();
          break;
        case 'zoom':
          participants = await this.extractZoomParticipants();
          break;
        case 'teams':
          participants = await this.extractTeamsParticipants();
          break;
        default:
          console.warn('❌ Unsupported platform for participant detection');
          return [];
      }

      // Update participant list and detect changes
      this.updateParticipantList(participants);

    } catch (error) {
      console.error('❌ Error extracting participants:', error);
    }

    return Array.from(this.participants.values());
  }

  async extractGoogleMeetParticipants() {
    const participants = [];
    
    // Primary method: Use data-participant-id (most accurate and responsive)
    const participantElements = document.querySelectorAll('[data-participant-id]');
    const uniqueParticipants = new Set();
    
    participantElements.forEach(element => {
      const participantId = element.getAttribute('data-participant-id');
      const textContent = element.textContent || '';
      
      // Skip temporary join notification elements
      if (textContent.includes(' joined') && element.className === '') {
        return;
      }
      
      // Only process elements with the main participant class (oZRSLe) to avoid duplicates
      if (participantId && !uniqueParticipants.has(participantId) && 
          element.className.includes('oZRSLe')) {
        uniqueParticipants.add(participantId);
        
        // Check if this is the host (usually has UI controls)
        const isHost = textContent.includes('frame_person') || 
                      textContent.includes('visual_effects') ||
                      textContent.includes('Backgrounds');
        
        let name = 'Unknown Participant';
        if (isHost) {
          name = 'Host (You)';
        } else if (textContent && !textContent.includes('joined')) {
          // Extract actual name - handle duplicated names and clean up
          let cleanName = textContent
            .replace(/devices?/gi, '')  // Remove "devices"
            .replace(/\s+/g, ' ')       // Normalize whitespace
            .trim();
          
          // Handle duplicated names like "Christian OnyisiChristian Onyisi"
          // First try to find a pattern where the name is repeated
          const namePattern = /^(.+?)\1/;
          const match = cleanName.match(namePattern);
          
          if (match) {
            // If we found a repeated pattern, use just the first occurrence
            cleanName = match[1].trim();
          } else {
            // Fallback: remove duplicate consecutive words
            const words = cleanName.split(' ');
            const uniqueWords = [];
            let lastWord = '';
            
            for (const word of words) {
              if (word.toLowerCase() !== lastWord.toLowerCase() && word.length > 0) {
                uniqueWords.push(word);
                lastWord = word;
              }
            }
            
            cleanName = uniqueWords.join(' ');
          }
          
          if (cleanName && cleanName.length > 0 && cleanName.length < 50) {
            name = cleanName;
          }
        }
        
        participants.push({
          id: participantId,
          name: name,
          platform_id: participantId,
          status: 'active',
          join_time: new Date().toISOString(),
          is_host: isHost
        });
      }
    });

    // Fallback: If no participants detected but we're in a meeting, add host
    if (participants.length === 0) {
      const inMeeting = this.isInGoogleMeet();
      if (inMeeting) {
        participants.push({
          id: 'gmeet-host',
          name: 'Host (You)',
          platform_id: 'gmeet-host',
          status: 'active',
          join_time: new Date().toISOString(),
          is_host: true
        });
      }
    }

    console.log('👥 Google Meet participants found:', participants.length);
    if (participants.length > 0) {
      console.log('👤 Participant details:', participants.map(p => `${p.name} (${p.is_host ? 'Host' : 'Guest'})`));
    }

    // Debug logging to help understand DOM structure (only if debug mode is enabled)
    if (this.debugMode) {
      this.logDOMStructure(participants.length);
    }

    return participants;
  }

  async extractZoomParticipants() {
    const participants = [];

    // Method 1: Participant panel
    const participantList = document.querySelector('.participants-ul');
    if (participantList) {
      const items = participantList.querySelectorAll('.participants-li');
      items.forEach((item, index) => {
        const nameElement = item.querySelector('.participants-li__display-name');
        const name = nameElement?.textContent?.trim();

        if (name) {
          participants.push({
            id: `zoom-${index}`,
            name: name,
            platform_id: `zoom-${index}`,
            status: 'active',
            join_time: new Date().toISOString()
          });
        }
      });
    }

    // Method 2: Video gallery
    if (participants.length === 0) {
      const videoItems = document.querySelectorAll('.video-item');
      videoItems.forEach((item, index) => {
        const nameElement = item.querySelector('.video-item__name');
        const name = nameElement?.textContent?.trim();

        if (name) {
          // Convert "You" to actual user name or "Host" for better identification
          const participantName = name === 'You' ? 'Host (You)' : name;
          participants.push({
            id: `zoom-${index}`,
            name: participantName,
            platform_id: `zoom-${index}`,
            status: 'active',
            join_time: new Date().toISOString(),
            is_host: name === 'You'  // Flag to identify the host
          });
        }
      });
    }

    console.log('👥 Zoom participants found:', participants.length);
    return participants;
  }

  async extractTeamsParticipants() {
    const participants = [];

    // Method 1: Roster panel
    const rosterItems = document.querySelectorAll('[data-tid="roster-participant"]');
    rosterItems.forEach((item, index) => {
      const nameElement = item.querySelector('.participant-name');
      const name = nameElement?.textContent?.trim();

      if (name) {
        participants.push({
          id: `teams-${index}`,
          name: name,
          platform_id: `teams-${index}`,
          status: 'active',
          join_time: new Date().toISOString()
        });
      }
    });

    // Method 2: Video tiles
    if (participants.length === 0) {
      const videoTiles = document.querySelectorAll('[data-tid="video-tile"]');
      videoTiles.forEach((tile, index) => {
        const nameElement = tile.querySelector('.displayname');
        const name = nameElement?.textContent?.trim();

        if (name && name !== 'You') {
          participants.push({
            id: `teams-${index}`,
            name: name,
            platform_id: `teams-${index}`,
            status: 'active',
            join_time: new Date().toISOString()
          });
        }
      });
    }

    console.log('👥 Teams participants found:', participants.length);
    return participants;
  }

  extractNameFromGoogleMeetItem(item) {
    // Try multiple selectors for name extraction
    const selectors = [
      '.participant-name',
      '[data-self-name]',
      '[aria-label]',
      '.name-text'
    ];

    for (const selector of selectors) {
      const element = item.querySelector(selector);
      if (element) {
        const name = element.textContent?.trim() || element.getAttribute('aria-label');
        if (name && name !== 'You') {
          return name;
        }
      }
    }

    return null;
  }

  updateParticipantList(newParticipants) {
    const previousCount = this.participants.size;

    // Clear existing participants
    this.participants.clear();

    // Add new participants
    newParticipants.forEach(participant => {
      this.participants.set(participant.id, participant);
    });

    const currentCount = this.participants.size;

    // Log changes
    if (currentCount !== previousCount) {
      console.log(`👥 Participant count changed: ${previousCount} → ${currentCount}`);
      console.log('👤 Current participants:', Array.from(this.participants.values()).map(p => `${p.name} (${p.is_host ? 'Host' : 'Guest'})`));

      // Notify listeners of participant changes
      this.notifyParticipantChange({
        type: 'participant_count_changed',
        previous_count: previousCount,
        current_count: currentCount,
        participants: Array.from(this.participants.values())
      });
    }
  }

  setupParticipantObservers() {
    // Set up DOM observers for dynamic participant changes
    const observer = new MutationObserver((mutations) => {
      let shouldUpdate = false;

      mutations.forEach(mutation => {
        // Check for participant-related changes
        if (mutation.type === 'childList') {
          // Check if nodes with data-participant-id were added or removed
          const addedNodes = Array.from(mutation.addedNodes);
          const removedNodes = Array.from(mutation.removedNodes);
          
          const hasParticipantChanges = [...addedNodes, ...removedNodes].some(node => {
            return node.nodeType === Node.ELEMENT_NODE && (
              node.hasAttribute?.('data-participant-id') ||
              node.querySelector?.('[data-participant-id]')
            );
          });
          
          if (hasParticipantChanges) {
            shouldUpdate = true;
          }
        }
        
        // Check for attribute changes on participant elements
        if (mutation.type === 'attributes' && 
            mutation.attributeName === 'data-participant-id') {
          shouldUpdate = true;
        }
      });

      if (shouldUpdate) {
        console.log('🔄 Participant DOM change detected, updating...');
        // Small delay to let DOM settle
        setTimeout(() => this.extractParticipants(), 100);
      }
    });

    // Observe the entire document for participant changes
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['data-participant-id']
    });

    this.participantObservers.push(observer);
  }

  notifyParticipantChange(event) {
    // Send participant change event to content script
    window.dispatchEvent(new CustomEvent('scrumbot-participant-change', {
      detail: event
    }));

    // Also send to background script
    chrome.runtime.sendMessage({
      type: 'PARTICIPANT_CHANGE',
      ...event
    });
  }

  getParticipants() {
    return Array.from(this.participants.values());
  }

  getParticipantCount() {
    return this.participants.size;
  }

  logDOMStructure(participantCount) {
    const timestamp = new Date().toISOString();
    let logContent = `\n🔍 DOM Structure Analysis - ${timestamp}\n`;
    logContent += '========================\n';
    
    // Log all potential participant-related elements
    const selectors = [
      '[data-participant-id]',
      '[data-self-name]',
      '[data-participant-name]',
      '[jsname]',
      'video',
      '[data-allocation-index]',
      '[aria-label*="frame_person"]',
      '[data-self-name="frame_person"]',
      '[aria-label*="person"]',
      '.participant-name',
      '.name'
    ];
    
    selectors.forEach(selector => {
      const elements = document.querySelectorAll(selector);
      if (elements.length > 0) {
        logContent += `🔍 ${selector}: ${elements.length} elements\n`;
        elements.forEach((el, index) => {
          if (index < 3) { // Log first 3 elements to avoid spam
            const info = {
              tagName: el.tagName,
              id: el.id,
              className: el.className,
              'data-participant-id': el.getAttribute('data-participant-id'),
              'data-self-name': el.getAttribute('data-self-name'),
              'data-participant-name': el.getAttribute('data-participant-name'),
              'aria-label': el.getAttribute('aria-label'),
              textContent: el.textContent?.trim().substring(0, 50)
            };
            logContent += `  [${index}]: ${JSON.stringify(info, null, 2)}\n`;
          }
        });
      }
    });
    
    // Log video elements specifically
    const videos = document.querySelectorAll('video');
    logContent += `🎥 Video elements: ${videos.length}\n`;
    videos.forEach((video, index) => {
      if (index < 3) {
        const parent = video.closest('[data-participant-id], [jsname], [data-allocation-index]');
        const videoInfo = {
          src: video.src?.substring(0, 50),
          parentInfo: parent ? {
            tagName: parent.tagName,
            'data-participant-id': parent.getAttribute('data-participant-id'),
            'jsname': parent.getAttribute('jsname'),
            'data-allocation-index': parent.getAttribute('data-allocation-index')
          } : 'No relevant parent'
        };
        logContent += `  Video[${index}]: ${JSON.stringify(videoInfo, null, 2)}\n`;
      }
    });
    
    // Log meeting state
    const inMeeting = this.isInGoogleMeet();
    logContent += `📞 In meeting: ${inMeeting}\n`;
    logContent += `👥 Final participant count: ${participantCount}\n`;
    logContent += '========================\n';
    
    // Also log to console
    console.log(logContent);
    
    // Write to file
    this.writeDOMLogToFile(logContent);
  }

  writeDOMLogToFile(content) {
    if (!this.debugMode) {
      return; // Skip file writing if debug mode is disabled
    }
    
    try {
      // Create or append to the log file
      const blob = new Blob([content], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      
      // Create download link
      const a = document.createElement('a');
      a.href = url;
      a.download = `google-meet-dom-analysis-${Date.now()}.txt`;
      
      // Auto-download the file
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      console.log('📁 DOM analysis saved to file');
    } catch (error) {
      console.error('❌ Failed to save DOM analysis:', error);
    }
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Initialize detector
window.meetingDetector = new MeetingDetector();

// Add a manual test function for debugging
window.testParticipantDetection = function() {
  console.log('🧪 Manual participant detection test...');
  if (window.meetingDetector) {
    window.meetingDetector.extractParticipants().then(participants => {
      console.log('🧪 Test result:', participants);
    });
  } else {
    console.log('❌ Meeting detector not initialized');
  }
};

// Add a manual function to capture DOM analysis
window.captureDOMAnalysis = function() {
  console.log('📁 Capturing DOM analysis...');
  if (window.meetingDetector) {
    const wasDebugMode = window.meetingDetector.debugMode;
    window.meetingDetector.debugMode = true; // Temporarily enable debug mode
    window.meetingDetector.logDOMStructure(0); // This will trigger file download
    window.meetingDetector.debugMode = wasDebugMode; // Restore previous state
  } else {
    console.log('❌ Meeting detector not initialized');
  }
};

// Add functions to control debug mode
window.enableDOMDebug = function() {
  if (window.meetingDetector) {
    window.meetingDetector.debugMode = true;
    console.log('🐛 DOM debug mode enabled - logs will be saved to files');
  } else {
    console.log('❌ Meeting detector not initialized');
  }
};

window.disableDOMDebug = function() {
  if (window.meetingDetector) {
    window.meetingDetector.debugMode = false;
    console.log('🔇 DOM debug mode disabled - logs will only show in console');
  } else {
    console.log('❌ Meeting detector not initialized');
  }
};

