# ScrumBot Chrome Extension - Testing Guide

## Environment Setup

### Development Mode (Default)
```bash
# Ensure you're in dev mode
npm run env:dev

# Start mock servers
npm run dev
```

### Production Mode (When backend is ready)
```bash
# Switch to production mode
npm run env:prod

# No mock servers needed - uses real backend
```

## Quick Setup & Testing

### 1. Start Development Environment

```bash
cd chrome_extension

# Install dependencies
npm install

# Ensure dev mode (default)
npm run env:dev

# Start mock servers
npm run dev
```

You should see:
```
📡 Mock servers starting...
   WebSocket: ws://localhost:8080/ws
   REST API:  http://localhost:3001
```

### 2. Load Extension in Chrome

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `chrome_extension` folder
5. Extension should appear with ScrumBot icon

### 3. Test on Google Meet

1. Go to [Google Meet](https://meet.google.com)
2. Start or join a meeting
3. Open browser console (F12)
4. Look for ScrumBot initialization messages
5. Run test: `testScrumBot()`

### 4. Test Extension Popup

1. Click the ScrumBot extension icon in Chrome toolbar
2. Should see popup with:
   - Connection status (should show green in dev mode)
   - Start/Stop recording buttons
   - Dashboard and test buttons

### 5. Test Recording with Mock Data

1. In a Google Meet call, click ScrumBot icon
2. Click "Start Recording" 
3. Grant audio permissions when prompted
4. Should see "Recording..." status
5. Check console for:
   - Audio chunk messages
   - Mock transcription results
   - WebSocket connection messages

## Expected Console Output (Dev Mode)

```
🔧 ScrumBot Config Loaded: {
  environment: 'dev',
  backend: 'http://localhost:3001',
  websocket: 'ws://localhost:8080/ws',
  mockMode: true
}
🤖 ScrumBot extension loaded on: https://meet.google.com/...
✅ ScrumBot: Supported platform detected: meet.google.com
📝 Meeting ID: meeting-1234567890-abc123
[ScrumBot] Detected platform: google-meet
[WebSocket] Using server URL: ws://localhost:8080/ws
✅ ScrumBot controller initialized
🟢 Connected
[AudioCapture] Recording started with 2000ms chunks
[AudioCapture] Mock transcription: {text: "Hello everyone, welcome to our team meeting.", confidence: 0.92, mock: true}
```

## Environment Switching

### Switch to Development Mode
```bash
npm run env:dev
# Then reload extension in Chrome
```

### Switch to Production Mode
```bash
npm run env:prod
# Then reload extension in Chrome
# Make sure real backend is running!
```

## Testing Scenarios

### 1. Basic Functionality Test
- ✅ Extension loads without errors
- ✅ Meeting detection works on Google Meet
- ✅ Popup shows correct status
- ✅ Mock servers respond to health checks

### 2. Audio Capture Test
- ✅ Audio permissions granted
- ✅ Audio stream starts successfully
- ✅ Audio chunks generated every 2 seconds (dev mode)
- ✅ Mock transcriptions appear in console

### 3. WebSocket Test
- ✅ WebSocket connects to mock server
- ✅ Handshake successful
- ✅ Audio chunks sent via WebSocket
- ✅ Mock transcription responses received

### 4. REST API Test
- ✅ Health endpoint responds
- ✅ Save transcript endpoint works
- ✅ Get meetings endpoint returns data
- ✅ Mock transcription endpoint responds

## Troubleshooting

### Extension Not Loading
- Check manifest.json syntax
- Reload extension in chrome://extensions/
- Check console for errors

### Mock Servers Not Starting
```bash
# Check if ports are in use
lsof -i :8080  # WebSocket server
lsof -i :3001  # REST API server

# Kill processes if needed
kill -9 <PID>

# Restart servers
npm run dev
```

### Audio Capture Fails
- Ensure you're in an active meeting
- Grant microphone permissions
- Check if other apps are using microphone
- Try refreshing the meeting page

### WebSocket Connection Issues
- Verify mock WebSocket server is running
- Check browser console for connection errors
- Try restarting mock servers

## Test Commands

Run these in browser console on a meeting page:

```javascript
// Test all components
testScrumBot()

// Check configuration
console.log('Config:', window.SCRUMBOT_CONFIG)

// Test individual components
window.meetingDetector.checkMeetingStatus()
window.scrumBotAudioCapture.startCapture()
window.scrumBotWebSocket.connect()

// Check states
console.log('Meeting detected:', window.meetingDetector.isInMeeting)
console.log('Recording:', window.scrumBotController.isRecording)
console.log('WebSocket connected:', window.scrumBotWebSocket.isConnected)

// Test mock transcription
window.scrumBotAudioCapture.handleMockTranscription('test-audio-data')
```

## Development Workflow

### Daily Development
1. `npm run dev` - Start mock servers
2. Load/reload extension in Chrome
3. Test on Google Meet
4. Check console logs for issues
5. Make code changes
6. Reload extension to test changes

### Before Production
1. `npm run env:prod` - Switch to production mode
2. Verify backend is running
3. Test with real backend endpoints
4. Verify WebSocket connection works
5. Test real audio transcription

## Next Steps After Testing

### Development Phase ✅
1. ✅ Verify all components load correctly
2. ✅ Test meeting detection works
3. ✅ Test audio capture permissions
4. ✅ Test mock API connections
5. ✅ Test WebSocket with mock server
6. ✅ Test mock transcription flow

### Production Integration 🔄
1. 🔄 Switch to production mode
2. 🔄 Test real backend API connection
3. 🔄 Test real audio transcription
4. 🔄 Test WebSocket streaming
5. 🔄 Test transcript storage
6. 🔄 Integration with frontend dashboard