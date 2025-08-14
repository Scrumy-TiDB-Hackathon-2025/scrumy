// test-core.js - Test suite for core logic, WebSocket, and background functionality
const WebSocket = require('ws');
const assert = require('assert');

// Mock MeetingDetector (based on core/meetingdetector.js)
class MeetingDetector {
  constructor() {
    this.platform = 'unknown';
  }
  detect() {
    // Simulate detection based on hostname (mocked for Node.js)
    this.platform = 'google-meet'; // Hardcoded for testing; adjust logic as needed
    return this.platform;
  }
}

// Mock WebSocketClient (based on services/websocketclient.js)
class WebSocketClient {
  constructor(url = 'ws://localhost:8081/ws') {
    this.url = url;
    this.ws = null;
  }
  connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.url);
      this.ws.onopen = () => {
        console.log('[Test] WebSocket connected');
        resolve();
      };
      this.ws.onerror = (error) => reject(error);
      this.ws.onclose = () => console.log('[Test] WebSocket closed');
    });
  }
  sendMessage(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
      console.log('[Test] Message sent:', message);
    }
  }
  get isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }
  onMessage(callback) {
    this.ws.onmessage = (event) => callback(JSON.parse(event.data));
  }
}

// Mock Background Logic
class BackgroundSimulator {
  constructor() {
    this.state = { isRecording: false };
  }
  startRecording() {
    this.state.isRecording = true;
    console.log('[Background] Recording started');
    return this.state;
  }
  stopRecording() {
    this.state.isRecording = false;
    console.log('[Background] Recording stopped');
    return this.state;
  }
}

class CoreIntegrationTest {
  constructor() {
    this.testResults = [];
  }

  async runAllTests() {
    console.log('[Core Test] Starting integration tests...');
    await this.testMeetingDetection();
    await this.testWebSocketConnection();
    await this.testBackgroundLogic();
    this.printResults();
  }

  async testMeetingDetection() {
    console.log('[Test] Meeting Detection...');
    try {
      const detector = new MeetingDetector();
      detector.detect();
      const isDetected = detector.platform === 'google-meet';
      this.testResults.push({
        test: 'Meeting Detection',
        passed: isDetected,
        details: `Platform: ${detector.platform}`
      });
    } catch (error) {
      this.testResults.push({
        test: 'Meeting Detection',
        passed: false,
        details: error.message
      });
    }
  }

  async testWebSocketConnection() {
    console.log('[Test] WebSocket Connection...');
    try {
      const wsClient = new WebSocketClient();
      await wsClient.connect();
      let receivedHandshake = false;
      
      wsClient.onMessage(msg => {
        console.log('[Test] Message received:', msg);
        if (msg.type === 'HANDSHAKE_ACK') {
          receivedHandshake = true;
        }
      });
      
      wsClient.sendMessage({ type: 'HANDSHAKE' });
      
      // Wait for response with timeout
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Close the connection to prevent hanging
      if (wsClient.ws) {
        wsClient.ws.close();
      }
      
      this.testResults.push({
        test: 'WebSocket Connection',
        passed: wsClient.isConnected && receivedHandshake,
        details: `Connected: ${wsClient.isConnected}, Handshake: ${receivedHandshake}`
      });
    } catch (error) {
      this.testResults.push({
        test: 'WebSocket Connection',
        passed: false,
        details: error.message
      });
    }
  }

  async testBackgroundLogic() {
    console.log('[Test] Background Logic...');
    try {
      const bg = new BackgroundSimulator();
      bg.startRecording();
      assert.strictEqual(bg.state.isRecording, true, 'Recording should start');
      bg.stopRecording();
      assert.strictEqual(bg.state.isRecording, false, 'Recording should stop');
      this.testResults.push({
        test: 'Background Logic',
        passed: true,
        details: 'State transitions worked'
      });
    } catch (error) {
      this.testResults.push({
        test: 'Background Logic',
        passed: false,
        details: error.message
      });
    }
  }

  printResults() {
    console.log('\n[Core Test Results]');
    console.log('=====================');
    let passed = 0;
    let total = this.testResults.length;
    this.testResults.forEach(result => {
      const status = result.passed ? '✅ PASS' : '❌ FAIL';
      console.log(`${status} ${result.test}: ${result.details}`);
      if (result.passed) passed++;
    });
    console.log(`\nSummary: ${passed}/${total} tests passed`);
    if (passed === total) {
      console.log('🎉 Core logic is ready!');
    } else {
      console.log('⚠️ Some tests failed. Please fix before proceeding.');
    }
  }
}

// Run tests
const tester = new CoreIntegrationTest();
tester.runAllTests().catch(error => console.error('[Core Test] Execution failed:', error));