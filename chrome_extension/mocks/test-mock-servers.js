#!/usr/bin/env node

/**
 * Mock Servers Test Script
 * Comprehensive testing for WebSocket and REST mock servers
 */

const WebSocket = require('ws');
const http = require('http');
const https = require('https');

// Test configuration
const config = {
  websocketUrl: 'ws://localhost:8081',
  restBaseUrl: 'http://localhost:3002',
  timeout: 5000,
  retries: 3
};

// Test results tracking
let testResults = {
  websocket: { passed: 0, failed: 0, tests: [] },
  rest: { passed: 0, failed: 0, tests: [] },
  total: { passed: 0, failed: 0 }
};

console.log('🧪 ScrumBot Mock Servers Test Suite');
console.log('=====================================');

// Utility functions
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function logTest(category, testName, passed, details = '') {
  const status = passed ? '✅ PASS' : '❌ FAIL';
  console.log(`${status} [${category.toUpperCase()}] ${testName}`);

  if (details) {
    console.log(`     ${details}`);
  }

  testResults[category].tests.push({
    name: testName,
    passed: passed,
    details: details
  });

  if (passed) {
    testResults[category].passed++;
    testResults.total.passed++;
  } else {
    testResults[category].failed++;
    testResults.total.failed++;
  }
}

// WebSocket test functions
async function testWebSocketConnection() {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(config.websocketUrl);
    let connected = false;

    const timeout = setTimeout(() => {
      if (!connected) {
        ws.close();
        reject(new Error('Connection timeout'));
      }
    }, config.timeout);

    ws.on('open', () => {
      connected = true;
      clearTimeout(timeout);
      ws.close();
      resolve(true);
    });

    ws.on('error', (error) => {
      clearTimeout(timeout);
      reject(error);
    });
  });
}

async function testWebSocketHandshake() {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(config.websocketUrl);
    let handshakeReceived = false;

    const timeout = setTimeout(() => {
      if (!handshakeReceived) {
        ws.close();
        reject(new Error('Handshake timeout'));
      }
    }, config.timeout);

    ws.on('open', () => {
      ws.send(JSON.stringify({
        type: 'HANDSHAKE',
        clientType: 'test-client',
        version: '1.0',
        capabilities: ['audio-capture', 'testing']
      }));
    });

    ws.on('message', (data) => {
      try {
        const message = JSON.parse(data);
        if (message.type === 'HANDSHAKE_ACK') {
          handshakeReceived = true;
          clearTimeout(timeout);
          ws.close();
          resolve({
            serverVersion: message.serverVersion,
            status: message.status,
            capabilities: message.capabilities
          });
        }
      } catch (error) {
        clearTimeout(timeout);
        ws.close();
        reject(error);
      }
    });

    ws.on('error', (error) => {
      clearTimeout(timeout);
      reject(error);
    });
  });
}

async function testBasicAudioChunk() {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(config.websocketUrl);
    let transcriptionReceived = false;

    const timeout = setTimeout(() => {
      if (!transcriptionReceived) {
        ws.close();
        reject(new Error('Transcription timeout'));
      }
    }, config.timeout);

    ws.on('open', () => {
      // Send handshake first
      ws.send(JSON.stringify({
        type: 'HANDSHAKE',
        clientType: 'test-client'
      }));

      // Wait a bit then send audio chunk
      setTimeout(() => {
        ws.send(JSON.stringify({
          type: 'AUDIO_CHUNK',
          data: 'dGVzdCBhdWRpbyBkYXRh', // base64 "test audio data"
          timestamp: new Date().toISOString(),
          metadata: {
            platform: 'google-meet',
            meetingUrl: 'https://meet.google.com/test-123',
            chunkSize: 100,
            sampleRate: 16000
          }
        }));
      }, 500);
    });

    ws.on('message', (data) => {
      try {
        const message = JSON.parse(data);
        if (message.type === 'transcription_result') {
          transcriptionReceived = true;
          clearTimeout(timeout);
          ws.close();
          resolve({
            text: message.data.text,
            confidence: message.data.confidence,
            speaker: message.data.speaker
          });
        }
      } catch (error) {
        // Ignore parsing errors for other messages
      }
    });

    ws.on('error', (error) => {
      clearTimeout(timeout);
      reject(error);
    });
  });
}

