# EC2 WebSocket Event Fixes Testing Guide

## Overview

This guide provides step-by-step instructions for testing the WebSocket event fixes on EC2, ensuring the duplicate transcription event issues have been resolved and the system is production-ready.

## Pre-Testing Requirements

### EC2 Instance Setup
- EC2 instance with ScrumBot backend deployed
- PM2 process manager configured
- Ngrok tunnel for WebSocket access
- Chrome extension loaded and configured

### Environment Variables Required
```bash
# TiDB Database
TIDB_CONNECTION_STRING=mysql://username:password@gateway01.us-west-2.prod.aws.tidbcloud.com:4000/test

# AI Provider
GROQ_API_KEY=gsk_your_groq_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=5167
ENVIRONMENT=production
DEBUG=true
```

## Testing Phases

## Phase 1: Deployment Verification

### 1.1 Deploy Updated Code
```bash
# SSH into EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-instance.amazonaws.com

# Navigate to project directory
cd /path/to/scrumy

# Pull latest changes
git pull origin feature/ai-processing-integration

# Restart services
pm2 restart all

# Check PM2 status
pm2 status
pm2 logs --lines 50
```

### 1.2 Verify File Deployment
```bash
# Check critical files are deployed
ls -la shared/websocket_events.py
ls -la shared/websocket_event_monitor.py
ls -la ai_processing/app/websocket_server.py

# Verify Python imports work
cd ai_processing
python3 -c "from shared.websocket_events import WebSocketEventTypes; print('✅ Constants imported successfully')"
python3 -c "from shared.websocket_event_monitor import monitor_event; print('✅ Monitor imported successfully')"
```

### 1.3 Test Suite Execution
```bash
# Run the comprehensive test suite
cd /path/to/scrumy
python3 test_websocket_event_fixes.py

# Expected output:
# 📊 TEST SUMMARY
#    Total Tests: 11
#    Passed: 11 ✅
#    Failed: 0 ❌
#    Pass Rate: 100.0%
```

## Phase 2: WebSocket Server Testing

### 2.1 WebSocket Server Health Check
```bash
# Check WebSocket server is running
curl http://localhost:5167/health

# Expected response:
# {"status": "healthy", "timestamp": "2024-01-01T10:00:00Z"}

# Check WebSocket endpoint accessibility
# Using ngrok URL (replace with your actual URL)
curl https://your-ngrok-id.ngrok-free.app/health
```

### 2.2 WebSocket Connection Testing
```bash
# Install wscat if not available
npm install -g wscat

# Test WebSocket connection (replace with your ngrok URL)
wscat -c wss://your-ngrok-id.ngrok-free.app/ws

# Send handshake message:
{"type": "HANDSHAKE", "clientType": "test_client", "version": "1.0"}

# Expected response:
{"type": "HANDSHAKE_ACK", "message": "Connected successfully"}
```

### 2.3 Event Monitoring Integration Test
```bash
# Create a simple monitoring test script
cat > test_monitoring.py << 'EOF'
import sys
import os
sys.path.append('/path/to/scrumy/shared')

from websocket_event_monitor import monitor_event, get_monitoring_report
from websocket_events import WebSocketEventTypes

# Test monitoring system
result = monitor_event(
    WebSocketEventTypes.TRANSCRIPTION_RESULT,
    {
        "text": "Test transcription",
        "confidence": 0.95,
        "timestamp": "2024-01-01T10:00:00Z",
        "speaker": "TestSpeaker"
    },
    source="ec2_test",
    session_id="test_session_123"
)

print(f"✅ Monitoring test result: {result}")

# Get comprehensive report
report = get_monitoring_report()
print(f"📊 Monitoring report: {report}")
EOF

# Run monitoring test
python3 test_monitoring.py
```

## Phase 3: Chrome Extension Integration Testing

### 3.1 Chrome Extension Configuration
1. Open Chrome and navigate to `chrome://extensions/`
2. Ensure ScrumBot extension is loaded and enabled
3. Check extension configuration points to EC2 ngrok URL
4. Open browser developer tools (F12)

