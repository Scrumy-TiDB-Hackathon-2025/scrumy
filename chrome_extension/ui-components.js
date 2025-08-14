/**
 * UI Components for ScrumBot Core Features
 * Displays participants, speaker attribution, and tasks
 */

class ScrumBotUI {
  constructor() {
    this.participants = [];
    this.transcripts = [];
    this.tasks = [];
    this.meetingSummary = null;
    this.isExpanded = false;
  }

  createEnhancedUI(meetingId) {
    // Remove existing panel if it exists
    const existingPanel = document.getElementById('scrumbot-panel');
    if (existingPanel) {
      existingPanel.remove();
    }

    // Create main panel
    const scrumBotPanel = document.createElement('div');
    scrumBotPanel.id = 'scrumbot-panel';
    scrumBotPanel.innerHTML = this.getMainPanelHTML(meetingId);

    document.body.appendChild(scrumBotPanel);
    this.attachEventListeners();
    
    return scrumBotPanel;
  }

  getMainPanelHTML(meetingId) {
    return `
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
        min-width: 320px;
        max-width: 400px;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
      ">
        <!-- Header -->
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
            <div style="font-weight: 600; font-size: 14px;">ScrumBot Enhanced</div>
            <div style="font-size: 11px; opacity: 0.8;" id="connection-status">Connecting...</div>
          </div>
          <button id="expand-toggle" style="
            margin-left: auto;
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
          ">${this.isExpanded ? '▼' : '▶'}</button>
        </div>
        
        <!-- Meeting Info -->
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
        
        <!-- Participants Section -->
        <div id="participants-section" style="margin-bottom: 12px; ${this.isExpanded ? '' : 'display: none;'}">
          <div style="font-size: 12px; font-weight: 600; margin-bottom: 8px;">
            👥 Participants (<span id="participant-count">0</span>)
          </div>
          <div id="participant-list" style="
            max-height: 120px;
            overflow-y: auto;
            background: rgba(255,255,255,0.1);
            border-radius: 6px;
            padding: 8px;
          ">
            <div style="font-size: 11px; opacity: 0.7; text-align: center;">
              Detecting participants...
            </div>
          </div>
        </div>
        
        <!-- Transcripts Section -->
        <div id="transcripts-section" style="margin-bottom: 12px; ${this.isExpanded ? '' : 'display: none;'}">
          <div style="font-size: 12px; font-weight: 600; margin-bottom: 8px;">
            📝 Live Transcripts
          </div>
          <div id="transcript-list" style="
            max-height: 150px;
            overflow-y: auto;
            background: rgba(255,255,255,0.1);
            border-radius: 6px;
            padding: 8px;
            font-size: 11px;
          ">
            <div style="opacity: 0.7; text-align: center;">
              Waiting for transcription...
            </div>
          </div>
        </div>
        
        <!-- Tasks Section -->
        <div id="tasks-section" style="margin-bottom: 12px; ${this.isExpanded ? '' : 'display: none;'}">
          <div style="font-size: 12px; font-weight: 600; margin-bottom: 8px;">
            ✅ Action Items (<span id="task-count">0</span>)
          </div>
          <div id="task-list" style="
            max-height: 120px;
            overflow-y: auto;
            background: rgba(255,255,255,0.1);
            border-radius: 6px;
            padding: 8px;
          ">
            <div style="font-size: 11px; opacity: 0.7; text-align: center;">
              No tasks detected yet
            </div>
          </div>
        </div>
        
        <!-- Controls -->
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
          margin-bottom: 8px;
        ">
          ▶️ Start Enhanced Recording
        </button>
        
        <div style="display: flex; gap: 5px;">
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
          ">🧪 Test</button>
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
      </div>
    `;
  }

  attachEventListeners() {
    // Expand/collapse toggle
    document.getElementById('expand-toggle')?.addEventListener('click', () => {
      this.toggleExpanded();
    });
    
    // Main controls (these will be handled by content.js)
    document.getElementById('scrumbot-toggle')?.addEventListener('click', () => {
      window.dispatchEvent(new CustomEvent('scrumbot-toggle-recording'));
    });
    
    document.getElementById('scrumbot-dashboard')?.addEventListener('click', () => {
      window.dispatchEvent(new CustomEvent('scrumbot-open-dashboard'));
    });
    
    document.getElementById('scrumbot-test')?.addEventListener('click', () => {
      window.dispatchEvent(new CustomEvent('scrumbot-test-api'));
    });
    
    document.getElementById('scrumbot-debug')?.addEventListener('click', () => {
      window.dispatchEvent(new CustomEvent('scrumbot-debug'));
    });
  }

  toggleExpanded() {
    this.isExpanded = !this.isExpanded;
    
    const expandButton = document.getElementById('expand-toggle');
    const sections = ['participants-section', 'transcripts-section', 'tasks-section'];
    
    if (expandButton) {
      expandButton.textContent = this.isExpanded ? '▼' : '▶';
    }
    
    sections.forEach(sectionId => {
      const section = document.getElementById(sectionId);
      if (section) {
        section.style.display = this.isExpanded ? 'block' : 'none';
      }
    });
  }

