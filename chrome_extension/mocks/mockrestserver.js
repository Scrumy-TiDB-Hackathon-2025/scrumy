// mock-rest-server.js - Simple REST API server for testing
const http = require('http');
const url = require('url');

const PORT = 3002;

// Mock data storage
let meetings = [];
let transcripts = [];

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, ngrok-skip-browser-warning',
  'Content-Type': 'application/json'
};

const server = http.createServer((req, res) => {
  const parsedUrl = url.parse(req.url, true);
  const path = parsedUrl.pathname;
  const method = req.method;

  console.log(`[Mock REST] ${method} ${path}`);

  // Handle CORS preflight
  if (method === 'OPTIONS') {
    res.writeHead(200, corsHeaders);
    res.end();
    return;
  }

  // Set CORS headers for all responses
  Object.keys(corsHeaders).forEach(key => {
    res.setHeader(key, corsHeaders[key]);
  });

  // Routes
  switch (path) {
    case '/health':
      handleHealth(req, res);
      break;
    case '/save-transcript':
      handleSaveTranscript(req, res);
      break;
    case '/get-meetings':
      handleGetMeetings(req, res);
      break;
    case '/transcribe':
      handleTranscribe(req, res);
      break;
    case '/get-model-config':
      handleGetModelConfig(req, res);
      break;
    case '/process-transcript':
      handleProcessTranscript(req, res);
      break;
    // Epic B endpoints
    case '/identify-speakers':
      handleIdentifySpeakers(req, res);
      break;
    case '/generate-summary':
      handleGenerateSummary(req, res);
      break;
    case '/extract-tasks':
      handleExtractTasks(req, res);
      break;
    case '/process-transcript-with-tools':
      handleProcessTranscriptWithTools(req, res);
      break;
    case '/available-tools':
      handleAvailableTools(req, res);
      break;
    default:
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ 
        error: 'Not found',
        available_endpoints: [
          '/health', '/save-transcript', '/get-meetings', '/transcribe',
          '/identify-speakers', '/generate-summary', '/extract-tasks',
          '/process-transcript-with-tools', '/available-tools'
        ]
      }));
  }
});

function handleHealth(req, res) {
  res.writeHead(200);
  res.end(JSON.stringify({ 
    status: 'healthy',
    server: 'mock-rest-api',
    timestamp: new Date().toISOString()
  }));
}

function handleSaveTranscript(req, res) {
  let body = '';
  req.on('data', chunk => {
    body += chunk.toString();
  });
  
  req.on('end', () => {
    try {
      const data = JSON.parse(body);
      const meetingId = `meeting-${Date.now()}`;
      
      // Store meeting data
      const meeting = {
        id: meetingId,
        title: data.meeting_title || 'Untitled Meeting',
        transcripts: data.transcripts || [],
        created_at: new Date().toISOString()
      };
      
      meetings.push(meeting);
      transcripts.push(...(data.transcripts || []));
      
      console.log(`[Mock REST] Saved meeting: ${meeting.title}`);
      
      res.writeHead(200);
      res.end(JSON.stringify({
        success: true,
        meeting_id: meetingId,
        transcripts_saved: data.transcripts?.length || 0
      }));
    } catch (error) {
      console.error('[Mock REST] Error saving transcript:', error);
      res.writeHead(400);
      res.end(JSON.stringify({ error: 'Invalid JSON' }));
    }
  });
}

function handleGetMeetings(req, res) {
  res.writeHead(200);
  res.end(JSON.stringify({
    meetings: meetings,
    total: meetings.length
  }));
}

function handleTranscribe(req, res) {
  // Mock transcription endpoint
  const mockTranscriptions = [
    "This is a mock transcription of the audio chunk.",
    "The meeting is progressing well with good participation.",
    "We're discussing the project timeline and deliverables.",
    "Everyone seems aligned on the next steps.",
    "The technical implementation looks promising."
  ];
  
  const randomText = mockTranscriptions[Math.floor(Math.random() * mockTranscriptions.length)];
  
  // Simulate processing delay
  setTimeout(() => {
    res.writeHead(200);
    res.end(JSON.stringify({
      text: randomText,
      confidence: 0.85 + Math.random() * 0.15,
      timestamp: new Date().toISOString(),
      mock: true
    }));
  }, 500 + Math.random() * 1000); // 500-1500ms delay
}

function handleGetModelConfig(req, res) {
  res.writeHead(200);
  res.end(JSON.stringify({
    model: 'mock-whisper-v1',
    language: 'en',
    sample_rate: 16000,
    chunk_length: 30
  }));
}