### 3.2 Meeting Platform Testing

#### Test on Google Meet
```javascript
// In browser console, verify configuration
console.log('ScrumBot Config:', window.SCRUMBOT_CONFIG);

// Expected output should show ngrok WebSocket URL:
// WEBSOCKET_URL: "wss://your-ngrok-id.ngrok-free.app/ws"
```

1. Join a Google Meet test meeting
2. Activate ScrumBot extension
3. Monitor browser console for WebSocket events
4. Verify only `TRANSCRIPTION_RESULT` events (no duplicates)

#### Test on Zoom (if configured)
1. Join a Zoom test meeting
2. Repeat Chrome extension testing steps
3. Monitor for consistent event handling

### 3.3 Real-time Event Monitoring
```bash
# Monitor PM2 logs in real-time
pm2 logs ai-processing --lines 0 --follow

# Look for these success indicators:
# ✅ WebSocket connected
# 📝 Whisper result: 'test transcription'
# 📨 WebSocket message: TRANSCRIPTION_RESULT
# ⚠️  NO duplicate event warnings
```

## Phase 4: End-to-End Transcription Testing

### 4.1 Audio Processing Test
1. Start a test meeting with audio
2. Speak clearly: "This is a test of the ScrumBot transcription system"
3. Monitor both server logs and browser console

#### Expected Server Log Output:
```
[2024-01-01 10:00:00] INFO - 📨 WebSocket message: HANDSHAKE
[2024-01-01 10:00:01] INFO - ✅ WebSocket connected
[2024-01-01 10:00:05] INFO - 🎤 Processing audio chunk: 4096 bytes
[2024-01-01 10:00:06] INFO - 📝 Whisper result: 'This is a test of the ScrumBot transcription system'
[2024-01-01 10:00:06] INFO - 📤 Sending TRANSCRIPTION_RESULT event
[2024-01-01 10:00:06] INFO - ✅ Event monitoring: no duplicates detected
```

#### Expected Browser Console Output:
```javascript
[WebSocket Event] WebSocket: {
  eventType: "TRANSCRIPTION_RESULT",
  standardType: "N/A",
  isDeprecated: false,
  dataKeys: ["text", "confidence", "timestamp", "speaker", "chunkId"],
  timestamp: "2024-01-01T10:00:06.123Z"
}
```

### 4.2 Duplicate Event Detection Test
```bash
# Create a script to simulate duplicate events (should be caught)
cat > simulate_duplicate_test.py << 'EOF'
import asyncio
import websockets
import json
from datetime import datetime

async def test_duplicate_detection():
    uri = "wss://your-ngrok-id.ngrok-free.app/ws"
    
    async with websockets.connect(uri) as websocket:
        # Send handshake
        await websocket.send(json.dumps({
            "type": "HANDSHAKE",
            "clientType": "duplicate_test"
        }))
        
        # Wait for handshake ack
        response = await websocket.recv()
        print(f"Handshake response: {response}")
        
        # Send identical audio chunks (should trigger duplicate detection)
        audio_data = "fake_audio_data_for_testing"
        for i in range(2):
            message = {
                "type": "AUDIO_CHUNK",
                "data": audio_data,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "platform": "test",
                    "meetingUrl": "https://test.com/meeting",
                    "chunkSize": len(audio_data)
                }
            }
            await websocket.send(json.dumps(message))
            print(f"Sent duplicate test message {i+1}")
            
            # Wait for response
            try:
                response = await websocket.recv()
                print(f"Response {i+1}: {response}")
            except asyncio.TimeoutError:
                print(f"No response for message {i+1}")

# Run test
asyncio.run(test_duplicate_detection())
EOF

# Execute duplicate detection test
python3 simulate_duplicate_test.py
```

## Phase 5: Performance and Reliability Testing

### 5.1 Network Traffic Analysis
```bash
# Monitor network usage before and after fixes
# Install nethogs if not available
sudo apt-get install nethogs

# Monitor network traffic during testing
sudo nethogs

# Expected: 50% reduction in WebSocket traffic compared to pre-fix baseline
```

