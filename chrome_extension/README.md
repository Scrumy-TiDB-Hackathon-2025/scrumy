# ScrumBot Chrome Extension - Enhanced Edition

AI-powered meeting transcription extension with participant detection, speaker attribution, and task extraction for the TiDB AgentX Hackathon 2025.

## 🎯 Core Features

### 1. **"Who Attended the Meeting"** ✅
- **Real-time Participant Detection**: Uses Google Meet's `data-participant-id` for accurate tracking
- **Instant Join/Leave Detection**: DOM observer provides 3-second maximum response time
- **Smart Name Extraction**: Handles duplicated names and extracts clean participant names
- **Host/Guest Identification**: Automatically identifies meeting hosts and participants
- **Cross-platform Support**: Works across all major meeting platforms

### 2. **"Who Said What"** ✅ 
- **Speaker Attribution**: AI-powered speaker identification using participant context
- **Enhanced Transcription**: Real-time transcription with speaker labels
- **Confidence Scoring**: Provides confidence levels for speaker attribution

### 3. **"Create Tasks Based on What Was Said"** ✅
- **Action Item Extraction**: AI extracts tasks and assignments from meeting discussions
- **Smart Prioritization**: Automatically prioritizes tasks based on urgency and impact
- **Task Assignment**: Maps tasks to participants mentioned in the meeting

## 🏗️ Architecture

Built on innovative multi-tab audio capture technology with enhanced AI processing integration.

## 🚀 Quick Start

### Development Mode (Recommended for Testing)

```bash
# Install dependencies
npm install

# Start development environment with mock servers
npm run dev

# Load extension in Chrome:
# 1. Go to chrome://extensions/
# 2. Enable Developer mode
# 3. Click "Load unpacked"
# 4. Select this folder
```

### Production Mode (Live Backend)

```bash
# Switch to production mode
npm run env:prod

# Load/reload extension in Chrome
# Ensure your backend is running!
```

## 🎯 Key Features

### Real-Time Participant Detection
- **Instant Detection**: Uses Google Meet's internal DOM structure for immediate participant tracking
- **Accurate Counting**: Tracks actual participants using unique device IDs, not UI elements
- **Smart Name Extraction**: Handles Google Meet's duplicated name format (e.g., "John SmithJohn Smith" → "John Smith")
- **Host Identification**: Automatically distinguishes between meeting hosts and guests
- **Responsive Updates**: DOM observer detects join/leave events within 3 seconds maximum
- **Debug Tools**: Optional DOM logging and console testing functions for troubleshooting

### Multi-Tab Audio Capture Innovation
- **Solves Chrome's Meeting Tab Visibility Issue**: Uses helper tab to make meeting tabs visible in sharing dialog
- **Universal Meeting Support**: Works with Google Meet, Zoom, and Microsoft Teams
- **Seamless User Experience**: Step-by-step guidance through capture process

### Advanced Audio Processing
- **High-Quality Capture**: 16kHz sample rate with echo cancellation and noise suppression
- **Real-Time Processing**: 1-2 second audio chunks for responsive transcription
- **Multiple Output Streams**: WebSocket for real-time, REST API for reliability

### Enhanced Participant Detection
- **DOM-Based Detection**: Uses Google Meet's internal `data-participant-id` attributes
- **Real-time Updates**: DOM observer detects changes within 100ms
- **Smart Filtering**: Excludes UI elements and temporary join notifications
- **Debug Mode**: Optional DOM logging for troubleshooting (disabled by default)

### Development-First Architecture
- **Complete Mock Environment**: Test without any backend dependencies
- **Environment Switching**: One command to switch between dev/prod
- **Comprehensive Testing**: Automated tests for all components

## 🏗️ Technical Architecture

This extension implements a sophisticated **multi-tab capture architecture** to solve Chrome's restriction on capturing audio from the requesting tab.

### Core Innovation: Multi-Tab Capture Pattern

```
Meeting Tab (Google Meet)  →  Helper Tab (Capture UI)  →  Audio Stream
     ↓                              ↓                        ↓
User clicks "Start"         User selects meeting tab    Audio processing
     ↓                              ↓                        ↓
Helper tab opens           Meeting tab now visible     Backend integration
```

**Why This Works**: Chrome excludes the requesting tab from `getDisplayMedia()` options. By requesting from a different tab, the meeting tab becomes visible and selectable.

For detailed technical documentation, see **[ARCHITECTURE.md](./ARCHITECTURE.md)**.

## 📁 Project Structure

