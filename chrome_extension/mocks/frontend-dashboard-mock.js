// frontend-dashboard-mock.js - Mock server for frontend dashboard testing
const http = require("http");
const url = require("url");

const PORT = 3003;

// Mock data storage
let meetings = [];
let transcripts = [];
let participants = [];
let analytics = {};

// CORS headers
const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers":
    "Content-Type, Authorization, ngrok-skip-browser-warning",
  "Content-Type": "application/json",
};

// Initialize mock data
function initializeMockData() {
  // Mock meetings with enhanced participant data
  meetings = [
    {
      id: "meeting_001",
      title: "Sprint Planning Meeting",
      platform: "google-meet",
      created_at: "2025-01-08T10:00:00Z",
      updated_at: "2025-01-08T11:30:00Z",
      duration: "90 minutes",
      participant_count: 4,
      has_enhanced_data: true,
      summary_status: "completed",
      meeting_url: "https://meet.google.com/abc-def-ghi",
      host: "John Smith",
      status: "completed",
    },
    {
      id: "meeting_002",
      title: "Daily Standup",
      platform: "zoom",
      created_at: "2025-01-07T09:00:00Z",
      updated_at: "2025-01-07T09:30:00Z",
      duration: "30 minutes",
      participant_count: 6,
      has_enhanced_data: true,
      summary_status: "completed",
      meeting_url: "https://zoom.us/j/123456789",
      host: "Sarah Johnson",
      status: "completed",
    },
    {
      id: "meeting_003",
      title: "Architecture Review",
      platform: "teams",
      created_at: "2025-01-06T14:00:00Z",
      updated_at: "2025-01-06T15:00:00Z",
      duration: "60 minutes",
      participant_count: 3,
      has_enhanced_data: false,
      summary_status: "processing",
      meeting_url: "https://teams.microsoft.com/l/meetup-join/...",
      host: "Mike Chen",
      status: "processing",
    },
    {
      id: "meeting_004",
      title: "Client Demo Preparation",
      platform: "google-meet",
      created_at: "2025-01-05T16:00:00Z",
      updated_at: "2025-01-05T17:30:00Z",
      duration: "90 minutes",
      participant_count: 5,
      has_enhanced_data: true,
      summary_status: "completed",
      meeting_url: "https://meet.google.com/xyz-123-789",
      host: "Emily Davis",
      status: "completed",
    },
  ];

  // Mock participants with detailed metrics
  participants = [
    {
      id: "participant_001",
      name: "Christian Onyisi",
      email: "christian@example.com",
      avatar: "/avatars/christian.jpg",
      meetings_attended: 15,
      avg_participation_level: "high",
      total_speaking_time: "4.5 hours",
      tasks_assigned: 8,
      tasks_completed: 6,
      completion_rate: 0.75,
      engagement_score: 92,
      preferred_meeting_times: ["morning", "afternoon"],
      role: "Senior Developer",
      department: "Engineering",
    },
    {
      id: "participant_002",
      name: "John Smith",
      email: "john@example.com",
      avatar: "/avatars/john.jpg",
      meetings_attended: 20,
      avg_participation_level: "high",
      total_speaking_time: "6.2 hours",
      tasks_assigned: 12,
      tasks_completed: 10,
      completion_rate: 0.83,
      engagement_score: 95,
      preferred_meeting_times: ["morning"],
      role: "Team Lead",
      department: "Engineering",
    },
    {
      id: "participant_003",
      name: "Sarah Johnson",
      email: "sarah@example.com",
      avatar: "/avatars/sarah.jpg",
      meetings_attended: 12,
      avg_participation_level: "medium",
      total_speaking_time: "2.8 hours",
      tasks_assigned: 5,
      tasks_completed: 4,
      completion_rate: 0.80,
      engagement_score: 78,
      preferred_meeting_times: ["afternoon"],
      role: "Product Manager",
      department: "Product",
    },
    {
      id: "participant_004",
      name: "Mike Chen",
      email: "mike@example.com",
      avatar: "/avatars/mike.jpg",
      meetings_attended: 18,
      avg_participation_level: "high",
      total_speaking_time: "5.1 hours",
      tasks_assigned: 9,
      tasks_completed: 8,
      completion_rate: 0.89,
      engagement_score: 88,
      preferred_meeting_times: ["morning", "evening"],
      role: "Senior Developer",
      department: "Engineering",
    },
    {
      id: "participant_005",
      name: "Emily Davis",
      email: "emily@example.com",
      avatar: "/avatars/emily.jpg",
      meetings_attended: 14,
      avg_participation_level: "high",
      total_speaking_time: "3.9 hours",
      tasks_assigned: 7,
      tasks_completed: 6,
      completion_rate: 0.86,
      engagement_score: 91,
      preferred_meeting_times: ["afternoon", "evening"],
      role: "UX Designer",
      department: "Design",
    },
  ];

  // Initialize analytics data
  analytics = {
    overview: {
      total_meetings: 23,
      enhanced_meetings: 18,
      total_participants: participants.length,
      active_participants: 4,
      total_tasks_created: 45,
      tasks_completed: 38,
      completion_rate: 0.84,
      avg_meeting_duration: "42 minutes",
      total_speaking_time: "22.5 hours",
      enhanced_audio_usage: 0.78,
    },
    participation_trends: {
      daily_active_users: [
        { date: "2025-01-01", count: 4 },
        { date: "2025-01-02", count: 6 },
        { date: "2025-01-03", count: 5 },
        { date: "2025-01-04", count: 7 },
        { date: "2025-01-05", count: 8 },
        { date: "2025-01-06", count: 6 },
        { date: "2025-01-07", count: 7 },
        { date: "2025-01-08", count: 8 },
      ],
      weekly_meetings: [
        { week: "Week 1", meetings: 8, enhanced: 6 },
        { week: "Week 2", meetings: 10, enhanced: 8 },
        { week: "Week 3", meetings: 5, enhanced: 4 },
      ],
      engagement_levels: {
        high: 5,
        medium: 2,
        low: 1,
      },
    },
    platform_usage: {
      "google-meet": 12,
      zoom: 7,
      teams: 4,
    },
    speaker_identification: {
      enhanced_accuracy: 0.92,
      basic_accuracy: 0.67,
      participant_context_usage: 0.78,
      total_chunks_processed: 1247,
      enhanced_chunks: 973,
      fallback_chunks: 274,
    },
    task_analytics: {
      completion_rate: 0.84,
      avg_time_to_complete: "3.2 days",
      overdue_tasks: 3,
      upcoming_deadlines: 7,
      by_priority: {
        high: { total: 15, completed: 13 },
        medium: { total: 20, completed: 17 },
        low: { total: 10, completed: 8 },
      },
      by_assignee: participants.map((p) => ({
        name: p.name,
        assigned: p.tasks_assigned,
        completed: p.tasks_completed,
        completion_rate: p.completion_rate,
      })),
    },
    meeting_quality: {
      avg_duration: 42,
      avg_participants: 4.2,
      participation_balance_score: 0.85,
      decision_clarity_score: 0.78,
      follow_up_completion: 0.82,
    },
  };
}

