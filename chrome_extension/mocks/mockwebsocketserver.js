// mock-server.js - Simple WebSocket server for testing
const WebSocket = require('ws');

const PORT = 8081; // Changed from 8080 to avoid conflicts
const wss = new WebSocket.Server({ port: PORT });

console.log(`[Mock Server] WebSocket server running on port ${PORT}`);

wss.on('connection', (ws) => {
  console.log('[Mock Server] Client connected');

  ws.on('message', (data) => {
    try {
      const message = JSON.parse(data);
      console.log(`[Mock Server] Received: ${message.type}`);
      
      switch(message.type) {
        case 'HANDSHAKE':
          ws.send(JSON.stringify({
            type: 'HANDSHAKE_ACK',
            serverVersion: '1.0',
            status: 'ready'
          }));
          break;
          
        case 'AUDIO_CHUNK':
          // Mock transcription response
          setTimeout(() => {
            ws.send(JSON.stringify({
              type: 'TRANSCRIPTION_RESULT',
              data: {
                text: `Mock transcription for chunk ${Date.now()}`,
                confidence: 0.95,
                timestamp: message.timestamp
              }
            }));
          }, 100);
          break;
      }
    } catch (error) {
      console.error('[Mock Server] Error parsing message:', error);
    }
  });

  ws.on('close', () => {
    console.log('[Mock Server] Client disconnected');
  });
});