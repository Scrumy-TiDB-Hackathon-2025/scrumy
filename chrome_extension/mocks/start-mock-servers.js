#!/usr/bin/env node

/**
 * Mock Servers Starter Script
 * Starts both WebSocket and REST mock servers for Chrome extension testing
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

console.log('🚀 Starting ScrumBot Mock Servers');
console.log('=====================================');

// Configuration
const config = {
  websocketPort: 8081,
  restPort: 3002,
  logFile: path.join(__dirname, 'mock-servers.log'),
  pidFile: path.join(__dirname, 'mock-servers.pid')
};

// Store process PIDs for cleanup
const processes = [];
const pids = [];

// Cleanup function
function cleanup() {
  console.log('\n🛑 Shutting down mock servers...');

  processes.forEach((proc, index) => {
    if (proc && !proc.killed) {
      console.log(`   Terminating ${index === 0 ? 'WebSocket' : 'REST'} server (PID: ${proc.pid})`);
      proc.kill('SIGINT');
    }
  });

  // Remove PID file
  if (fs.existsSync(config.pidFile)) {
    fs.unlinkSync(config.pidFile);
  }

  console.log('✅ Mock servers shut down complete');
  process.exit(0);
}

// Handle process termination
process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
process.on('exit', cleanup);

// Start WebSocket mock server
function startWebSocketServer() {
  return new Promise((resolve, reject) => {
    console.log(`📡 Starting WebSocket mock server on port ${config.websocketPort}...`);

    const wsServer = spawn('node', ['mockwebsocketserver.js'], {
      cwd: __dirname,
      stdio: ['pipe', 'pipe', 'pipe']
    });

    processes.push(wsServer);
    pids.push(wsServer.pid);

    wsServer.stdout.on('data', (data) => {
      const message = data.toString().trim();
      if (message) {
        console.log(`[WS] ${message}`);
      }

      if (message.includes('Enhanced WebSocket server running')) {
        resolve(wsServer);
      }
    });

    wsServer.stderr.on('data', (data) => {
      console.error(`[WS Error] ${data.toString().trim()}`);
    });

    wsServer.on('error', (error) => {
      console.error(`❌ WebSocket server failed to start: ${error.message}`);
      reject(error);
    });

    wsServer.on('exit', (code) => {
      if (code !== 0 && code !== null) {
        console.error(`❌ WebSocket server exited with code ${code}`);
        reject(new Error(`WebSocket server exit code: ${code}`));
      }
    });

    // Timeout after 10 seconds
    setTimeout(() => {
      reject(new Error('WebSocket server start timeout'));
    }, 10000);
  });
}

// Start REST mock server
function startRestServer() {
  return new Promise((resolve, reject) => {
    console.log(`🌐 Starting REST mock server on port ${config.restPort}...`);

    const restServer = spawn('node', ['mockrestserver.js'], {
      cwd: __dirname,
      stdio: ['pipe', 'pipe', 'pipe']
    });

    processes.push(restServer);
    pids.push(restServer.pid);

    restServer.stdout.on('data', (data) => {
      const message = data.toString().trim();
      if (message) {
        console.log(`[REST] ${message}`);
      }

      if (message.includes('Enhanced REST API running')) {
        resolve(restServer);
      }
    });

    restServer.stderr.on('data', (data) => {
      console.error(`[REST Error] ${data.toString().trim()}`);
    });

    restServer.on('error', (error) => {
      console.error(`❌ REST server failed to start: ${error.message}`);
      reject(error);
    });

    restServer.on('exit', (code) => {
      if (code !== 0 && code !== null) {
        console.error(`❌ REST server exited with code ${code}`);
        reject(new Error(`REST server exit code: ${code}`));
      }
    });

    // Timeout after 10 seconds
    setTimeout(() => {
      reject(new Error('REST server start timeout'));
    }, 10000);
  });
}

// Check if servers are already running
function checkExistingServers() {
  return new Promise((resolve) => {
    const net = require('net');
    let checks = 0;
    let results = { ws: false, rest: false };

    function checkComplete() {
      checks++;
      if (checks === 2) {
        resolve(results);
      }
    }

    // Check WebSocket port
    const wsSocket = new net.Socket();
    wsSocket.setTimeout(1000);

    wsSocket.on('connect', () => {
      results.ws = true;
      wsSocket.destroy();
      checkComplete();
    });

    wsSocket.on('error', () => {
      results.ws = false;
      checkComplete();
    });

    wsSocket.on('timeout', () => {
      results.ws = false;
      wsSocket.destroy();
      checkComplete();
    });

    wsSocket.connect(config.websocketPort, 'localhost');

    // Check REST port
    const restSocket = new net.Socket();
    restSocket.setTimeout(1000);

    restSocket.on('connect', () => {
      results.rest = true;
      restSocket.destroy();
      checkComplete();
    });

    restSocket.on('error', () => {
      results.rest = false;
      checkComplete();
    });

    restSocket.on('timeout', () => {
      results.rest = false;
      restSocket.destroy();
      checkComplete();
    });

    restSocket.connect(config.restPort, 'localhost');
  });
}

// Save PIDs to file
function savePids() {
  const pidData = {
    timestamp: new Date().toISOString(),
    pids: pids,
    ports: {
      websocket: config.websocketPort,
      rest: config.restPort
    }
  };

  fs.writeFileSync(config.pidFile, JSON.stringify(pidData, null, 2));
}

// Main startup function
async function startServers() {
  try {
    // Check for existing servers
    console.log('🔍 Checking for existing servers...');
    const existing = await checkExistingServers();

    if (existing.ws && existing.rest) {
      console.log('⚠️  Both servers already running!');
      console.log(`   WebSocket: ws://localhost:${config.websocketPort}`);
      console.log(`   REST API:  http://localhost:${config.restPort}`);
      console.log('   Use "npm run stop-mocks" to stop existing servers first.');
      process.exit(1);
    }

    if (existing.ws) {
      console.log(`⚠️  WebSocket server already running on port ${config.websocketPort}`);
      process.exit(1);
    }

    if (existing.rest) {
      console.log(`⚠️  REST server already running on port ${config.restPort}`);
      process.exit(1);
    }

    // Start servers
    const wsServer = await startWebSocketServer();
    const restServer = await startRestServer();

    // Save PIDs for cleanup
    savePids();

    console.log('\n✅ Mock servers started successfully!');
    console.log('=====================================');
    console.log(`📡 WebSocket Server: ws://localhost:${config.websocketPort}`);
    console.log(`🌐 REST API Server:  http://localhost:${config.restPort}`);
    console.log('\n📚 Available REST Endpoints:');
    console.log('   GET  /health');
    console.log('   POST /save-transcript');
    console.log('   GET  /get-meetings');
    console.log('   POST /transcribe');
    console.log('   POST /identify-speakers');
    console.log('   POST /generate-summary');
    console.log('   POST /extract-tasks');
    console.log('   POST /process-transcript-with-tools');
    console.log('   GET  /available-tools');
    console.log('   GET  /get-summary/{meeting_id}');
    console.log('   GET  /meetings');
    console.log('   GET  /participants');
    console.log('   GET  /analytics');
    console.log('   GET  /enhanced-audio-status');

    console.log('\n🎯 WebSocket Message Types:');
    console.log('   - HANDSHAKE');
    console.log('   - AUDIO_CHUNK (basic)');
    console.log('   - AUDIO_CHUNK_ENHANCED (with participant data)');
    console.log('   - MEETING_EVENT');

    console.log('\n📝 Testing Commands:');
    console.log('   Test WebSocket: npm run test-websocket');
    console.log('   Test REST API:  npm run test-rest');
    console.log('   Stop servers:   npm run stop-mocks');

    console.log('\n🔄 Servers running... Press Ctrl+C to stop');

    // Keep the process alive
    setInterval(() => {
      // Health check every 30 seconds
      processes.forEach((proc, index) => {
        if (proc.killed) {
          console.log(`⚠️  ${index === 0 ? 'WebSocket' : 'REST'} server process died`);
        }
      });
    }, 30000);

  } catch (error) {
    console.error(`❌ Failed to start mock servers: ${error.message}`);
    cleanup();
    process.exit(1);
  }
}

// Display help
function showHelp() {
  console.log('ScrumBot Mock Servers Starter');
  console.log('============================');
  console.log('');
  console.log('Usage: node start-mock-servers.js [options]');
  console.log('');
  console.log('Options:');
  console.log('  --help, -h     Show this help message');
  console.log('  --status, -s   Check server status');
  console.log('  --stop         Stop running servers');
  console.log('');
  console.log('Examples:');
  console.log('  node start-mock-servers.js         Start both servers');
  console.log('  node start-mock-servers.js --status Check if servers are running');
  console.log('  node start-mock-servers.js --stop   Stop all running servers');
}

// Check server status
async function checkStatus() {
  console.log('🔍 Checking mock server status...');

  const existing = await checkExistingServers();

  console.log(`📡 WebSocket Server (port ${config.websocketPort}): ${existing.ws ? '🟢 Running' : '🔴 Stopped'}`);
  console.log(`🌐 REST API Server (port ${config.restPort}):  ${existing.rest ? '🟢 Running' : '🔴 Stopped'}`);

  if (fs.existsSync(config.pidFile)) {
    try {
      const pidData = JSON.parse(fs.readFileSync(config.pidFile, 'utf8'));
      console.log(`📋 PID File: ${pidData.pids.join(', ')} (${pidData.timestamp})`);
    } catch (error) {
      console.log('📋 PID File: Invalid or corrupted');
    }
  } else {
    console.log('📋 PID File: Not found');
  }
}

// Stop servers
function stopServers() {
  console.log('🛑 Stopping mock servers...');

  if (fs.existsSync(config.pidFile)) {
    try {
      const pidData = JSON.parse(fs.readFileSync(config.pidFile, 'utf8'));

      pidData.pids.forEach((pid, index) => {
        try {
          process.kill(pid, 'SIGTERM');
          console.log(`   Stopped ${index === 0 ? 'WebSocket' : 'REST'} server (PID: ${pid})`);
        } catch (error) {
          console.log(`   PID ${pid} not found or already stopped`);
        }
      });

      fs.unlinkSync(config.pidFile);
      console.log('✅ Mock servers stopped');

    } catch (error) {
      console.error('❌ Error stopping servers:', error.message);
    }
  } else {
    console.log('⚠️  No PID file found. Servers may not be running.');
  }
}

// Parse command line arguments
const args = process.argv.slice(2);

if (args.includes('--help') || args.includes('-h')) {
  showHelp();
  process.exit(0);
} else if (args.includes('--status') || args.includes('-s')) {
  checkStatus().then(() => process.exit(0));
} else if (args.includes('--stop')) {
  stopServers();
  process.exit(0);
} else {
  // Start servers
  startServers();
}
