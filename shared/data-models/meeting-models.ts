// Shared data models for ScrumBot

export interface Meeting {
  id: string;
  title: string;
  platform: 'google-meet' | 'zoom' | 'teams' | 'unknown';
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
  identification_method: 'explicit_labels' | 'ai_inference' | 'fallback';
}

export interface Task {
  id: string;
  meeting_id: string;
  title: string;
  description: string;
  assignee?: string;
  due_date?: string;
  priority: 'low' | 'medium' | 'high';
  status: 'pending' | 'in_progress' | 'completed';
  category: 'action_item' | 'follow_up' | 'decision_required';
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
    urgency_level: 'low' | 'medium' | 'high';
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
    consensus_level: 'unanimous' | 'majority' | 'split' | 'unknown';
  };
  discussion_topics: {
    topics: Array<{
      topic: string;
      category: 'technical' | 'business' | 'process' | 'planning' | 'review';
      discussion_depth: 'brief' | 'moderate' | 'extensive';
      resolution_status: 'resolved' | 'ongoing' | 'deferred';
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
      priority: 'high' | 'medium' | 'low';
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
      role: string;
      participation_level: 'high' | 'medium' | 'low';
      key_contributions: string[];
    }>;
    meeting_leader: string;
    total_participants: number;
    participation_balance: 'balanced' | 'dominated' | 'mixed' | 'unknown';
  };
  summary_generated_at: string;
}

export interface AudioChunk {
  type: 'audio_chunk';
  data: string; // base64 encoded
  timestamp: string;
  metadata: {
    platform: string;
    meetingUrl: string;
    chunkSize: number;
    sampleRate?: number;
  };
}

export interface TranscriptionResult {
  type: 'transcription_result';
  data: {
    text: string;
    confidence: number;
    timestamp: string;
    speaker?: string;
  };
}

export interface ProcessingStatus {
  status: 'processing' | 'completed' | 'error';
  meeting_id: string;
  process_id?: string;
  data?: MeetingSummary;
  error?: string;
  start_time?: string;
  end_time?: string;
}