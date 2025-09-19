# ScrumBot Audio Fix Implementation Checklist

## 🚨 CRITICAL FIXES (Implement First)

### 1. Chrome Extension Audio Capture Fix
- [ ] **File**: `chrome_extension/core/audiocapture.js`
- [ ] **Action**: Replace existing AudioCapture class with EnhancedAudioCapture
- [ ] **Test**: Check browser console for audio level logs
- [ ] **Expected**: Should see "🎵 Audio detected" messages when speaking

### 2. WebSocket Server Whisper Enhancement
- [ ] **File**: `ai_processing/app/websocket_server.py`
- [ ] **Action**: Replace `_process_audio_with_whisper` method with enhanced version
- [ ] **Dependencies**: Install scipy if not present: `pip install scipy`
- [ ] **Test**: Check server logs for "🎵 Audio Stats" messages
- [ ] **Expected**: Better transcription results, fewer [BLANK_AUDIO] responses

### 3. Buffer Configuration Update
- [ ] **File**: `ai_processing/app/websocket_server.py`
- [ ] **Action**: Update AudioBufferManager with new timing settings
- [ ] **Test**: Verify 3-second buffer duration in logs
- [ ] **Expected**: "Processing timeout buffer (3000.0ms)" messages

## 🔍 TESTING PROTOCOL

### Phase 1: Quick Verification (5 minutes)
1. **Start Services**
   ```bash
   pm2 restart scrumbot-websocket
   pm2 restart scrumbot-backend
   ```

2. **Test Audio Levels**
   - Open Google Meet
   - Check Chrome DevTools Console
   - Speak normally
   - Look for "🎵 Audio detected" messages

3. **Verify Whisper Processing**
   - Check PM2 logs: `pm2 logs scrumbot-websocket`
   - Look for "🎵 Audio Stats" messages
   - Verify non-silence detection

### Phase 2: Full Transcription Test (10 minutes)
1. **Record Test Script**
   - Use the same transcription_test_script.md
   - Speak clearly and at normal pace
   - Monitor console logs in real-time

2. **Expected Results**
   - Audio level detection: Peak > 0.01
   - Whisper processing: Non-blank results
   - Transcription accuracy: >70% for clear speech

### Phase 3: Integration Test (15 minutes)
1. **Complete Meeting Flow**
   - Start meeting
   - Speak test content
   - End meeting
   - Check final transcript in database

2. **Success Criteria**
   - Clear audio capture logs
   - Meaningful transcription results
   - Proper meeting end processing

## 🚨 ROLLBACK PLAN

If issues occur:
1. **Backup current files** before making changes
2. **Keep original versions** of modified files
3. **Test incrementally** - implement one fix at a time
4. **Monitor logs** after each change

## 📊 SUCCESS METRICS

### Before Fix (Current State)
- Transcription accuracy: ~5%
- Blank audio detection: ~90%
- Speech recognition: Fragmented phrases only

### After Fix (Target State)
- Transcription accuracy: >70%
- Blank audio detection: <20%
- Speech recognition: Clear, coherent sentences

## 🔧 ADDITIONAL DEPENDENCIES

```bash
# Install required Python packages
cd ai_processing
pip install scipy numpy

# Verify Whisper model
ls -la whisper.cpp/models/ggml-base.en.bin

# Check audio system (if on local machine)
arecord -l
```

## 📞 SUPPORT CHECKLIST

If problems persist after implementation:
- [ ] Verify microphone permissions in Chrome
- [ ] Test with different browsers
- [ ] Check system audio settings
- [ ] Test with external microphone
- [ ] Verify network connectivity to WebSocket server
- [ ] Check PM2 process status and logs