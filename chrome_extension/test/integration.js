// test-integration.js - Test script for Epic A (Updated for Multi-Tab Architecture)
class EpicAIntegrationTest {
  constructor() {
    this.testResults = [];
  }

  async runAllTests() {
    console.log('[Epic A Test] Starting integration tests...');

    await this.testMeetingDetection();
    await this.testAudioCapture();
    await this.testWebSocketConnection();
    await this.testMultiTabCapture();
    await this.testExtensionUI();
    await this.testBackendIntegration();

    this.printResults();
  }

  async testMeetingDetection() {
    console.log('[Test] Meeting Detection...');

    // Test Google Meet detection
    const detector = new MeetingDetector();
    const isDetected = detector.platform === 'google-meet';

    this.testResults.push({
      test: 'Meeting Detection',
      passed: isDetected,
      details: `Platform: ${detector.platform}`
    });
  }

  async testAudioCapture() {
    console.log('[Test] Audio Capture...');

    try {
      const audioCapture = new AudioCapture();
      const canCapture = typeof audioCapture.startCapture === 'function';

      this.testResults.push({
        test: 'Audio Capture',
        passed: canCapture,
        details: 'Audio capture methods available'
      });
    } catch (error) {
      this.testResults.push({
        test: 'Audio Capture',
        passed: false,
        details: error.message
      });
    }
  }

  async testWebSocketConnection() {
    console.log('[Test] WebSocket Connection...');

    try {
      const wsClient = new WebSocketClient();
      wsClient.connect();

      // Wait for connection
      await new Promise(resolve => setTimeout(resolve, 2000));

      this.testResults.push({
        test: 'WebSocket Connection',
        passed: wsClient.isConnected,
        details: `Connected: ${wsClient.isConnected}`
      });
    } catch (error) {
      this.testResults.push({
        test: 'WebSocket Connection',
        passed: false,
        details: error.message
      });
    }
  }

  async testMultiTabCapture() {
    console.log('[Test] Multi-Tab Capture Architecture...');

    try {
      // Test helper tab URL generation
      const captureUrl = chrome.runtime.getURL('capture.html');
      const urlGenerated = captureUrl.includes('capture.html');

      // Test required files accessibility
      const requiredFiles = ['capture.html', 'capture.js', 'config.js'];
      const filesAccessible = requiredFiles.every(file => {
        const url = chrome.runtime.getURL(file);
        return url.startsWith('chrome-extension://');
      });

      this.testResults.push({
        test: 'Multi-Tab Capture Architecture',
        passed: urlGenerated && filesAccessible,
        details: `URL Generation: ${urlGenerated}, Files Accessible: ${filesAccessible}`
      });
    } catch (error) {
      this.testResults.push({
        test: 'Multi-Tab Capture Architecture',
        passed: false,
        details: error.message
      });
    }
  }

  async testExtensionUI() {
    console.log('[Test] Extension UI...');

    const hasPopup = document.querySelector('#startBtn') !== null;
    const hasMultiTabButton = document.querySelector('#scrumbot-toggle') !== null;

    this.testResults.push({
      test: 'Extension UI',
      passed: hasPopup || hasMultiTabButton,
      details: `Popup: ${hasPopup}, Multi-Tab UI: ${hasMultiTabButton}`
    });
  }

  async testBackendIntegration() {
    console.log('[Test] Backend Integration...');

    try {
      const response = await fetch('http://localhost:3002/health');
      const data = await response.json();
      const isHealthy = data.status === 'healthy';

      // Test meetings endpoint
      const meetingsResponse = await fetch('http://localhost:3002/get-meetings');
      const meetingsData = await meetingsResponse.json();
      const hasMeetings = meetingsData.total > 0;

      this.testResults.push({
        test: 'Backend Integration',
        passed: isHealthy && hasMeetings,
        details: `Health: ${isHealthy}, Meetings: ${meetingsData.total} stored`
      });
    } catch (error) {
      this.testResults.push({
        test: 'Backend Integration',
        passed: false,
        details: error.message
      });
    }
  }

  printResults() {
    console.log('\n[Epic A Test Results]');
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
      console.log('🎉 Epic A is ready for integration!');
    } else {
      console.log('⚠️  Some tests failed. Please fix before integration.');
    }
  }
}

// Run tests
const tester = new EpicAIntegrationTest();
tester.runAllTests();