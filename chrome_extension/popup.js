// popup.js - Extension popup controller with ngrok backend support
class PopupController {
  constructor() {
    this.isInMeeting = false;
    this.isRecording = false;
    this.isConnected = false;
    this.platform = 'unknown';
    this.startTime = null;
    this.durationInterval = null;

    this.initializeElements();
    this.setupEventListeners();
    this.updateStatus();
  }

  initializeElements() {
    this.statusEl = document.getElementById('status');
    this.startBtn = document.getElementById('startBtn');
    this.stopBtn = document.getElementById('stopBtn');
    this.dashboardBtn = document.getElementById('dashboard-btn');
    this.testBtn = document.getElementById('test-btn');
  }

  setupEventListeners() {
    this.startBtn.addEventListener('click', () => this.startRecording());
    this.stopBtn.addEventListener('click', () => this.stopRecording());
    this.dashboardBtn.addEventListener('click', () => this.openDashboard());
    this.testBtn.addEventListener('click', () => this.testConnection());

    // Listen for status updates from content script
    chrome.runtime.onMessage.addListener((message) => {
      this.handleMessage(message);
    });
  }

  async updateStatus() {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      chrome.tabs.sendMessage(tab.id, { type: 'GET_STATUS' }, (response) => {
        if (response) {
          this.isInMeeting = response.isInMeeting;
          this.isRecording = response.isRecording;
          this.platform = response.platform;
          this.updateUI();
        }
      });

      // Initial connection test
      this.testConnection();
    } catch (error) {
      console.error('[Popup] Error updating status:', error);
    }
  }

  handleMessage(message) {
    switch (message.type) {
      case 'MEETING_STATE_CHANGE':
        this.isInMeeting = message.isInMeeting;
        this.platform = message.platform;
        this.updateUI();
        break;
      case 'RECORDING_STATE_CHANGE':
        this.isRecording = message.isRecording;
        if (this.isRecording) {
          this.startTime = Date.now();
          this.startDurationTimer();
        } else {
          this.stopDurationTimer();
        }
        this.updateUI();
        break;
    }
  }

  updateUI() {
    if (this.isRecording) {
      this.statusEl.textContent = '🔴 Recording in progress';
      this.statusEl.className = 'status recording';
    } else if (this.isInMeeting) {
      this.statusEl.textContent = '📹 In meeting - Ready to record';
      this.statusEl.className = 'status meeting';
    } else if (this.isConnected) {
      this.statusEl.textContent = '🟢 Backend Connected (ngrok)';
      this.statusEl.className = 'status connected';
    } else {
      this.statusEl.textContent = '🔴 Checking connection...';
      this.statusEl.className = 'status disconnected';
    }

    this.startBtn.disabled = !this.isInMeeting || this.isRecording;
    this.stopBtn.disabled = !this.isRecording;
    this.dashboardBtn.disabled = !window.SCRUMBOT_CONFIG;
    this.testBtn.disabled = false; // Always enable test button
  }

  async startRecording() {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      chrome.tabs.sendMessage(tab.id, { type: 'START_RECORDING' });
    } catch (error) {
      console.error('[Popup] Error starting recording:', error);
    }
  }

  async stopRecording() {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      chrome.tabs.sendMessage(tab.id, { type: 'STOP_RECORDING' });
    } catch (error) {
      console.error('[Popup] Error stopping recording:', error);
    }
  }

  startDurationTimer() {
    this.durationInterval = setInterval(() => {
      if (this.startTime) {
        const elapsed = Date.now() - this.startTime;
        const minutes = Math.floor(elapsed / 60000);
        const seconds = Math.floor((elapsed % 60000) / 1000);
        this.statusEl.textContent = `🔴 Recording: ${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
      }
    }, 1000);
  }

  stopDurationTimer() {
    if (this.durationInterval) {
      clearInterval(this.durationInterval);
      this.durationInterval = null;
    }
    this.updateUI(); // Revert to meeting or disconnected state
  }

  testConnection() {
    const statusDiv = this.statusEl;
    statusDiv.textContent = '🔄 Testing...';
    statusDiv.className = 'status disconnected';

    if (!window.SCRUMBOT_CONFIG) {
      statusDiv.textContent = '🔴 Config Error';
      return;
    }

    fetch(`${window.SCRUMBOT_CONFIG.BACKEND_URL}/health`, {
      headers: {
        'ngrok-skip-browser-warning': 'true',
        'Content-Type': 'application/json'
      }
    })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        this.isConnected = data.status === 'healthy';
        this.updateUI();
      })
      .catch(error => {
        console.error('Connection test failed:', error);
        this.isConnected = false;
        statusDiv.textContent = '🔴 Backend Offline';
      });
  }

  openDashboard() {
    if (window.SCRUMBOT_CONFIG) {
      chrome.tabs.create({ url: window.SCRUMBOT_CONFIG.FRONTEND_URL });
    } else {
      console.error('Config not loaded');
    }
  }
}

// Initialize popup when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new PopupController();
});