async function testEnhancedAudioChunk() {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(config.websocketUrl);
    let enhancedTranscriptionReceived = false;
    let meetingUpdateReceived = false;
    let results = {};

    const timeout = setTimeout(() => {
      ws.close();
      if (!enhancedTranscriptionReceived) {
        reject(new Error('Enhanced transcription timeout'));
      } else {
        resolve(results);
      }
    }, config.timeout);

    ws.on('open', () => {
      // Send handshake first
      ws.send(JSON.stringify({
        type: 'HANDSHAKE',
        clientType: 'test-client'
      }));

      // Wait then send enhanced audio chunk
      setTimeout(() => {
        ws.send(JSON.stringify({
          type: 'AUDIO_CHUNK_ENHANCED',
          data: 'dGVzdCBhdWRpbyBkYXRh',
          timestamp: new Date().toISOString(),
          platform: 'google-meet',
          meetingUrl: 'https://meet.google.com/test-enhanced-123',
          participants: [
            {
              id: 'participant_1',
              name: 'Test User One',
              platform_id: 'google_meet_test_123',
              status: 'active',
              is_host: true,
              join_time: new Date().toISOString()
            },
            {
              id: 'participant_2',
              name: 'Test User Two',
              platform_id: 'google_meet_test_456',
              status: 'active',
              is_host: false,
              join_time: new Date().toISOString()
            }
          ],
          participant_count: 2,
          metadata: {
            chunk_size: 100,
            sample_rate: 16000,
            channels: 1,
            format: 'webm'
          }
        }));
      }, 500);
    });

    ws.on('message', (data) => {
      try {
        const message = JSON.parse(data);

        if (message.type === 'TRANSCRIPTION_RESULT') {
          enhancedTranscriptionReceived = true;
          results.transcription = {
            text: message.data.text,
            speaker: message.data.speaker,
            speaker_id: message.data.speaker_id,
            participants: message.data.speakers
          };
        }

        if (message.type === 'MEETING_UPDATE') {
          meetingUpdateReceived = true;
          results.meetingUpdate = {
            participants: message.data.participants,
            participant_count: message.data.participant_count,
            platform: message.data.platform
          };
        }

        if (enhancedTranscriptionReceived && meetingUpdateReceived) {
          clearTimeout(timeout);
          ws.close();
          resolve(results);
        }
      } catch (error) {
        // Ignore parsing errors
      }
    });

    ws.on('error', (error) => {
      clearTimeout(timeout);
      reject(error);
    });
  });
}

async function testMeetingEvent() {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(config.websocketUrl);
    let eventAckReceived = false;

    const timeout = setTimeout(() => {
      if (!eventAckReceived) {
        ws.close();
        reject(new Error('Meeting event ACK timeout'));
      }
    }, config.timeout);

    ws.on('open', () => {
      // Send handshake first
      ws.send(JSON.stringify({
        type: 'HANDSHAKE',
        clientType: 'test-client'
      }));

      // Send meeting event
      setTimeout(() => {
        ws.send(JSON.stringify({
          type: 'MEETING_EVENT',
          eventType: 'meeting_started',
          timestamp: new Date().toISOString(),
          data: {
            meetingId: 'test-meeting-123',
            participant: {
              id: 'participant_1',
              name: 'Test User',
              status: 'active',
              is_host: true
            },
            total_participants: 1
          }
        }));
      }, 500);
    });

    ws.on('message', (data) => {
      try {
        const message = JSON.parse(data);
        if (message.type === 'MEETING_EVENT_ACK') {
          eventAckReceived = true;
          clearTimeout(timeout);
          ws.close();
          resolve({
            eventType: message.eventType,
            status: message.status
          });
        }
      } catch (error) {
        // Ignore parsing errors
      }
    });

    ws.on('error', (error) => {
      clearTimeout(timeout);
      reject(error);
    });
  });
}

