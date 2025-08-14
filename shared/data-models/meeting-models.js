// JavaScript data models for ScrumBot (reference for frontend development)

/**
 * Meeting object structure
 * @typedef {Object} Meeting
 * @property {string} id - Unique meeting identifier
 * @property {string} title - Meeting title
 * @property {'google-meet'|'zoom'|'teams'|'unknown'} platform - Video platform
 * @property {string} created_at - ISO timestamp
 * @property {string} updated_at - ISO timestamp
 */

/**
 * Transcript object structure
 * @typedef {Object} Transcript
 * @property {string} id - Unique transcript identifier
 * @property {string} meeting_id - Associated meeting ID
 * @property {string} text - Transcript text
 * @property {string} timestamp - ISO timestamp
 * @property {string} [speaker] - Speaker name (optional)
 * @property {number} [confidence] - Confidence score (optional)
 */

/**
 * Task object structure
 * @typedef {Object} Task
 * @property {string} id - Unique task identifier
 * @property {string} meeting_id - Associated meeting ID
 * @property {string} title - Task title
 * @property {string} description - Task description
 * @property {string} [assignee] - Person assigned (optional)
 * @property {string} [due_date] - Due date ISO string (optional)
 * @property {'low'|'medium'|'high'} priority - Task priority
 * @property {'pending'|'in_progress'|'completed'} status - Task status
 * @property {'action_item'|'follow_up'|'decision_required'} category - Task category
 * @property {string} [notion_page_id] - Notion page ID (optional)
 * @property {string} [slack_message_ts] - Slack message timestamp (optional)
 * @property {string} created_at - ISO timestamp
 */

/**
 * Processing Status object structure
 * @typedef {Object} ProcessingStatus
 * @property {'processing'|'completed'|'error'} status - Processing status
 * @property {string} meeting_id - Associated meeting ID
 * @property {string} [process_id] - Process identifier (optional)
 * @property {Object} [data] - Meeting summary data (optional)
 * @property {string} [error] - Error message (optional)
 * @property {string} [start_time] - Start time ISO string (optional)
 * @property {string} [end_time] - End time ISO string (optional)
 */

// Example data structures for development
export const exampleMeeting = {
  id: "meeting_123",
  title: "Sprint Planning Meeting",
  platform: "google-meet",
  created_at: "2025-01-08T10:00:00Z",
  updated_at: "2025-01-08T11:30:00Z"
};

export const exampleTask = {
  id: "task_456",
  meeting_id: "meeting_123",
  title: "Update user authentication system",
  description: "Implement OAuth 2.0 with Google and GitHub providers",
  assignee: "John Smith",
  due_date: "2025-01-15",
  priority: "high",
  status: "pending",
  category: "action_item",
  created_at: "2025-01-08T10:30:00Z"
};

export const exampleTranscript = {
  id: "transcript_789",
  meeting_id: "meeting_123",
  text: "We need to prioritize the authentication feature for Q1",
  timestamp: "2025-01-08T10:15:00Z",
  speaker: "John Smith",
  confidence: 0.95
};