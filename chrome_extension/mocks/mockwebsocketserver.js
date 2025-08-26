// mock-websocket-server.js - Enhanced WebSocket server for testing with participant data
const WebSocket = require("ws");

const PORT = 8081; // Changed from 8080 to avoid conflicts
const wss = new WebSocket.Server({ port: PORT });

console.log(`[Mock Server] Enhanced WebSocket server running on port ${PORT}`);
console.log(
  `[Mock Server] Supporting: HANDSHAKE, AUDIO_CHUNK, AUDIO_CHUNK_ENHANCED, MEETING_EVENT`,
);

// Mock data for enhanced responses
const mockParticipants = [
  {
    id: "participant_1",
    name: "Christian Onyisi",
    platform_id: "google_meet_user_123",
    status: "active",
    is_host: false,
  },
  {
    id: "participant_2",
    name: "John Smith",
    platform_id: "google_meet_user_456",
    status: "active",
    is_host: true,
  },
  {
    id: "participant_3",
    name: "Sarah Johnson",
    platform_id: "google_meet_user_789",
    status: "active",
    is_host: false,
  },
];

const mockTranscriptions = [
  "Let's start the meeting and review our progress.",
  "I think we should focus on the authentication feature first.",
  "The database integration is working well so far.",
  "We need to schedule a follow-up meeting next week.",
  "Great work everyone, we're making good progress.",
  "Christian: I'll work on the API endpoints.",
  "John: That sounds good to me.",
  "Sarah: I can help with the testing.",
];

let meetingSession = {
  id: null,
  participants: [],
  chunkCount: 0,
};

wss.on("connection", (ws) => {
  console.log("[Mock Server] Client connected");

  ws.on("message", (data) => {
    try {
      const message = JSON.parse(data);
      console.log(`[Mock Server] Received: ${message.type}`);

      switch (message.type) {
        case "HANDSHAKE":
          handleHandshake(ws, message);
          break;

        case "AUDIO_CHUNK":
          handleBasicAudioChunk(ws, message);
          break;

        case "AUDIO_CHUNK_ENHANCED":
          handleEnhancedAudioChunk(ws, message);
          break;

        case "MEETING_EVENT":
          handleMeetingEvent(ws, message);
          break;

        default:
          console.log(`[Mock Server] Unknown message type: ${message.type}`);
          ws.send(
            JSON.stringify({
              type: "ERROR",
              error: `Unknown message type: ${message.type}`,
            }),
          );
      }
    } catch (error) {
      console.error("[Mock Server] Error parsing message:", error);
      ws.send(
        JSON.stringify({
          type: "ERROR",
          error: "Invalid JSON message",
        }),
      );
    }
  });

  ws.on("close", () => {
    console.log("[Mock Server] Client disconnected");
  });
});

function handleHandshake(ws, message) {
  console.log(`[Mock Server] Handshake from: ${message.clientType}`);

  ws.send(
    JSON.stringify({
      type: "HANDSHAKE_ACK",
      serverVersion: "1.0",
      status: "ready",
      timestamp: new Date().toISOString(),
      capabilities: [
        "enhanced-audio",
        "participant-tracking",
        "speaker-identification",
      ],
    }),
  );
}

function handleBasicAudioChunk(ws, message) {
  console.log(`[Mock Server] Processing basic audio chunk`);
  meetingSession.chunkCount++;

  // Mock transcription response (legacy format)
  setTimeout(
    () => {
      const randomText =
        mockTranscriptions[
          Math.floor(Math.random() * mockTranscriptions.length)
        ];

      ws.send(
        JSON.stringify({
          type: "transcription_result",
          data: {
            text: randomText,
            confidence: 0.85 + Math.random() * 0.15,
            timestamp: message.timestamp || new Date().toISOString(),
            speaker: "Unknown Speaker",
          },
        }),
      );
    },
    100 + Math.random() * 200,
  );
}