// REST API test functions
function makeRequest(method, path, data = null) {
  return new Promise((resolve, reject) => {
    const url = `${config.restBaseUrl}${path}`;
    const options = {
      method: method,
      headers: {
        'Content-Type': 'application/json'
      },
      timeout: config.timeout
    };

    const req = http.request(url, options, (res) => {
      let body = '';

      res.on('data', (chunk) => {
        body += chunk;
      });

      res.on('end', () => {
        try {
          const response = {
            statusCode: res.statusCode,
            headers: res.headers,
            data: JSON.parse(body)
          };
          resolve(response);
        } catch (error) {
          resolve({
            statusCode: res.statusCode,
            headers: res.headers,
            data: body
          });
        }
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });

    if (data) {
      req.write(JSON.stringify(data));
    }

    req.end();
  });
}

async function testRestHealth() {
  const response = await makeRequest('GET', '/health');
  return {
    statusCode: response.statusCode,
    status: response.data.status,
    server: response.data.server
  };
}

async function testRestAvailableTools() {
  const response = await makeRequest('GET', '/available-tools');
  return {
    statusCode: response.statusCode,
    toolCount: response.data.count,
    tools: response.data.tool_names
  };
}

async function testRestIdentifySpeakers() {
  const response = await makeRequest('POST', '/identify-speakers', {
    text: 'John: Hello everyone. Sarah: Hi John, how are you?',
    context: 'Team meeting'
  });

  return {
    statusCode: response.statusCode,
    speakers: response.data.data.speakers,
    confidence: response.data.data.confidence,
    method: response.data.data.identification_method
  };
}

async function testRestGenerateSummary() {
  const response = await makeRequest('POST', '/generate-summary', {
    transcript: 'We discussed the project timeline and assigned tasks.',
    meeting_id: 'test-meeting-123',
    meeting_title: 'Project Planning'
  });

  return {
    statusCode: response.statusCode,
    summary: response.data.data.executive_summary,
    participants: response.data.data.participants
  };
}

async function testRestExtractTasks() {
  const response = await makeRequest('POST', '/extract-tasks', {
    transcript: 'John needs to update the database. Sarah will review the code.',
    meeting_context: { participants: ['John', 'Sarah'] }
  });

  return {
    statusCode: response.statusCode,
    tasks: response.data.data.tasks,
    taskSummary: response.data.data.task_summary
  };
}

async function testRestGetSummary() {
  const meetingId = 'test-meeting-123';
  const response = await makeRequest('GET', `/get-summary/${meetingId}`);

  return {
    statusCode: response.statusCode,
    meetingId: response.data.data.meeting_id,
    speakers: response.data.data.speakers,
    participants: response.data.data.participants
  };
}

async function testRestMeetings() {
  const response = await makeRequest('GET', '/meetings');

  return {
    statusCode: response.statusCode,
    meetings: response.data.meetings,
    enhancedMeetings: response.data.enhanced_meetings
  };
}

async function testRestAnalytics() {
  const response = await makeRequest('GET', '/analytics');

  return {
    statusCode: response.statusCode,
    overview: response.data.overview,
    speakerAccuracy: response.data.speaker_identification.enhanced_accuracy
  };
}

async function testRestEnhancedAudioStatus() {
  const response = await makeRequest('GET', '/enhanced-audio-status');

  return {
    statusCode: response.statusCode,
    enhancedEnabled: response.data.enhanced_audio_enabled,
    participantSupport: response.data.participant_data_support,
    accuracy: response.data.speaker_identification_accuracy
  };
}

// Test runner functions
async function runWebSocketTests() {
  console.log('\n📡 WebSocket Tests');
  console.log('==================');

  try {
    const connectionResult = await testWebSocketConnection();
    logTest('websocket', 'Connection', true, 'Successfully connected to WebSocket server');
  } catch (error) {
    logTest('websocket', 'Connection', false, `Connection failed: ${error.message}`);
    return false;
  }

  try {
    const handshakeResult = await testWebSocketHandshake();
    logTest('websocket', 'Handshake', true,
      `Server version: ${handshakeResult.serverVersion}, Status: ${handshakeResult.status}`);
  } catch (error) {
    logTest('websocket', 'Handshake', false, `Handshake failed: ${error.message}`);
  }

  try {
    const audioResult = await testBasicAudioChunk();
    logTest('websocket', 'Basic Audio Chunk', true,
      `Transcribed: "${audioResult.text}", Confidence: ${audioResult.confidence}`);
  } catch (error) {
    logTest('websocket', 'Basic Audio Chunk', false, `Audio processing failed: ${error.message}`);
  }

  try {
    const enhancedResult = await testEnhancedAudioChunk();
    logTest('websocket', 'Enhanced Audio Chunk', true,
      `Speaker: ${enhancedResult.transcription.speaker}, Participants: ${enhancedResult.meetingUpdate.participant_count}`);
  } catch (error) {
    logTest('websocket', 'Enhanced Audio Chunk', false, `Enhanced processing failed: ${error.message}`);
  }

  try {
    const eventResult = await testMeetingEvent();
    logTest('websocket', 'Meeting Event', true,
      `Event: ${eventResult.eventType}, Status: ${eventResult.status}`);
  } catch (error) {
    logTest('websocket', 'Meeting Event', false, `Event handling failed: ${error.message}`);
  }

  return true;
}

async function runRestTests() {
  console.log('\n🌐 REST API Tests');
  console.log('=================');

  try {
    const healthResult = await testRestHealth();
    logTest('rest', 'Health Check', healthResult.statusCode === 200,
      `Status: ${healthResult.status}, Server: ${healthResult.server}`);
  } catch (error) {
    logTest('rest', 'Health Check', false, `Health check failed: ${error.message}`);
    return false;
  }

  try {
    const toolsResult = await testRestAvailableTools();
    logTest('rest', 'Available Tools', toolsResult.statusCode === 200,
      `Tools: ${toolsResult.toolCount}, Names: ${toolsResult.tools.join(', ')}`);
  } catch (error) {
    logTest('rest', 'Available Tools', false, `Tools check failed: ${error.message}`);
  }

  try {
    const speakersResult = await testRestIdentifySpeakers();
    logTest('rest', 'Identify Speakers', speakersResult.statusCode === 200,
      `Speakers: ${speakersResult.speakers.length}, Method: ${speakersResult.method}`);
  } catch (error) {
    logTest('rest', 'Identify Speakers', false, `Speaker identification failed: ${error.message}`);
  }

  try {
    const summaryResult = await testRestGenerateSummary();
    logTest('rest', 'Generate Summary', summaryResult.statusCode === 200,
      `Overview: ${summaryResult.summary.overview.substring(0, 50)}...`);
  } catch (error) {
    logTest('rest', 'Generate Summary', false, `Summary generation failed: ${error.message}`);
  }

  try {
    const tasksResult = await testRestExtractTasks();
    logTest('rest', 'Extract Tasks', tasksResult.statusCode === 200,
      `Tasks: ${tasksResult.tasks.length}, High priority: ${tasksResult.taskSummary.high_priority}`);
  } catch (error) {
    logTest('rest', 'Extract Tasks', false, `Task extraction failed: ${error.message}`);
  }

  try {
    const getSummaryResult = await testRestGetSummary();
    logTest('rest', 'Get Summary', getSummaryResult.statusCode === 200,
      `Meeting: ${getSummaryResult.meetingId}, Speakers: ${getSummaryResult.speakers.speakers.length}`);
  } catch (error) {
    logTest('rest', 'Get Summary', false, `Get summary failed: ${error.message}`);
  }

  try {
    const meetingsResult = await testRestMeetings();
    logTest('rest', 'Get Meetings', meetingsResult.statusCode === 200,
      `Meetings: ${meetingsResult.meetings.length}, Enhanced: ${meetingsResult.enhancedMeetings}`);
  } catch (error) {
    logTest('rest', 'Get Meetings', false, `Get meetings failed: ${error.message}`);
  }

  try {
    const analyticsResult = await testRestAnalytics();
    logTest('rest', 'Analytics', analyticsResult.statusCode === 200,
      `Total meetings: ${analyticsResult.overview.total_meetings}, Accuracy: ${analyticsResult.speakerAccuracy}`);
  } catch (error) {
    logTest('rest', 'Analytics', false, `Analytics failed: ${error.message}`);
  }

  try {
    const audioStatusResult = await testRestEnhancedAudioStatus();
    logTest('rest', 'Enhanced Audio Status', audioStatusResult.statusCode === 200,
      `Enhanced: ${audioStatusResult.enhancedEnabled}, Accuracy: ${audioStatusResult.accuracy}`);
  } catch (error) {
    logTest('rest', 'Enhanced Audio Status', false, `Audio status failed: ${error.message}`);
  }

  return true;
}

function printTestSummary() {
  console.log('\n📊 Test Results Summary');
  console.log('========================');

  console.log(`📡 WebSocket Tests: ${testResults.websocket.passed}/${testResults.websocket.passed + testResults.websocket.failed} passed`);
  console.log(`🌐 REST API Tests:  ${testResults.rest.passed}/${testResults.rest.passed + testResults.rest.failed} passed`);
  console.log(`🎯 Total:          ${testResults.total.passed}/${testResults.total.passed + testResults.total.failed} passed`);

  if (testResults.total.failed > 0) {
    console.log('\n❌ Failed Tests:');
    ['websocket', 'rest'].forEach(category => {
      testResults[category].tests
        .filter(test => !test.passed)
        .forEach(test => {
          console.log(`   [${category.toUpperCase()}] ${test.name}: ${test.details}`);
        });
    });
  }

  const successRate = Math.round((testResults.total.passed / (testResults.total.passed + testResults.total.failed)) * 100);

  if (successRate === 100) {
    console.log('\n🎉 All tests passed! Mock servers are working correctly.');
  } else if (successRate >= 80) {
    console.log(`\n✅ Most tests passed (${successRate}%). Mock servers are mostly functional.`);
  } else {
    console.log(`\n⚠️  Many tests failed (${successRate}% success). Check mock server configuration.`);
  }
}

// Main test execution
async function runAllTests() {
  const startTime = Date.now();

  console.log(`Testing servers at:`);
  console.log(`  WebSocket: ${config.websocketUrl}`);
  console.log(`  REST API:  ${config.restBaseUrl}`);
  console.log(`  Timeout:   ${config.timeout}ms\n`);

  // Run WebSocket tests
  const wsSuccess = await runWebSocketTests();

  // Small delay between test suites
  await delay(1000);

  // Run REST API tests
  const restSuccess = await runRestTests();

  // Print summary
  printTestSummary();

  const duration = Date.now() - startTime;
  console.log(`\n⏱️  Test duration: ${duration}ms`);

  // Exit with appropriate code
  const overallSuccess = testResults.total.failed === 0;
  process.exit(overallSuccess ? 0 : 1);
}

// Handle command line arguments
const args = process.argv.slice(2);

if (args.includes('--help') || args.includes('-h')) {
  console.log('Mock Servers Test Suite');
  console.log('=======================');
  console.log('');
  console.log('Usage: node test-mock-servers.js [options]');
  console.log('');
  console.log('Options:');
  console.log('  --help, -h       Show this help message');
  console.log('  --websocket-only Test only WebSocket server');
  console.log('  --rest-only      Test only REST API server');
  console.log('');
  console.log('Examples:');
  console.log('  node test-mock-servers.js              Run all tests');
  console.log('  node test-mock-servers.js --rest-only  Test only REST API');
  process.exit(0);
} else if (args.includes('--websocket-only')) {
  runWebSocketTests().then(() => {
    printTestSummary();
    process.exit(testResults.websocket.failed === 0 ? 0 : 1);
  });
} else if (args.includes('--rest-only')) {
  runRestTests().then(() => {
    printTestSummary();
    process.exit(testResults.rest.failed === 0 ? 0 : 1);
  });
} else {
  runAllTests();
}
