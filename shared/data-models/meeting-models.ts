// Shared data models for ScrumBot

export interface Meeting {
  id: string;
  title: string;
  platform: "google-meet" | "zoom" | "teams" | "unknown";
  created_at: string;
  updated_at: string;
}

export interface Transcript {
  id: string;
  meeting_id: string;
  text: string;
  timestamp: string;
  speaker?: string;
  confidence?: number;
}

export interface Speaker {
  id: string;
  name: string;
  segments: string[];
  total_words?: number;
  characteristics?: string;
}

export interface SpeakerIdentification {
  speakers: Speaker[];
  confidence: number;
  total_speakers: number;
  identification_method: "explicit_labels" | "ai_inference" | "fallback";
}

export interface Task {
  id: string;
  meeting_id: string;
  title: string;
  description: string;
  assignee?: string;
  due_date?: string;
  priority: "low" | "medium" | "high";
  status: "pending" | "in_progress" | "completed";
  category: "action_item" | "follow_up" | "decision_required";
  notion_page_id?: string;
  slack_message_ts?: string;
  created_at: string;
}

export interface MeetingSummary {
  meeting_id: string;
  meeting_title: string;
  executive_summary: {
    overview: string;
    key_outcomes: string[];
    business_impact: string;
    urgency_level: "low" | "medium" | "high";
    follow_up_required: boolean;
  };
  key_decisions: {
    decisions: Array<{
      decision: string;
      rationale: string;
      impact: string;
      timeline: string;
      confidence: number;
    }>;
    total_decisions: number;
    consensus_level: "unanimous" | "majority" | "split" | "unknown";
  };
  discussion_topics: {
    topics: Array<{
      topic: string;
      category: "technical" | "business" | "process" | "planning" | "review";
      discussion_depth: "brief" | "moderate" | "extensive";
      resolution_status: "resolved" | "ongoing" | "deferred";
      key_points: string[];
    }>;
    primary_focus: string;
    topic_distribution: Record<string, number>;
  };
  next_steps: {
    next_steps: Array<{
      action: string;
      owner: string;
      deadline: string;
      priority: "high" | "medium" | "low";
      dependencies: string[];
    }>;
    next_meeting: {
      scheduled: boolean;
      date: string;
      purpose: string;
    };
    total_actions: number;
  };
  participants: {
    participants: Array<{
      name: string;
    }>;
    meeting_leader: string;
    total_participants: number;
    participation_balance: "balanced" | "dominated" | "mixed" | "unknown";
  };
  summary_generated_at: string;
}

export interface Participant {
  id: string;
  name: string;
  platform_id: string;
  status: "active" | "inactive" | "left";
  is_host: boolean;
  join_time: string;
  leave_time?: string;
}

export interface AudioChunk {
  type: "audio_chunk";
  data: string; // base64 encoded
  timestamp: string;
  metadata: {
    platform: string;
    meetingUrl: string;
    chunkSize: number;
    sampleRate?: number;
  };
}

export interface AudioChunkEnhanced {
  type: "AUDIO_CHUNK_ENHANCED";
  data: string; // base64 encoded
  timestamp: string;
  platform: "google-meet" | "zoom" | "teams" | "unknown";
  meetingUrl: string;
  participants: Participant[];
  participant_count: number;
  metadata: {
    chunk_size: number;
    sample_rate: number;
    channels: number;
    format: string;
  };
}

export interface TranscriptionResult {
  type: "transcription_result";
  data: {
    text: string;
    confidence: number;
    timestamp: string;
    speaker?: string;
  };
}

export interface TranscriptionResultEnhanced {
  type: "TRANSCRIPTION_RESULT";
  data: {
    text: string;
    confidence: number;
    timestamp: string;
    speaker: string;
    speaker_id: string;
    speaker_confidence: number;
    meetingId: string;
    chunkId: number;
    speakers: Array<{
      id: string;
      name: string;
      segments: string[];
      confidence: number;
    }>;
  };
}

export interface MeetingEvent {
  type: "MEETING_EVENT";
  eventType:
    | "participant_joined"
    | "participant_left"
    | "meeting_started"
    | "meeting_ended";
  timestamp: string;
  data: {
    meetingId: string;
    participant: Participant;
    total_participants: number;
  };
}

export interface ProcessingStatus {
  status: "processing" | "completed" | "error";
  meeting_id: string;
  process_id?: string;
  data?: MeetingSummary;
  error?: string;
  start_time?: string;
  end_time?: string;
}

// Enhanced processing status with participant context
export interface ProcessingStatusEnhanced {
  status: "processing" | "completed" | "error";
  meeting_id: string;
  process_id?: string;
  data?: MeetingSummary;
  participants?: Participant[];
  participant_count?: number;
  platform?: string;
  error?: string;
  start_time?: string;
  end_time?: string;
}