function handleProcessTranscript(req, res) {
  let body = '';
  req.on('data', chunk => {
    body += chunk.toString();
  });
  
  req.on('end', () => {
    try {
      const data = JSON.parse(body);
      
      // Mock processing result
      res.writeHead(200);
      res.end(JSON.stringify({
        processed: true,
        summary: "Mock summary: This meeting covered project updates and next steps.",
        action_items: [
          "Review technical specifications",
          "Schedule follow-up meeting",
          "Update project timeline"
        ],
        participants: ["User 1", "User 2", "User 3"],
        duration: "30 minutes"
      }));
    } catch (error) {
      res.writeHead(400);
      res.end(JSON.stringify({ error: 'Invalid JSON' }));
    }
  });
}

server.listen(PORT, () => {
  console.log(`[Mock REST Server] Running on http://localhost:${PORT}`);
  console.log('Available endpoints:');
  console.log('  GET  /health');
  console.log('  POST /save-transcript');
  console.log('  GET  /get-meetings');
  console.log('  POST /transcribe');
  console.log('  GET  /get-model-config');
  console.log('  POST /process-transcript');
});

// Epic B Mock Handlers
function handleIdentifySpeakers(req, res) {
  getRequestBody(req, (body) => {
    const { text, context } = body;
    
    // Mock speaker identification
    const mockSpeakers = ["John Smith", "Sarah Johnson", "Mike Chen", "Emily Davis"];
    const numSpeakers = Math.min(2 + Math.floor(Math.random() * 3), mockSpeakers.length);
    const selectedSpeakers = mockSpeakers.slice(0, numSpeakers);
    
    setTimeout(() => {
      res.writeHead(200);
      res.end(JSON.stringify({
        status: 'success',
        data: {
          speakers: selectedSpeakers.map((name, index) => ({
            id: `speaker_${index + 1}`,
            name: name,
            segments: [
              `${name} discussed the project requirements`,
              `${name} provided updates on current progress`
            ],
            total_words: 50 + Math.floor(Math.random() * 100),
            characteristics: `${name.split(' ')[0]} - active participant, clear communication`
          })),
          confidence: 0.85 + Math.random() * 0.15,
          total_speakers: numSpeakers,
          identification_method: 'ai_inference',
          processing_time: 2.3
        }
      }));
    }, 500 + Math.random() * 1000);
  });
}

function handleGenerateSummary(req, res) {
  getRequestBody(req, (body) => {
    const { transcript, meeting_id, meeting_title } = body;
    
    setTimeout(() => {
      res.writeHead(200);
      res.end(JSON.stringify({
        status: 'success',
        data: {
          meeting_title: meeting_title || "Team Meeting",
          executive_summary: {
            overview: "Team discussed project progress, identified key challenges, and planned next steps for the upcoming sprint.",
            key_outcomes: [
              "Prioritized authentication feature development",
              "Identified performance optimization opportunities",
              "Planned integration testing strategy"
            ],
            business_impact: "Critical foundation for user management system",
            urgency_level: "high",
            follow_up_required: true
          },
          key_decisions: {
            decisions: [
              {
                decision: "Implement OAuth 2.0 authentication",
                rationale: "Industry standard for secure user authentication",
                impact: "Enables secure user access and third-party integrations",
                timeline: "Complete by end of sprint",
                confidence: 0.95
              }
            ],
            total_decisions: 1,
            consensus_level: "unanimous"
          },
          participants: {
            participants: [
              {
                name: "John Smith",
                role: "Team Lead",
                participation_level: "high",
                key_contributions: ["Technical insights", "Project planning"]
              },
              {
                name: "Sarah Johnson", 
                role: "Developer",
                participation_level: "medium",
                key_contributions: ["Implementation details", "Testing strategy"]
              }
            ],
            meeting_leader: "John Smith",
            total_participants: 2,
            participation_balance: "balanced"
          },
          summary_generated_at: new Date().toISOString()
        }
      }));
    }, 800 + Math.random() * 1200);
  });
}