### 5.2 Memory Usage Monitoring
```bash
# Monitor memory usage during intensive testing
watch -n 5 'ps aux | grep "python.*websocket" | head -5'

# Check PM2 memory monitoring
pm2 monit

# Expected: Stable memory usage, no memory leaks
```

### 5.3 Stress Testing
```bash
# Create stress test script
cat > websocket_stress_test.py << 'EOF'
import asyncio
import websockets
import json
import time
from datetime import datetime

async def stress_test_connection(connection_id):
    uri = "wss://your-ngrok-id.ngrok-free.app/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            # Send handshake
            await websocket.send(json.dumps({
                "type": "HANDSHAKE",
                "clientType": f"stress_test_{connection_id}"
            }))
            
            # Send multiple audio chunks rapidly
            for i in range(10):
                message = {
                    "type": "AUDIO_CHUNK",
                    "data": f"stress_test_audio_{connection_id}_{i}",
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {"platform": "stress_test"}
                }
                await websocket.send(json.dumps(message))
                await asyncio.sleep(0.1)  # 100ms between messages
                
            print(f"✅ Connection {connection_id} completed stress test")
            
    except Exception as e:
        print(f"❌ Connection {connection_id} failed: {e}")

async def run_stress_test():
    # Create 5 concurrent connections
    tasks = [stress_test_connection(i) for i in range(5)]
    await asyncio.gather(*tasks)

# Run stress test
asyncio.run(run_stress_test())
EOF

# Execute stress test
python3 websocket_stress_test.py
```

## Phase 6: Event Monitoring Validation

### 6.1 Monitoring Dashboard Data
```bash
# Create monitoring report script
cat > get_monitoring_report.py << 'EOF'
import sys
sys.path.append('/path/to/scrumy/shared')

from websocket_event_monitor import get_monitoring_report
import json

# Get comprehensive monitoring report
report = get_monitoring_report()

print("📊 WEBSOCKET EVENT MONITORING REPORT")
print("=" * 50)
print(f"Total Events: {report['summary']['total_events']}")
print(f"Duplicates Detected: {report['summary']['duplicates_detected']}")
print(f"Deprecated Events: {report['summary']['deprecated_events']}")
print(f"Validation Errors: {report['summary']['validation_errors']}")
print(f"Unique Sessions: {report['summary']['unique_sessions']}")

print(f"\n📈 RECOMMENDATIONS:")
for rec in report['recommendations']:
    print(f"  • {rec}")

# Save detailed report
with open('/tmp/monitoring_report.json', 'w') as f:
    json.dump(report, f, indent=2)
    
print(f"\n💾 Detailed report saved to: /tmp/monitoring_report.json")
EOF

# Run monitoring report
python3 get_monitoring_report.py
```

### 6.2 Real-time Monitoring Alerts
```bash
# Set up monitoring alert script
cat > monitoring_alerts.py << 'EOF'
import sys
import time
sys.path.append('/path/to/scrumy/shared')

from websocket_event_monitor import get_monitoring_report

def check_system_health():
    report = get_monitoring_report()
    alerts = []
    
    # Check for duplicates
    if report['summary']['duplicates_detected'] > 0:
        alerts.append(f"🚨 ALERT: {report['summary']['duplicates_detected']} duplicate events detected")
    
    # Check for validation errors
    if report['summary']['validation_errors'] > 0:
        alerts.append(f"⚠️  WARNING: {report['summary']['validation_errors']} validation errors")
    
    # Check for high deprecated usage
    if report['summary']['deprecated_events'] > 10:
        alerts.append(f"📢 INFO: {report['summary']['deprecated_events']} deprecated events (consider updating)")
    
    if not alerts:
        print("✅ System health: All systems normal")
    else:
        for alert in alerts:
            print(alert)
    
    return len(alerts) == 0

# Run continuous monitoring (every 30 seconds for 5 minutes)
for i in range(10):
    print(f"\n🔍 Health check #{i+1} at {time.strftime('%H:%M:%S')}")
    check_system_health()
    time.sleep(30)
EOF

# Run monitoring alerts
python3 monitoring_alerts.py
```