function handleEnhancedAudioChunk(ws, message) {
  console.log(
    `[Mock Server] Processing enhanced audio chunk with ${message.participants?.length || 0} participants`,
  );

  // Update session with participant data
  if (message.participants) {
    meetingSession.participants = message.participants;
    meetingSession.id = `${message.platform}_${Date.now()}`;

    console.log(`[Mock Server] Updated session with participants:`);
    message.participants.forEach((p) => {
      console.log(`  - ${p.name} (${p.id}) ${p.is_host ? "[HOST]" : ""}`);
    });
  }

  meetingSession.chunkCount++;

  // Mock enhanced transcription with speaker attribution
  setTimeout(
    () => {
      const randomText =
        mockTranscriptions[
          Math.floor(Math.random() * mockTranscriptions.length)
        ];
      const participants = message.participants || [];
      const randomParticipant =
        participants.length > 0
          ? participants[Math.floor(Math.random() * participants.length)]
          : { id: "unknown", name: "Unknown Speaker" };

      // Send basic format for compatibility
      ws.send(
        JSON.stringify({
          type: "transcription_result",
          data: {
            text: randomText,
            confidence: 0.9 + Math.random() * 0.1,
            timestamp: message.timestamp || new Date().toISOString(),
            speaker: randomParticipant.name,
          },
        }),
      );

      // Send enhanced format with additional data
      ws.send(
        JSON.stringify({
          type: "TRANSCRIPTION_RESULT",
          data: {
            text: randomText,
            confidence: 0.9 + Math.random() * 0.1,
            timestamp: message.timestamp || new Date().toISOString(),
            speaker: randomParticipant.name,
            speaker_id: randomParticipant.id,
            speaker_confidence: 0.85 + Math.random() * 0.15,
            meetingId: meetingSession.id,
            chunkId: meetingSession.chunkCount,
            speakers: [
              {
                id: randomParticipant.id,
                name: randomParticipant.name,
                segments: [randomText],
                confidence: 0.9 + Math.random() * 0.1,
              },
            ],
          },
        }),
      );

      // Send meeting update
      ws.send(
        JSON.stringify({
          type: "MEETING_UPDATE",
          data: {
            meetingId: meetingSession.id,
            participants: participants.map((p) => p.name),
            participant_data: participants,
            participant_count: participants.length,
            platform: message.platform,
            latestTranscript: randomText,
            timestamp: new Date().toISOString(),
          },
        }),
      );
    },
    150 + Math.random() * 300,
  );
}

function handleMeetingEvent(ws, message) {
  console.log(`[Mock Server] Meeting event: ${message.eventType}`);

  switch (message.eventType) {
    case "meeting_started":
      ws.send(
        JSON.stringify({
          type: "MEETING_EVENT_ACK",
          eventType: message.eventType,
          status: "acknowledged",
          timestamp: new Date().toISOString(),
        }),
      );
      break;

    case "meeting_ended":
      // Mock meeting summary
      setTimeout(() => {
        ws.send(
          JSON.stringify({
            type: "MEETING_SUMMARY",
            data: {
              meetingId: meetingSession.id,
              summary: {
                overview: "Mock meeting completed successfully",
                key_outcomes: [
                  "Enhanced audio processing tested",
                  "Participant data validated",
                ],
              },
              tasks: [
                {
                  id: "task_1",
                  title: "Review meeting outcomes",
                  assignee:
                    meetingSession.participants[0]?.name || "Unassigned",
                  priority: "medium",
                },
              ],
              participants: meetingSession.participants.map((p) => p.name),
              totalChunks: meetingSession.chunkCount,
              generatedAt: new Date().toISOString(),
            },
          }),
        );
      }, 500);
      break;

    case "participant_joined":
    case "participant_left":
      ws.send(
        JSON.stringify({
          type: "MEETING_EVENT_ACK",
          eventType: message.eventType,
          status: "acknowledged",
          participantUpdate: message.data?.participant,
          timestamp: new Date().toISOString(),
        }),
      );
      break;
  }
}

// Graceful shutdown
process.on("SIGINT", () => {
  console.log("\n[Mock Server] Shutting down WebSocket server...");
  wss.close(() => {
    console.log("[Mock Server] Server closed");
    process.exit(0);
  });
});