const server = http.createServer((req, res) => {
  const parsedUrl = url.parse(req.url, true);
  const path = parsedUrl.pathname;
  const method = req.method;

  console.log(`[Frontend Mock] ${method} ${path}`);

  // Handle CORS preflight
  if (method === "OPTIONS") {
    res.writeHead(200, corsHeaders);
    res.end();
    return;
  }

  // Set CORS headers for all responses
  Object.keys(corsHeaders).forEach((key) => {
    res.setHeader(key, corsHeaders[key]);
  });

  // Route handlers
  switch (path) {
    case "/health":
      handleHealth(req, res);
      break;
    case "/get-meetings":
      handleGetMeetings(req, res);
      break;
    case "/meetings":
      handleMeetingsAPI(req, res, method);
      break;
    case "/participants":
      handleParticipantsAPI(req, res, method);
      break;
    case "/analytics":
      handleAnalyticsAPI(req, res);
      break;
    case "/analytics/overview":
      handleAnalyticsOverview(req, res);
      break;
    case "/analytics/participation":
      handleParticipationAnalytics(req, res);
      break;
    case "/analytics/tasks":
      handleTaskAnalytics(req, res);
      break;
    case "/enhanced-audio-status":
      handleEnhancedAudioStatus(req, res);
      break;
    default:
      if (path.startsWith("/get-summary/")) {
        handleGetSummary(req, res, parsedUrl);
      } else if (path.startsWith("/meetings/")) {
        handleMeetingDetails(req, res, parsedUrl);
      } else if (path.startsWith("/participants/")) {
        handleParticipantDetails(req, res, parsedUrl);
      } else {
        handle404(req, res);
      }
  }
});

function handleHealth(req, res) {
  res.writeHead(200);
  res.end(
    JSON.stringify({
      status: "healthy",
      server: "frontend-dashboard-mock",
      timestamp: new Date().toISOString(),
      version: "1.0.0",
      enhanced_features: true,
    })
  );
}

