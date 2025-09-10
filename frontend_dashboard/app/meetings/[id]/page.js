'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { apiService } from '@/lib/api';
import { useWebSocket } from '@/hooks/useWebSocket';

const MeetingDetailPage = () => {
  const router = useRouter();
  const params = useParams();
  const meetingId = params.id;
  
  const [selectedMeeting, setSelectedMeeting] = useState(null);
  const [activeTab, setActiveTab] = useState('summary');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [liveTranscript, setLiveTranscript] = useState([]);

  const handleTranscriptUpdate = useCallback((data) => {
    if (data.text) {
      const newEntry = {
        speaker: data.speaker || 'Speaker',
        time: new Date().toLocaleTimeString(),
        text: data.text,
        avatar: data.speaker ? data.speaker.charAt(0).toUpperCase() : 'S',
        isLive: true
      };
      setLiveTranscript(prev => [...prev, newEntry]);
    }
  }, []);

  const { isConnected } = useWebSocket(selectedMeeting?.id, handleTranscriptUpdate);

  useEffect(() => {
    const fetchMeeting = async () => {
      if (!meetingId) return;
      
      try {
        setLoading(true);
        // First get the meeting from the list
        const meetingsResponse = await apiService.getMeetings();
        const meeting = meetingsResponse.data?.meetings?.find(m => m.id == meetingId);
        
        if (!meeting) {
          setError('Meeting not found');
          return;
        }

        // Set basic meeting data with defaults
        const meetingWithDefaults = {
          ...meeting,
          actionItemsList: meeting.actionItemsList || [],
          chatQuestions: meeting.chatQuestions || [],
          transcript: meeting.transcript || []
        };
        
        setSelectedMeeting(meetingWithDefaults);
        
        // Load detailed transcript data
        try {
          const response = await apiService.getMeetingDetail(meetingId);
          if (response.data) {
            const transcriptData = response.data;
            const formattedTranscript = transcriptData.transcript_chunks?.map((chunk, index) => ({
              speaker: chunk.speaker || `Speaker ${index + 1}`,
              time: chunk.timestamp || '0:00',
              text: chunk.text || '',
              avatar: chunk.speaker ? chunk.speaker.charAt(0).toUpperCase() : 'S'
            })) || [];
            
            setSelectedMeeting(prev => ({
              ...prev,
              transcript: formattedTranscript,
              overview: transcriptData.transcript || meeting.summary
            }));
          }
        } catch (transcriptErr) {
          console.error('Failed to load meeting transcript:', transcriptErr);
          // Keep basic meeting data if transcript load fails
        }
        
        setError('');
      } catch (err) {
        console.error('Failed to fetch meeting:', err);
        setError(`Failed to load meeting: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchMeeting();
  }, [meetingId]);

  const handleBackToList = () => {
    router.push('/meetings');
  };

  const toggleActionItem = (actionItemId) => {
    if (!selectedMeeting) return;
    
    const updatedActionItems = (selectedMeeting.actionItemsList || []).map(item =>
      item.id === actionItemId ? { ...item, completed: !item.completed } : item
    );
    
    setSelectedMeeting({
      ...selectedMeeting,
      actionItemsList: updatedActionItems
    });
  };

  const addActionItem = (text) => {
    if (!selectedMeeting || !text.trim()) return;
    
    const newActionItem = {
      id: Date.now(),
      text: text.trim(),
      completed: false
    };
    
    setSelectedMeeting({
      ...selectedMeeting,
      actionItemsList: [...(selectedMeeting.actionItemsList || []), newActionItem]
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400 text-lg">Loading meeting...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="text-red-600 text-lg mb-2">Error</div>
          <div className="text-gray-600 mb-4">{error}</div>
          <button 
            onClick={handleBackToList}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Back to Meetings
          </button>
        </div>
      </div>
    );
  }

  if (!selectedMeeting) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400 text-lg">Meeting not found</div>
      </div>
    );
  }

  return (
    <div className="flex h-full bg-gray-50">
      {/* Main Content */}
      <div className="flex-1 bg-white">
        {/* Header */}
        <div className="border-b border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button 
                onClick={handleBackToList}
                className="text-gray-600 hover:text-gray-800"
              >
                ←
              </button>
              <h1 className="text-2xl font-semibold text-gray-900">{selectedMeeting.title}</h1>
              <button className="text-gray-400 hover:text-gray-600">
                ⋯
              </button>
            </div>
          </div>
          
          <div className="flex items-center gap-6 mt-4 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <span>📅</span>
              <span>{selectedMeeting.date} at {selectedMeeting.time}</span>
            </div>
            <div className="flex items-center gap-2">
              <span>⏱</span>
              <span>{selectedMeeting.duration}</span>
            </div>
            <button className="flex items-center gap-2 text-blue-600 hover:text-blue-700">
              <span>📄</span>
              <span>copy summary</span>
            </button>
          </div>
          
          <div className="text-sm text-gray-500 mt-2">
            🤝 Shared with: General
          </div>
          
          {/* Tabs */}
          <div className="flex border-b border-gray-200 mt-6">
            <button
              onClick={() => setActiveTab('summary')}
              className={`px-4 py-2 text-sm font-medium border-b-2 ${
                activeTab === 'summary'
                  ? 'text-blue-600 border-blue-600'
                  : 'text-gray-500 border-transparent hover:text-gray-700'
              }`}
            >
              Summary
            </button>
            <button
              onClick={() => setActiveTab('transcript')}
              className={`px-4 py-2 text-sm font-medium border-b-2 ${
                activeTab === 'transcript'
                  ? 'text-blue-600 border-blue-600'
                  : 'text-gray-500 border-transparent hover:text-gray-700'
              }`}
            >
              Transcript
            </button>
            {activeTab === 'transcript' && (
              <button className="ml-auto px-4 py-2 text-sm text-blue-600 hover:text-blue-700">
                ✏️ Edit Transcript
              </button>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto">
          {activeTab === 'summary' && (
            <div className="space-y-8">
              {/* Overview */}
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  📋 Overview
                </h2>
                <p className="text-gray-700 leading-relaxed">
                  {selectedMeeting.overview || selectedMeeting.summary}
                </p>
              </div>

              {/* Action Items */}
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  ☑️ Action Items
                  <button className="text-gray-400 hover:text-gray-600">
                    ⋯
                  </button>
                </h2>
                <div className="space-y-3">
                  {(selectedMeeting.actionItemsList || []).map((item) => (
                    <div key={item.id} className="flex items-center gap-3">
                      <button
                        onClick={() => toggleActionItem(item.id)}
                        className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                          item.completed
                            ? 'bg-blue-600 border-blue-600 text-white'
                            : 'border-gray-300 hover:border-gray-400'
                        }`}
                      >
                        {item.completed && '✓'}
                      </button>
                      <span className={`${item.completed ? 'line-through text-gray-500' : 'text-gray-700'}`}>
                        {item.text}
                      </span>
                    </div>
                  ))}
                  <button
                    onClick={() => {
                      const text = prompt('Enter new action item:');
                      if (text) addActionItem(text);
                    }}
                    className="flex items-center gap-2 text-blue-600 hover:text-blue-700 mt-4"
                  >
                    + Add action item
                  </button>
                </div>
              </div>

              {/* Outline */}
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  📝 Outline
                </h2>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <p className="text-purple-800">Meeting outline and key discussion points</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'transcript' && (
            <div className="space-y-4">
              <div className="flex justify-between items-center mb-6">
                <div className="text-sm text-gray-600">
                  <strong>Speakers</strong>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                  <span className="text-gray-500">
                    {isConnected ? 'Live' : 'Offline'}
                  </span>
                </div>
              </div>
              
              {/* Historical transcript */}
              {selectedMeeting.transcript?.map((entry, index) => (
                <div key={`history-${index}`} className="flex gap-4">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium ${
                    entry.avatar === 'C' ? 'bg-blue-500' : 
                    entry.avatar === 'L' ? 'bg-orange-500' : 
                    entry.avatar === 'G' ? 'bg-green-500' : 
                    entry.avatar === 'P' ? 'bg-purple-500' : 
                    entry.avatar === 'J' ? 'bg-indigo-500' : 
                    'bg-gray-500'
                  }`}>
                    {entry.avatar}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-gray-900">{entry.speaker}</span>
                      <span className="text-sm text-gray-500">{entry.time}</span>
                    </div>
                    <p className="text-gray-700">{entry.text}</p>
                  </div>
                </div>
              ))}
              
              {/* Live transcript */}
              {liveTranscript.map((entry, index) => (
                <div key={`live-${index}`} className="flex gap-4 bg-green-50 p-3 rounded-lg border-l-4 border-green-500">
                  <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center text-white text-sm font-medium">
                    {entry.avatar}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-gray-900">{entry.speaker}</span>
                      <span className="text-sm text-gray-500">{entry.time}</span>
                      <span className="text-xs text-green-600 font-medium">LIVE</span>
                    </div>
                    <p className="text-gray-700">{entry.text}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* AI Chat Sidebar */}
      <div className="w-80 bg-gray-50 border-l border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <h3 className="font-semibold text-gray-900">ScrumAI Chat</h3>
        </div>
        
        <div className="p-4">
          <div className="bg-blue-50 p-3 rounded-lg mb-4">
            <p className="text-sm text-gray-700">
              <strong>Hello, Cephas</strong><br />
              I am Fred your AI Assistant who can help you answer any question from your meeting, generate content and more.
            </p>
          </div>
          
          <div className="space-y-3">
            {(selectedMeeting.chatQuestions || []).map((question, index) => (
              <button
                key={index}
                className="w-full text-left p-3 bg-white rounded-lg border border-gray-200 hover:border-gray-300 text-sm text-gray-700"
              >
                💡 {question}
              </button>
            ))}
          </div>
          
          <div className="mt-6">
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Ask Scrum AI"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                ➤
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MeetingDetailPage;