function handleExtractTasks(req, res) {
  getRequestBody(req, (body) => {
    const { transcript, meeting_context } = body;
    
    const mockTasks = [
      {
        title: "Update authentication system",
        description: "Implement OAuth 2.0 with Google and GitHub providers",
        category: "action_item",
        priority: "high"
      },
      {
        title: "Review API documentation",
        description: "Update API docs with new endpoints and examples",
        category: "follow_up",
        priority: "medium"
      },
      {
        title: "Schedule follow-up meeting",
        description: "Plan next sprint review meeting with stakeholders",
        category: "decision_required",
        priority: "low"
      }
    ];
    
    const numTasks = 1 + Math.floor(Math.random() * 3);
    const selectedTasks = mockTasks.slice(0, numTasks);
    const mockAssignees = ["John Smith", "Sarah Johnson", "Mike Chen"];
    
    setTimeout(() => {
      const tasks = selectedTasks.map((task, index) => ({
        id: `task_${index + 1}`,
        title: task.title,
        description: task.description,
        assignee: Math.random() > 0.3 ? mockAssignees[Math.floor(Math.random() * mockAssignees.length)] : "Unassigned",
        due_date: Math.random() > 0.5 ? getRandomFutureDate() : null,
        priority: task.priority,
        status: "pending",
        category: task.category,
        dependencies: Math.random() > 0.7 ? ["Previous task completion"] : [],
        business_impact: task.priority,
        created_at: new Date().toISOString()
      }));
      
      res.writeHead(200);
      res.end(JSON.stringify({
        status: 'success',
        data: {
          tasks: tasks,
          task_summary: {
            total_tasks: tasks.length,
            high_priority: tasks.filter(t => t.priority === 'high').length,
            with_deadlines: tasks.filter(t => t.due_date).length,
            assigned: tasks.filter(t => t.assignee !== 'Unassigned').length
          },
          extraction_metadata: {
            explicit_tasks_found: Math.floor(tasks.length * 0.7),
            implicit_tasks_found: Math.floor(tasks.length * 0.3),
            extracted_at: new Date().toISOString()
          }
        }
      }));
    }, 600 + Math.random() * 800);
  });
}

function handleProcessTranscriptWithTools(req, res) {
  getRequestBody(req, (body) => {
    const { text, meeting_id, timestamp, platform } = body;
    
    setTimeout(() => {
      // Generate mock comprehensive analysis
      const mockSpeakers = ["John Smith", "Sarah Johnson", "Mike Chen"];
      const speakers = mockSpeakers.slice(0, 2 + Math.floor(Math.random() * 2));
      
      const summary = {
        meeting_title: "Team Meeting",
        executive_summary: {
          overview: "Comprehensive meeting analysis with participant detection and task extraction",
          key_outcomes: ["Enhanced collaboration", "Clear action items", "Improved productivity"]
        }
      };
      
      const tasks = [
        {
          id: "task_1",
          title: "Implement user authentication",
          assignee: speakers[0],
          priority: "high",
          due_date: getRandomFutureDate()
        }
      ];
      
      res.writeHead(200);
      res.end(JSON.stringify({
        status: 'success',
        meeting_id: meeting_id,
        analysis: summary,
        actions_taken: tasks,
        speakers: speakers.map((name, index) => ({
          id: `speaker_${index + 1}`,
          name: name,
          segments: [`${name} contributed to the discussion`]
        })),
        tools_used: 3,
        processed_at: new Date().toISOString()
      }));
    }, 1500 + Math.random() * 2000);
  });
}

function handleAvailableTools(req, res) {
  res.writeHead(200);
  res.end(JSON.stringify({
    tools: [
      {
        name: 'identify_speakers',
        description: 'Identify speakers in meeting transcript',
        parameters: ['text', 'context']
      },
      {
        name: 'extract_tasks',
        description: 'Extract action items and tasks',
        parameters: ['transcript', 'meeting_context']
      },
      {
        name: 'generate_summary',
        description: 'Generate comprehensive meeting summary',
        parameters: ['transcript', 'meeting_title']
      }
    ],
    tool_names: ['identify_speakers', 'extract_tasks', 'generate_summary'],
    count: 3
  }));
}

// Helper functions
function getRequestBody(req, callback) {
  let body = '';
  req.on('data', chunk => {
    body += chunk.toString();
  });
  req.on('end', () => {
    try {
      const parsedBody = JSON.parse(body);
      callback(parsedBody);
    } catch (error) {
      console.error('Error parsing request body:', error);
      callback({});
    }
  });
}

function getRandomFutureDate() {
  const days = Math.floor(Math.random() * 14) + 1; // 1-14 days from now
  const futureDate = new Date();
  futureDate.setDate(futureDate.getDate() + days);
  return futureDate.toISOString().split('T')[0]; // YYYY-MM-DD format
}

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n[Mock REST Server] Shutting down...');
  server.close(() => {
    console.log('[Mock REST Server] Server closed');
    process.exit(0);
  });
});