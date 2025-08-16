'use client';

import CalendarSection from '@/components/CalendarSection';
import MeetingCard from '@/components/MeetingCard';
import { useState, useEffect } from 'react';

export default function Dashboard() {
  const [health, setHealth] = useState('Checking...');
  const [meetings, setMeetings] = useState([]);
  const [backendUrl] = useState(process.env.NEXT_PUBLIC_API_URL || 'https://b5462b7bbb65.ngrok-free.app');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  // Enhanced fetch function with ngrok support
  const apiCall = async (endpoint) => {
    const url = `${backendUrl}${endpoint}`;

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true', // Skip ngrok warning
        },
        mode: 'cors',
        credentials: 'omit', // Don't send cookies
      });

      // Check if response is ok
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // Check if response is actually JSON
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        // If we get HTML instead of JSON, it might be ngrok warning
        const text = await response.text();
        if (text.includes('ngrok')) {
          throw new Error('ngrok warning page detected - please visit the API URL directly first');
        }
        throw new Error(`Expected JSON but received: ${contentType}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API call failed for ${endpoint}:`, error);
      throw error;
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);

      // Check backend health
      try {
        const healthData = await apiCall('/health');
        setHealth(healthData.status === 'healthy' ? 'healthy' : 'unhealthy');
      } catch (err) {
        console.error('Health check failed:', err);
        setHealth('Offline');
        setError(`Health check failed: ${err.message}`);
      }

      // Get meetings
      try {
        const meetingsData = await apiCall('/get-meetings');

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
        if (error.includes('Health check failed')) {
          setError('');
        }
      } catch (err) {
        console.error('Failed to fetch meetings:', err);
        setError(`API Error: ${err.message}`);
        setMeetings([]);
      }

      setLoading(false);
    };

    fetchData();

    // Refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [backendUrl, error]);

// ...existing code...
  return (
    <div className="bg-white min-h-screen">
      <div className="max-w-3xl px-4 py-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">
          🤖 ScrumBot Dashboard
        </h1>

        <CalendarSection />
        <MeetingCard meetings={meetings} loading={loading} />

        {/* Debug Panel (only show if there are errors) */}
        {error && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
            <h3 className="text-xs font-semibold text-yellow-800 mb-1">🔧 Debug Information</h3>
            <div className="text-xs text-yellow-700 space-y-1">
              <p><strong>Backend URL:</strong> {backendUrl}</p>
              <p><strong>Error:</strong> {error}</p>
              <p><strong>Health Status:</strong> {health}</p>
              <p><strong>Meetings Count:</strong> {meetings.length}</p>
            </div>
            <div className="mt-2 flex gap-2">
              <a
                href={`${backendUrl}/health`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs bg-yellow-200 hover:bg-yellow-300 px-2 py-1 rounded"
              >
                Test Health Endpoint
              </a>
              <a
                href={`${backendUrl}/get-meetings`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs bg-yellow-200 hover:bg-yellow-300 px-2 py-1 rounded"
              >
                Test Meetings Endpoint
              </a>
            </div>
          </div>
        )}

        {/* Hackathon Demo Card */}
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-100 rounded-lg p-4">
          <h3 className="text-base font-semibold text-blue-800 mb-1">🚀 TiDB AgentX Hackathon Demo</h3>
          <p className="text-blue-700 mb-3 text-sm">
            This is a live demo of ScrumBot - an AI-powered meeting intelligence system built for the TiDB AgentX Hackathon 2025.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
            <span className="bg-blue-200 text-blue-800 px-2 py-1 rounded-full text-xs font-medium text-center">
              Multi-step AI
            </span>
            <span className="bg-green-200 text-green-800 px-2 py-1 rounded-full text-xs font-medium text-center">
              TiDB Vector Search
            </span>
            <span className="bg-purple-200 text-purple-800 px-2 py-1 rounded-full text-xs font-medium text-center">
              Real-time Transcription
            </span>
            <span className="bg-orange-200 text-orange-800 px-2 py-1 rounded-full text-xs font-medium text-center">
              Chrome Extension
            </span>
          </div>
          <div className="flex flex-wrap gap-2 text-xs">
            <a
              href={backendUrl}
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
      </div>
    </div>
  );
}