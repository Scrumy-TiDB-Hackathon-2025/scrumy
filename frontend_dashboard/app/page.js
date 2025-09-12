'use client';

import CalendarSection from '@/components/CalendarSection';
import NewChatSection from '@/components/NewChatSection';
import MeetingCard from '@/components/MeetingCard';
import { useState, useEffect } from 'react';
import { useSidebar } from '@/contexts/SidebarContext';

import { config } from '@/lib/config';
import { apiService } from '@/lib/api';

export default function Dashboard() {
  const [health, setHealth] = useState('Checking...');
  const [meetings, setMeetings] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  
  const { sidebarCollapsed } = useSidebar();

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);

      // Check backend health
      try {
        const healthData = await apiService.checkHealth();
        setHealth(healthData.status === 'healthy' ? 'healthy' : 'unhealthy');
      } catch (err) {
        console.error('Health check failed:', err);
        setHealth('Offline');
        setError(`Health check failed: ${err.message}`);
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
  }, [error]);

  return (
    <div className="h-full bg-gray-50">
      <div className="h-full flex flex-col">
        <div className={`transition-all duration-300 ${sidebarCollapsed ? 'p-8' : 'p-6'}`}>
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-bold text-gray-900">
              ScrumBot Dashboard
            </h1>
            
            <div className="flex items-center gap-4 text-sm">
              <span className="text-gray-600">
                Status: <span className={health === 'healthy' ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
                  {health}
                </span>
              </span>
            </div>
          </div>
        </div>

        {/* Scrollable content area */}
        <div className="flex-1 overflow-y-auto">
          <div className={`transition-all duration-300 ${sidebarCollapsed ? 'px-8 pb-8' : 'px-6 pb-6'}`}>
            <div className="space-y-6">
              {/* Calendar Section - Expandable */}
              <div className={`bg-white rounded-lg border shadow-sm transition-all duration-300 ${
                sidebarCollapsed ? 'p-8' : 'p-4'
              }`}>
                <CalendarSection />
              </div>
              
              {/* Meeting Card - Takes more space when expanded */}
              <div className={`transition-all duration-300 ${
                sidebarCollapsed ? 'min-h-[700px]' : 'min-h-[500px]'
              }`}>
                <MeetingCard meetings={meetings} loading={loading} />
              </div>

              {/* Hackathon Demo Card */}
              <div className={`bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-100 rounded-lg transition-all duration-300 ${
                sidebarCollapsed ? 'p-8' : 'p-6'
              }`}>
                <h3 className="text-lg font-semibold text-blue-800 mb-2">🚀 TiDB AgentX Hackathon Demo</h3>
                <p className="text-blue-700 mb-4 text-sm">
                  This is a live demo of ScrumBot - an AI-powered meeting intelligence system built for the TiDB AgentX Hackathon 2025.
                </p>
                <div className={`grid gap-3 mb-4 transition-all duration-300 ${
                  sidebarCollapsed 
                    ? 'grid-cols-2 md:grid-cols-6' 
                    : 'grid-cols-2 md:grid-cols-4'
                }`}>
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
                  {sidebarCollapsed && (
                    <>
                      <span className="bg-pink-200 text-pink-800 px-3 py-2 rounded-full text-xs font-medium text-center">
                        Meeting Analytics
                      </span>
                      <span className="bg-indigo-200 text-indigo-800 px-3 py-2 rounded-full text-xs font-medium text-center">
                        Action Items
                      </span>
                    </>
                  )}
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
                <div className={`bg-yellow-50 border border-yellow-200 rounded-lg transition-all duration-300 ${
                  sidebarCollapsed ? 'p-6' : 'p-4'
                }`}>
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
      </div>

      {/* Chat Component - Now as floating overlay */}
      <NewChatSection />
    </div>
  );
}