function handleGetMeetings(req, res) {
  // Frontend expects this format
  res.writeHead(200);
  res.end(
    JSON.stringify({
      meetings: meetings,
      total: meetings.length,
      enhanced_meetings: meetings.filter((m) => m.has_enhanced_data).length,
      status: "success",
    })
  );
}

function handleMeetingsAPI(req, res, method) {
  if (method === "GET") {
    const enhancedMeetings = meetings.map((meeting) => ({
      ...meeting,
      participants_preview: participants.slice(0, 3).map((p) => ({
        id: p.id,
        name: p.name,
        avatar: p.avatar,
      })),
      recent_activity: {
        last_transcript: "We discussed the sprint goals and timeline...",
        last_speaker: "John Smith",
        last_updated: meeting.updated_at,
      },
      metrics: {
        engagement_score: Math.floor(Math.random() * 30 + 70),
        decision_count: Math.floor(Math.random() * 5 + 1),
        task_count: Math.floor(Math.random() * 8 + 2),
        speaking_balance: Math.random() * 0.3 + 0.7,
      },
    }));

    res.writeHead(200);
    res.end(
      JSON.stringify({
        meetings: enhancedMeetings,
        total: enhancedMeetings.length,
        enhanced_count: enhancedMeetings.filter((m) => m.has_enhanced_data)
          .length,
        pagination: {
          page: 1,
          per_page: 20,
          total_pages: 1,
        },
      })
    );
  }
}

function handleMeetingDetails(req, res, parsedUrl) {
  const meetingId = parsedUrl.pathname.split("/").pop();
  const meeting = meetings.find((m) => m.id === meetingId);

  if (!meeting) {
    res.writeHead(404);
    res.end(JSON.stringify({ error: "Meeting not found" }));
    return;
  }

  const detailedMeeting = {
    ...meeting,
    participants: participants.slice(0, meeting.participant_count).map((p) => ({
      ...p,
      speaking_time: `${Math.floor(Math.random() * 15 + 5)} minutes`,
      engagement_level: ["high", "medium", "low"][Math.floor(Math.random() * 3)],
      key_contributions: [
        "Provided technical insights",
        "Asked clarifying questions",
        "Summarized action items",
      ].slice(0, Math.floor(Math.random() * 3 + 1)),
    })),
    transcript_summary: {
      total_words: Math.floor(Math.random() * 2000 + 1000),
      key_topics: ["Sprint Planning", "Task Assignment", "Timeline Discussion"],
      sentiment_analysis: {
        positive: 0.7,
        neutral: 0.25,
        negative: 0.05,
      },
    },
    decisions: [
      {
        id: "decision_1",
        text: "Implement OAuth 2.0 authentication by end of sprint",
        confidence: 0.95,
        participants_involved: ["John Smith", "Christian Onyisi"],
      },
      {
        id: "decision_2",
        text: "Schedule weekly architecture reviews",
        confidence: 0.87,
        participants_involved: ["Mike Chen", "Sarah Johnson"],
      },
    ],
    tasks: [
      {
        id: "task_1",
        title: "Set up OAuth providers",
        assignee: "Christian Onyisi",
        due_date: "2025-01-15",
        priority: "high",
        status: "in_progress",
      },
      {
        id: "task_2",
        title: "Update API documentation",
        assignee: "John Smith",
        due_date: "2025-01-12",
        priority: "medium",
        status: "pending",
      },
    ],
  };

  res.writeHead(200);
  res.end(JSON.stringify(detailedMeeting));
}