  updateParticipants(participants) {
    this.participants = participants || [];
    
    const countElement = document.getElementById('participant-count');
    const listElement = document.getElementById('participant-list');
    
    if (countElement) {
      countElement.textContent = this.participants.length;
    }
    
    if (listElement) {
      if (this.participants.length === 0) {
        listElement.innerHTML = `
          <div style="font-size: 11px; opacity: 0.7; text-align: center;">
            No participants detected
          </div>
        `;
      } else {
        listElement.innerHTML = this.participants.map(participant => `
          <div style="
            display: flex;
            align-items: center;
            padding: 4px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
          ">
            <div style="
              width: 8px;
              height: 8px;
              background: #4ade80;
              border-radius: 50%;
              margin-right: 8px;
            "></div>
            <div style="flex: 1; font-size: 11px;">
              ${participant.name}
            </div>
            <div style="font-size: 10px; opacity: 0.6;">
              ${participant.status}
            </div>
          </div>
        `).join('');
      }
    }
  }

  addTranscript(transcriptData) {
    this.transcripts.push(transcriptData);
    
    // Keep only last 10 transcripts
    if (this.transcripts.length > 10) {
      this.transcripts = this.transcripts.slice(-10);
    }
    
    const listElement = document.getElementById('transcript-list');
    if (listElement) {
      listElement.innerHTML = this.transcripts.map(transcript => `
        <div style="
          padding: 6px 0;
          border-bottom: 1px solid rgba(255,255,255,0.1);
          font-size: 11px;
        ">
          <div style="display: flex; align-items: center; margin-bottom: 2px;">
            <span style="font-weight: 600; color: #fbbf24;">
              ${transcript.speaker || 'Unknown'}:
            </span>
            <span style="margin-left: auto; font-size: 10px; opacity: 0.6;">
              ${transcript.confidence ? Math.round(transcript.confidence * 100) + '%' : ''}
            </span>
          </div>
          <div style="opacity: 0.9;">
            ${transcript.text}
          </div>
        </div>
      `).join('');
      
      // Auto-scroll to bottom
      listElement.scrollTop = listElement.scrollHeight;
    }
  }

  updateSpeakerAttribution(data) {
    // Update the last transcript with speaker info
    if (this.transcripts.length > 0) {
      const lastTranscript = this.transcripts[this.transcripts.length - 1];
      lastTranscript.speaker = data.speaker_name;
      lastTranscript.speaker_id = data.speaker_id;
      lastTranscript.confidence = data.confidence;
      
      // Refresh the transcript display
      this.addTranscript(lastTranscript);
    }
  }

  updateMeetingAnalysis(data) {
    if (data.action_items) {
      this.tasks = data.action_items;
      
      const countElement = document.getElementById('task-count');
      const listElement = document.getElementById('task-list');
      
      if (countElement) {
        countElement.textContent = this.tasks.length;
      }
      
      if (listElement) {
        if (this.tasks.length === 0) {
          listElement.innerHTML = `
            <div style="font-size: 11px; opacity: 0.7; text-align: center;">
              No tasks detected yet
            </div>
          `;
        } else {
          listElement.innerHTML = this.tasks.map(task => `
            <div style="
              padding: 6px 0;
              border-bottom: 1px solid rgba(255,255,255,0.1);
              font-size: 11px;
            ">
              <div style="font-weight: 600; margin-bottom: 2px;">
                ${task.title}
              </div>
              <div style="display: flex; align-items: center; font-size: 10px; opacity: 0.8;">
                <span>👤 ${task.assignee || 'Unassigned'}</span>
                <span style="margin-left: auto;">
                  📅 ${task.due_date || 'No deadline'}
                </span>
              </div>
              <div style="
                margin-top: 4px;
                padding: 2px 6px;
                background: ${task.priority === 'high' ? '#ef4444' : task.priority === 'medium' ? '#f59e0b' : '#6b7280'};
                border-radius: 4px;
                font-size: 10px;
                display: inline-block;
              ">
                ${task.priority || 'medium'} priority
              </div>
            </div>
          `).join('');
        }
      }
    }
  }

  updateConnectionStatus(status, message) {
    const statusElement = document.getElementById('connection-status');
    if (statusElement) {
      const colors = {
        'connected': '#4ade80',
        'connecting': '#fbbf24', 
        'error': '#f87171',
        'offline': '#6b7280'
      };
      
      statusElement.textContent = message || status;
      statusElement.style.color = colors[status] || '#fbbf24';
    }
  }

  updateRecordingState(isRecording, participantCount = 0) {
    const button = document.getElementById('scrumbot-toggle');
    const statusElement = document.getElementById('connection-status');
    
    if (button) {
      if (isRecording) {
        button.innerHTML = '⏹️ Stop Recording';
        button.style.background = '#ef4444';
        button.style.color = 'white';
      } else {
        button.innerHTML = '▶️ Start Enhanced Recording';
        button.style.background = '#fff';
        button.style.color = '#333';
      }
    }
    
    if (statusElement && isRecording) {
      statusElement.textContent = `🔴 Recording (${participantCount} participants)`;
      statusElement.style.color = '#ef4444';
    }
  }
}

// Make available globally
window.scrumBotUI = new ScrumBotUI();

console.log('✅ ScrumBot Enhanced UI Components loaded');