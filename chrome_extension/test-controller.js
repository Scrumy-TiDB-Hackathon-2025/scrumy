// test-controller.js - Test script to verify controller initialization
console.log('🧪 Testing ScrumBot Controller Initialization...');

// Wait for all components to load
setTimeout(() => {
  console.log('\n📊 Component Status:');
  console.log('===================');
  
  const components = {
    'Config': !!window.SCRUMBOT_CONFIG,
    'Meeting Detector': !!window.meetingDetector,
    'Audio Capture': !!window.scrumBotAudioCapture,
    'WebSocket Client': !!window.scrumBotWebSocket,
    'ScrumBot Controller': !!window.scrumBotController
  };
  
  let allLoaded = true;
  
  Object.entries(components).forEach(([name, loaded]) => {
    const status = loaded ? '✅' : '❌';
    console.log(`${status} ${name}: ${loaded ? 'Loaded' : 'Missing'}`);
    if (!loaded) allLoaded = false;
  });
  
  console.log('\n🔍 Detailed Analysis:');
  console.log('====================');
  
  if (window.SCRUMBOT_CONFIG) {
    console.log('✅ Config environment:', window.SCRUMBOT_CONFIG.ENVIRONMENT);
    console.log('✅ Backend URL:', window.SCRUMBOT_CONFIG.BACKEND_URL);
    console.log('✅ WebSocket URL:', window.SCRUMBOT_CONFIG.WEBSOCKET_URL);
  }
  
  if (window.meetingDetector) {
    console.log('✅ Meeting platform:', window.meetingDetector.platform);
    console.log('✅ In meeting:', window.meetingDetector.isInMeeting);
  }
  
  if (window.scrumBotController) {
    console.log('✅ Controller recording:', window.scrumBotController.isRecording);
    console.log('✅ Controller detector:', !!window.scrumBotController.detector);
    console.log('✅ Controller audio capture:', !!window.scrumBotController.audioCapture);
  } else {
    console.log('❌ Controller missing - checking why...');
    
    // Check if dependencies are available
    if (!window.meetingDetector) {
      console.log('   - Missing MeetingDetector class');
    }
    if (!window.scrumBotAudioCapture) {
      console.log('   - Missing AudioCapture class');
    }
    
    // Try to manually create controller
    try {
      if (window.MeetingDetector && window.AudioCapture) {
        console.log('🔄 Attempting to manually create controller...');
        window.scrumBotController = new ScrumBotController();
        console.log('✅ Controller manually created!');
      }
    } catch (error) {
      console.log('❌ Failed to create controller:', error.message);
    }
  }
  
  console.log('\n🎯 Summary:');
  console.log('===========');
  
  if (allLoaded) {
    console.log('🎉 All components loaded successfully!');
    console.log('✅ Extension is ready for testing');
  } else {
    console.log('⚠️  Some components are missing');
    console.log('🔄 Try reloading the extension');
  }
  
}, 2000);

// Make test function available globally
window.testController = () => {
  console.log('🧪 Manual Controller Test');
  
  if (window.scrumBotController) {
    console.log('✅ Controller available');
    console.log('   Recording:', window.scrumBotController.isRecording);
    console.log('   In meeting:', window.scrumBotController.detector?.isInMeeting);
    return true;
  } else {
    console.log('❌ Controller not available');
    return false;
  }
};