function handleGetSummary(req, res, parsedUrl) {
  const meetingId = parsedUrl.pathname.split("/").pop();
  console.log(`[Frontend Mock] Get summary for meeting: ${meetingId}`);

  const meeting = meetings.find((m) => m.id === meetingId) || meetings[0];

  setTimeout(() => {
    res.writeHead(200);
    res.end(
      JSON.stringify({
        status: "completed",
        data: {
          meeting_id: meetingId,
          meeting_title: meeting.title,
          platform: meeting.platform,
          created_at: meeting.created_at,
          duration: meeting.duration,
          speakers: {
            speakers: [
              {
                id: "speaker_1",
                name: "Christian Onyisi",
                participant_id: "participant_001",
                segments: [
                  "I can work on the OAuth implementation",
                  "The API endpoints should be straightforward",
                ],
                total_words: 125,
                characteristics: "Technical contributor, detail-oriented",
                confidence: 0.92,
                speaking_time: "8 minutes",
              },
              {
                id: "speaker_2",
                name: "John Smith",
                participant_id: "participant_002",
                segments: [
                  "Let's prioritize the authentication feature",
                  "We should schedule weekly reviews",
                ],
                total_words: 98,
                characteristics: "Team lead, strategic thinking",
                confidence: 0.89,
                speaking_time: "12 minutes",
              },
            ],
            confidence: 0.91,
            total_speakers: 2,
            identification_method: "enhanced_participant_context",
          },
          summary: {
            meeting_title: meeting.title,
            executive_summary: {
              overview:
                "Team discussed sprint priorities, assigned tasks, and established timeline for authentication feature development.",
              key_outcomes: [
                "OAuth 2.0 implementation prioritized",
                "Weekly architecture reviews scheduled",
                "Clear task assignments established",
              ],
              business_impact: "Critical foundation for user management system",
              urgency_level: "high",
              follow_up_required: true,
            },
            key_decisions: {
              decisions: [
                {
                  decision: "Implement OAuth 2.0 with Google and GitHub",
                  rationale: "Industry standard for secure authentication",
                  impact: "Enables secure user access and integrations",
                  timeline: "Complete by sprint end",
                  confidence: 0.95,
                },
              ],
              total_decisions: 1,
              consensus_level: "unanimous",
            },
            participants: {
              participants: [
                {
                  name: "Christian Onyisi",
                  role: "Senior Developer",
                  participation_level: "high",
                  key_contributions: [
                    "Technical implementation details",
                    "API design suggestions",
                  ],
                  speaking_time: "8 minutes",
                  engagement_score: 92,
                },
                {
                  name: "John Smith",
                  role: "Team Lead",
                  participation_level: "high",
                  key_contributions: [
                    "Strategic planning",
                    "Meeting facilitation",
                  ],
                  speaking_time: "12 minutes",
                  engagement_score: 95,
                },
              ],
              total_participants: 2,
              participation_balance: "balanced",
              meeting_leader: "John Smith",
            },
          },
          tasks: [
            {
              id: "task_1",
              title: "Implement OAuth 2.0 authentication",
              description: "Set up Google and GitHub OAuth providers",
              assignee: "Christian Onyisi",
              due_date: "2025-01-15",
              priority: "high",
              status: "pending",
              category: "action_item",
              estimated_hours: 16,
              dependencies: ["API framework setup"],
            },
            {
              id: "task_2",
              title: "Schedule weekly architecture reviews",
              description: "Establish recurring meetings for system design",
              assignee: "John Smith",
              due_date: "2025-01-10",
              priority: "medium",
              status: "pending",
              category: "process",
              estimated_hours: 2,
            },
          ],
          participants: participants.slice(0, meeting.participant_count).map((p) => ({
            ...p,
            participation_metrics: {
              speaking_time_percent: Math.floor(Math.random() * 30 + 20),
              engagement_level: "high",
              questions_asked: Math.floor(Math.random() * 5 + 1),
              contributions_made: Math.floor(Math.random() * 8 + 2),
              sentiment_score: Math.random() * 0.4 + 0.6,
            },
          })),
          enhanced_features: {
            participant_mapping_accuracy: 0.92,
            speaker_identification_method: "enhanced_participant_context",
            audio_quality_score: 0.89,
            transcription_accuracy: 0.94,
          },
        },
      })
    );
  }, 300 + Math.random() * 500);
}

function handleParticipantsAPI(req, res, method) {
  if (method === "GET") {
    res.writeHead(200);
    res.end(
      JSON.stringify({
        participants: participants,
        total: participants.length,
        active_participants: participants.filter(
          (p) => p.avg_participation_level === "high"
        ).length,
        stats: {
          total_meetings: participants.reduce((sum, p) => sum + p.meetings_attended, 0),
          total_tasks: participants.reduce((sum, p) => sum + p.tasks_assigned, 0),
          avg_completion_rate: participants.reduce((sum, p) => sum + p.completion_rate, 0) / participants.length,
          avg_engagement: participants.reduce((sum, p) => sum + p.engagement_score, 0) / participants.length,
        },
      })
    );
  }
}

