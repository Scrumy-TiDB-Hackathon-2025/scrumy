'use client';

import CalendarSection from '@/components/CalendarSection';
import ChatSection from '@/components/ChatSection';
import MeetingCard from '@/components/MeetingCard';
import { useState, useEffect } from 'react';

import { config } from '@/lib/config';
import { apiService } from '@/lib/api';

export default function Dashboard() {
  const [health, setHealth] = useState('Checking...');
  const [meetings, setMeetings] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingInfo, setRecordingInfo] = useState(null);

  const fetchData = async () => {
    setLoading(true);

    // Check backend health and recording status
    try {
      const healthData = await apiService.checkHealth();
      setHealth(healthData.status === 'healthy' ? 'healthy' : 'unhealthy');
      
      // Check recording status for smart refresh
      try {
        const recordingResponse = await fetch(`${config.apiUrl}/recording-status`);
        if (recordingResponse.ok) {
          const recordingData = await recordingResponse.json();
          // Only set recording true if there are actual active sessions
          setIsRecording(recordingData.is_recording && recordingData.active_sessions > 0);
          setRecordingInfo(recordingData);
        }
      } catch (recordingErr) {
        console.warn('Recording status check failed:', recordingErr);
        setIsRecording(false);
      }
    } catch (err) {
      console.error('Health check failed:', err);
      setHealth('Offline');
      setError(`Health check failed: ${err.message}`);
      setIsRecording(false);
    }

    // Get meetings
    try {
      const meetingsData = await apiService.getMeetings();

      // Handle the response structure
      if (Array.isArray(meetingsData)) {
        setMeetings(meetingsData);
      } else if (meetingsData.meetings && Array.isArray(meetingsData.meetings)) {
        setMeetings(meetingsData.meetings);
      } else {
        console.warn('Unexpected meetings response format:', meetingsData);
        setMeetings([]);
      }

      // Clear error if meetings fetch succeeded
      if (error) {
        setError('');
      }
    } catch (err) {
      console.error('Failed to fetch meetings:', err);
      setError(`API Error: ${err.message}`);
      setMeetings([]);
    }

    setLoading(false);
  };

  useEffect(() => {

    fetchData();

    // Smart refresh: 30s when recording, 2min when idle  
    const refreshInterval = isRecording ? 30000 : 120000; // 30s if recording, 2min otherwise
    const interval = setInterval(fetchData, refreshInterval);
    return () => clearInterval(interval);
  }, [isRecording]);

  return (
    <div className="flex h-full bg-gray-50">
      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-bold text-gray-900">
              ScrumBot Dashboard
            </h1>
            <div className="flex items-center gap-3">
              {isRecording && recordingInfo && recordingInfo.active_sessions > 0 && (
                <div className="flex items-center gap-2 text-red-600 text-sm font-medium" title={`Active recording sessions: ${recordingInfo.recent_sessions?.map(s => s.meeting_id).join(', ') || 'Unknown'}`}>
                  <div className="w-2 h-2 bg-red-600 rounded-full animate-pulse"></div>
                  <span>Live Recording ({recordingInfo.active_sessions} session{recordingInfo.active_sessions !== 1 ? 's' : ''})</span>
                </div>
              )}
              <button
                onClick={() => {
                  setLoading(true);
                  fetchData();
                }}
                disabled={loading}
                className="px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Refreshing...' : 'Refresh'}
              </button>
            </div>
          </div>

          <div className="space-y-6">
            <CalendarSection />
            
            <MeetingCard meetings={meetings} loading={loading} />

            {/* Hackathon Demo Card */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-100 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-blue-800 mb-2">🚀 TiDB AgentX Hackathon Demo</h3>
              <p className="text-blue-700 mb-4 text-sm">
                This is a live demo of ScrumBot - an AI-powered meeting intelligence system built for the TiDB AgentX Hackathon 2025.
              </p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                <span className="bg-blue-200 text-blue-800 px-3 py-2 rounded-full text-xs font-medium text-center">
                  Multi-step AI
                </span>
                <span className="bg-green-200 text-green-800 px-3 py-2 rounded-full text-xs font-medium text-center">
                  TiDB Vector Search
                </span>
                <span className="bg-purple-200 text-purple-800 px-3 py-2 rounded-full text-xs font-medium text-center">
                  Real-time Transcription
                </span>
                <span className="bg-orange-200 text-orange-800 px-3 py-2 rounded-full text-xs font-medium text-center">
                  Chrome Extension
                </span>
              </div>
              <div className="flex flex-wrap gap-3 text-sm">
                <a
                  href={config.apiUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 font-medium"
                >
                  🔗 API Endpoint
                </a>
                <span className="text-gray-400">•</span>
                <span className="text-gray-600">
                  Status: <span className={health === 'healthy' ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
                    {health}
                  </span>
                </span>
              </div>
            </div>

            {/* Debug Panel (only show if there are errors) */}
            {error && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-yellow-800 mb-2">🔧 Debug Information</h3>
                <div className="text-sm text-yellow-700 space-y-1">
                  <p><strong>Backend URL:</strong> {config.apiUrl}</p>
                  <p><strong>Environment:</strong> {config.environment}</p>
                  <p><strong>Error:</strong> {error}</p>
                  <p><strong>Health Status:</strong> {health}</p>
                  <p><strong>Meetings Count:</strong> {meetings.length}</p>
                </div>
                <div className="mt-3 flex gap-2">
                  <a
                    href={`${config.apiUrl}${config.endpoints.health}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs bg-yellow-200 hover:bg-yellow-300 px-3 py-2 rounded"
                  >
                    Test Health Endpoint
                  </a>
                  <a
                    href={`${config.apiUrl}${config.endpoints.meetings}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs bg-yellow-200 hover:bg-yellow-300 px-3 py-2 rounded"
                  >
                    Test Meetings Endpoint
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Chat Sidebar - Fixed position */}
      <div className="w-80 bg-white border-l border-gray-200 flex-shrink-0 h-full">
        <div className="h-full p-4">
          <ChatSection />
        </div>
      </div>
    </div>
  );
}