## Phase 7: Production Readiness Checklist

### 7.1 System Health Verification
- [ ] All PM2 processes running without errors
- [ ] WebSocket server responding to health checks
- [ ] No duplicate events detected in monitoring
- [ ] Memory usage stable under load
- [ ] Network traffic reduced by ~50%

### 7.2 Feature Verification
- [ ] Chrome extension connects successfully
- [ ] Audio transcription working correctly
- [ ] Only TRANSCRIPTION_RESULT events (no lowercase variants)
- [ ] Event monitoring system active
- [ ] Backward compatibility maintained

### 7.3 Error Handling Verification
- [ ] Graceful handling of connection drops
- [ ] Proper error logging
- [ ] No unhandled exceptions in logs
- [ ] Monitoring alerts working

## Troubleshooting Common Issues

### Issue 1: Import Errors
```bash
# Symptom: "ModuleNotFoundError: No module named 'websocket_events'"
# Solution:
export PYTHONPATH="/path/to/scrumy/shared:$PYTHONPATH"
# Or add to ~/.bashrc for permanent fix
```

### Issue 2: WebSocket Connection Failures
```bash
# Check ngrok status
curl https://your-ngrok-id.ngrok-free.app/health

# Restart ngrok if needed
pkill ngrok
./start-ngrok.sh

# Update Chrome extension config with new ngrok URL
```

### Issue 3: Duplicate Events Still Detected
```bash
# Check server logs for warnings
pm2 logs | grep -i "duplicate"

# Verify latest code is deployed
git log --oneline -5

# Restart all services
pm2 restart all
```

### Issue 4: Performance Issues
```bash
# Check memory usage
free -h
pm2 monit

# Check disk space
df -h

# Restart services if memory usage high
pm2 restart all
```

## Success Criteria

### ✅ Testing Complete When:
1. All 11 test suite tests pass (100%)
2. No duplicate events detected during 30-minute test session
3. Chrome extension successfully processes transcription events
4. Memory usage stable under load
5. Network traffic reduced compared to baseline
6. Event monitoring system reports no issues
7. Real-time transcription working accurately

### 📊 Performance Benchmarks:
- **Network Traffic**: 50% reduction in WebSocket messages
- **Event Processing**: Single TRANSCRIPTION_RESULT per audio chunk
- **Memory Usage**: Stable, no leaks detected
- **Response Time**: < 100ms for event processing
- **Error Rate**: 0% for WebSocket event handling

## Post-Testing Documentation

### Results Documentation Template
```markdown
# EC2 WebSocket Testing Results

**Date**: [Test Date]
**Tester**: [Name]
**EC2 Instance**: [Instance ID]
**Duration**: [Test Duration]

## Test Results Summary
- Test Suite: [X/11] tests passed
- Duplicate Events: [X] detected
- Performance: [X]% traffic reduction achieved
- Errors: [X] errors encountered

## Issues Found
1. [Issue description and resolution]
2. [Issue description and resolution]

## Recommendations
1. [Recommendation]
2. [Recommendation]

## Production Readiness
- [ ] Ready for production deployment
- [ ] Needs additional testing
- [ ] Issues require resolution before deployment
```

## Continuous Monitoring Setup

### Long-term Monitoring Script
```bash
# Create daily monitoring cron job
cat > /etc/cron.daily/websocket-monitoring << 'EOF'
#!/bin/bash
cd /path/to/scrumy
python3 -c "
from shared.websocket_event_monitor import get_monitoring_report
import json
from datetime import datetime

report = get_monitoring_report()
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

if report['summary']['duplicates_detected'] > 0:
    print(f'{timestamp}: 🚨 ALERT - {report[\"summary\"][\"duplicates_detected\"]} duplicates detected')
else:
    print(f'{timestamp}: ✅ System healthy - no duplicates detected')
" >> /var/log/websocket-monitoring.log 2>&1
EOF

chmod +x /etc/cron.daily/websocket-monitoring
```

This comprehensive testing guide ensures thorough validation of the WebSocket event fixes in the EC2 environment before production deployment.