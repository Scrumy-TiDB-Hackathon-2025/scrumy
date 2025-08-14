// test-extension.js - Quick test script for the chrome extension
console.log('🧪 Testing ScrumBot Chrome Extension...');

// Test 1: Configuration loaded
function testConfig() {
  console.log('\n1. Testing Configuration...');
  if (window.SCRUMBOT_CONFIG) {
    console.log('✅ Config loaded');
    console.log('   Backend URL:', window.SCRUMBOT_CONFIG.BACKEND_URL);
    console.log('   Frontend URL:', window.SCRUMBOT_CONFIG.FRONTEND_URL);
    return true;
  } else {
    console.log('❌ Config not loaded');
    return false;
  }
}

// Test 2: Meeting Detection
function testMeetingDetection() {
  console.log('\n2. Testing Meeting Detection...');
  if (window.meetingDetector) {
    console.log('✅ Meeting detector available');
    console.log('   Platform:', window.meetingDetector.platform);
    console.log('   In meeting:', window.meetingDetector.isInMeeting);
    return true;
  } else {
    console.log('❌ Meeting detector not available');
    return false;
  }
}

// Test 3: Audio Capture
function testAudioCapture() {
  console.log('\n3. Testing Audio Capture...');
  if (window.scrumBotAudioCapture) {
    console.log('✅ Audio capture available');
    console.log('   Recording:', window.scrumBotAudioCapture.isRecording);
    return true;
  } else {
    console.log('❌ Audio capture not available');
    return false;
  }
}

// Test 4: WebSocket Client
function testWebSocketClient() {
  console.log('\n4. Testing WebSocket Client...');
  if (window.scrumBotWebSocket) {
    console.log('✅ WebSocket client available');
    console.log('   Connected:', window.scrumBotWebSocket.isConnected);
    console.log('   Server URL:', window.scrumBotWebSocket.serverUrl);
    return true;
  } else {
    console.log('❌ WebSocket client not available');
    return false;
  }
}

// Test 5: Controller
function testController() {
  console.log('\n5. Testing ScrumBot Controller...');
  if (window.scrumBotController) {
    console.log('✅ Controller available');
    console.log('   Recording:', window.scrumBotController.isRecording);
    return true;
  } else {
    console.log('❌ Controller not available');
    return false;
  }
}

// Test 6: Backend Connection
async function testBackendConnection() {
  console.log('\n6. Testing Backend Connection...');
  if (!window.SCRUMBOT_CONFIG) {
    console.log('❌ No config for backend test');
    return false;
  }

  try {
    const response = await fetch(`${window.SCRUMBOT_CONFIG.BACKEND_URL}/health`, {
      headers: {
        'ngrok-skip-browser-warning': 'true'
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ Backend connected');
      console.log('   Status:', data.status);
      return true;
    } else {
      console.log('❌ Backend connection failed:', response.status);
      return false;
    }
  } catch (error) {
    console.log('❌ Backend connection error:', error.message);
    return false;
  }
}

// Run all tests
async function runAllTests() {
  console.log('🚀 Starting ScrumBot Extension Tests...');
  console.log('=====================================');

  const results = [];
  results.push(testConfig());
  results.push(testMeetingDetection());
  results.push(testAudioCapture());
  results.push(testWebSocketClient());
  results.push(testController());
  results.push(await testBackendConnection());

  const passed = results.filter(r => r).length;
  const total = results.length;

  console.log('\n📊 Test Results');
  console.log('================');
  console.log(`Passed: ${passed}/${total}`);

  if (passed === total) {
    console.log('🎉 All tests passed! Extension is ready.');
  } else {
    console.log('⚠️  Some tests failed. Check the issues above.');
  }

  return { passed, total, success: passed === total };
}

// Auto-run tests if on a meeting platform
if (window.location.href.includes('meet.google.com') || 
    window.location.href.includes('zoom.us') || 
    window.location.href.includes('teams.microsoft.com')) {
  
  // Wait for all components to load
  setTimeout(() => {
    runAllTests();
  }, 3000);
}

// Make test function available globally
window.testScrumBot = runAllTests;