function handleParticipantDetails(req, res, parsedUrl) {
  const participantId = parsedUrl.pathname.split("/").pop();
  const participant = participants.find((p) => p.id === participantId);

  if (!participant) {
    res.writeHead(404);
    res.end(JSON.stringify({ error: "Participant not found" }));
    return;
  }

  const detailedParticipant = {
    ...participant,
    recent_meetings: meetings.slice(0, 3).map((m) => ({
      id: m.id,
      title: m.title,
      date: m.created_at,
      duration: m.duration,
      participation_score: Math.floor(Math.random() * 30 + 70),
    })),
    task_history: [
      {
        id: "task_001",
        title: "API Integration",
        status: "completed",
        completed_date: "2025-01-07",
        duration: "3 days",
      },
      {
        id: "task_002",
        title: "Database Schema Update",
        status: "in_progress",
        started_date: "2025-01-06",
        estimated_completion: "2025-01-09",
      },
    ],
    performance_trends: {
      engagement_history: [
        { month: "Nov", score: 85 },
        { month: "Dec", score: 89 },
        { month: "Jan", score: participant.engagement_score },
      ],
      task_completion_trend: [
        { month: "Nov", rate: 0.78 },
        { month: "Dec", rate: 0.82 },
        { month: "Jan", rate: participant.completion_rate },
      ],
    },
  };

  res.writeHead(200);
  res.end(JSON.stringify(detailedParticipant));
}

function handleAnalyticsAPI(req, res) {
  res.writeHead(200);
  res.end(JSON.stringify(analytics));
}

function handleAnalyticsOverview(req, res) {
  res.writeHead(200);
  res.end(JSON.stringify(analytics.overview));
}

function handleParticipationAnalytics(req, res) {
  res.writeHead(200);
  res.end(
    JSON.stringify({
      trends: analytics.participation_trends,
      participant_stats: participants.map((p) => ({
        id: p.id,
        name: p.name,
        engagement_score: p.engagement_score,
        participation_level: p.avg_participation_level,
        meetings_attended: p.meetings_attended,
      })),
    })
  );
}

function handleTaskAnalytics(req, res) {
  res.writeHead(200);
  res.end(JSON.stringify(analytics.task_analytics));
}

function handleEnhancedAudioStatus(req, res) {
  console.log(`[Frontend Mock] Enhanced audio status check`);

  res.writeHead(200);
  res.end(
    JSON.stringify({
      enhanced_audio_enabled: true,
      participant_data_support: true,
      speaker_identification_accuracy: analytics.speaker_identification.enhanced_accuracy,
      total_enhanced_chunks_processed: analytics.speaker_identification.enhanced_chunks,
      participant_mapping_success_rate: 0.89,
      last_enhanced_chunk: new Date().toISOString(),
      supported_platforms: ["google-meet", "zoom", "teams"],
      features: {
        participant_tracking: true,
        speaker_attribution: true,
        engagement_metrics: true,
        real_time_updates: true,
        sentiment_analysis: true,
      },
      system_health: {
        websocket_connections: 12,
        active_meetings: 3,
        processing_queue: 0,
        error_rate: 0.02,
      },
    })
  );
}

function handle404(req, res) {
  res.writeHead(404);
  res.end(
    JSON.stringify({
      error: "Not found",
      available_endpoints: [
        "/health",
        "/get-meetings",
        "/meetings",
        "/meetings/{id}",
        "/participants",
        "/participants/{id}",
        "/analytics",
        "/analytics/overview",
        "/analytics/participation",
        "/analytics/tasks",
        "/get-summary/{meeting_id}",
        "/enhanced-audio-status",
      ],
    })
  );
}

// Initialize mock data on startup
initializeMockData();

server.listen(PORT, () => {
  console.log(`[Frontend Dashboard Mock] Server running on http://localhost:${PORT}`);
  console.log("Available endpoints:");
  console.log("  GET  /health");
  console.log("  GET  /get-meetings");
  console.log("  GET  /meetings");
  console.log("  GET  /meetings/{id}");
  console.log("  GET  /participants");
  console.log("  GET  /participants/{id}");
  console.log("  GET  /analytics");
  console.log("  GET  /analytics/overview");
  console.log("  GET  /analytics/participation");
  console.log("  GET  /analytics/tasks");
  console.log("  GET  /get-summary/{meeting_id}");
  console.log("  GET  /enhanced-audio-status");
  console.log(`\nMock data initialized:`);
  console.log(`  - ${meetings.length} meetings`);
  console.log(`  - ${participants.length} participants`);
  console.log(`  - Enhanced features enabled`);
});

// Graceful shutdown
process.on("SIGINT", () => {
  console.log("\n[Frontend Dashboard Mock] Shutting down...");
  server.close(() => {
    console.log("[Frontend Dashboard Mock] Server closed");
    process.exit(0);
  });
});
