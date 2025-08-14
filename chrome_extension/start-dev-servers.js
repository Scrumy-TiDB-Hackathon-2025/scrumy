// start-dev-servers.js - Start both mock servers for development
const { spawn } = require('child_process');
const path = require('path');

console.log('🚀 Starting ScrumBot Development Servers...\n');

// Start WebSocket server
const wsServer = spawn('node', ['mocks/mockwebsocketserver.js'], {
  cwd: __dirname,
  stdio: 'inherit'
});

// Start REST API server
const restServer = spawn('node', ['mocks/mockrestserver.js'], {
  cwd: __dirname,
  stdio: 'inherit'
});

console.log('📡 Mock servers starting...');
console.log('   WebSocket: ws://localhost:8081/ws');
console.log('   REST API:  http://localhost:3002');
console.log('\n🔧 Extension configured for DEV mode');
console.log('   Load extension and test on Google Meet');
console.log('   Press Ctrl+C to stop all servers\n');

// Handle shutdown
process.on('SIGINT', () => {
  console.log('\n🛑 Shutting down development servers...');
  
  wsServer.kill('SIGINT');
  restServer.kill('SIGINT');
  
  setTimeout(() => {
    console.log('✅ Development servers stopped');
    process.exit(0);
  }, 1000);
});

// Handle server crashes
wsServer.on('close', (code) => {
  if (code !== 0) {
    console.error('❌ WebSocket server crashed with code', code);
  }
});

restServer.on('close', (code) => {
  if (code !== 0) {
    console.error('❌ REST API server crashed with code', code);
  }
});