```
chrome_extension/
├── 📄 ARCHITECTURE.md         # Comprehensive technical documentation
├── 📄 TESTING_GUIDE.md        # Testing procedures and troubleshooting
├── 📄 manifest.json           # Chrome extension configuration
├── 📄 config.js               # Environment-based configuration
├── 📄 content.js              # Main content script (meeting tab)
├── 📄 capture.html/js         # Helper tab for audio capture
├── 📄 popup.html/js           # Extension popup interface
├── 📄 ui-components.js        # Enhanced UI components for ScrumBot interface
├── 📁 core/                   # Core functionality modules
├── 📁 services/               # External service integrations
├── 📁 worker/                 # Background service worker
├── 📁 mocks/                  # Development mock servers
├── 📁 test/                   # Testing utilities
└── 📄 test-enhanced-features.js # Testing framework for enhanced features
```

## 🧪 Testing & Development

### Quick Test (No Backend Required)

```bash
# 1. Start mock servers
npm run dev

# 2. Load extension in Chrome
# 3. Go to Google Meet and join a call
# 4. Click ScrumBot extension icon
# 5. Click "Start Recording"
# 6. Follow helper tab instructions
# 7. Watch console for mock transcriptions
```

### Available Scripts

```bash
npm run dev          # Start both mock servers
npm run env:dev      # Switch to development mode  
npm run env:prod     # Switch to production mode
npm run test:ws      # WebSocket mock server only
npm run test:rest    # REST API mock server only
npm run test:core    # Run component tests
```

### Debug Commands (Browser Console)

```javascript
// Core Testing
testScrumBot()                    // Run all component tests
testMultiTabCapture()             // Test multi-tab architecture
testController()                  // Test controller status
console.log(window.SCRUMBOT_CONFIG) // Check current configuration

// Participant Detection Testing & Debugging
testParticipantDetection()        // Test current participant detection
enableDOMDebug()                  // Enable DOM logging to files (for debugging)
disableDOMDebug()                 // Disable DOM logging (default)
captureDOMAnalysis()              // Capture one-time DOM analysis file
```

## 🔧 Configuration

### Environment Switching

```bash
# Development: Mock servers, debug logging, 2s audio chunks
npm run env:dev

# Production: Real backend, optimized performance, 1s audio chunks  
npm run env:prod
```

### Manual Configuration

Edit `config.js` to customize:
- Backend URLs and endpoints
- Audio processing settings
- Debug and logging options
- Mock transcription behavior

## 🚨 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Extension won't load | Check manifest.json syntax, reload in chrome://extensions/ |
| Helper tab doesn't open | Check pop-up blocker, verify permissions |
| Meeting tab not visible | Ensure you're in active meeting, not just lobby |
| Audio capture fails | Grant screen sharing permissions, enable "Also share tab audio" |
| Mock servers won't start | Check ports 8081/3002 availability, restart with `npm run dev` |
| Participant detection issues | Use `testParticipantDetection()` in console, enable debug with `enableDOMDebug()` |
| Participants not updating | Check if in active meeting, DOM observer should detect changes in 3s |

### Getting Help

1. **Check Console Logs**: Detailed error messages and debug information
2. **Run Test Commands**: Use browser console debug commands
3. **Review Documentation**: See [ARCHITECTURE.md](./ARCHITECTURE.md) for technical details
4. **Check Testing Guide**: See [TESTING_GUIDE.md](./TESTING_GUIDE.md) for procedures

## 🎉 Success Indicators

When working correctly, you should see:

✅ **Extension loads** without errors  
✅ **Meeting detection** shows platform and status  
✅ **Participant detection** shows accurate count and names  
✅ **Real-time updates** when participants join/leave (within 3 seconds)  
✅ **Helper tab opens** with clear instructions  
✅ **Meeting tab appears** in sharing dialog  
✅ **Audio capture starts** successfully  
✅ **Mock transcriptions** appear in console (dev mode)  
✅ **Stop recording** works cleanly  

## 📚 Documentation

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Complete technical architecture and engineering details
- **[TESTING_GUIDE.md](./TESTING_GUIDE.md)** - Comprehensive testing procedures and troubleshooting
- **[Epic_A_Chrome_Extension_Guide.md](../Epic_A_Chrome_Extension_Guide.md)** - Original development guide

## 🏆 Technical Achievements

- **Multi-Tab Capture Innovation**: First-of-its-kind solution to Chrome's meeting tab visibility issue
- **Cross-Context Architecture**: Sophisticated message passing between extension contexts
- **Development-First Design**: Complete offline testing with realistic mock environment
- **Security-Compliant**: Works within Chrome's security model and permission system
- **Production-Ready**: Environment switching, error handling, and performance optimization

---

**Built for TiDB AgentX Hackathon 2025**  
**Version**: 1.0.0  
**License**: MIT