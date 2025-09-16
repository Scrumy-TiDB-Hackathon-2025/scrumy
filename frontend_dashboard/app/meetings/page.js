'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { apiService } from '@/lib/api';
import { useWebSocket } from '@/hooks/useWebSocket';

const MeetingsPage = () => {
  const router = useRouter();
  const [selectedMeeting, setSelectedMeeting] = useState(null);
  const [activeTab, setActiveTab] = useState('summary');
  const [filterOpen, setFilterOpen] = useState(false);
  const [dateRangeOpen, setDateRangeOpen] = useState(false);

  const [meetingsData, setMeetingsData] = useState({
    totalMeetings: 0,
    completed: 0,
    actionItems: 0,
    avgDuration: 0
  });
  const [meetings, setMeetings] = useState([
    // Default data while loading
    {
      id: 1,
      title: 'Daily Standup',
      date: 'Aug 5, 2025',
      time: '9:00AM',
      duration: '35 minutes',
      attendees: 4,
      actionItems: 3,
      summary: 'Team reported steady progress on the dashboard module. Grace flagged a blocker with the API response formatting. Paul will help troubleshoot after lunch. John is on leave today.',
      overview: 'The October GameUp Africa MeetUp featured talks from Unity Technologies. Ollie Nicholson discussed accelerating Unity development with tools like Pro Builder, Polybrush, and AI-driven features such as Muse Texture and Sprite generation. He emphasized the importance of optimizing assets and leveraging the Asset Store for productivity. Valentin Simonov introduced Unity 6, highlighting its new generational release model and features like GPU-resident drawers for improved performance. He also discussed the transition to a more stable and frequent update cycle, with additive features in update releases. Both speakers encouraged developers to explore these tools and resources for enhanced game development.',
      actionItemsList: [],
      transcript: [
        { speaker: 'Charlie', time: '0:00', text: 'Hey Lisa, I got your email with a meeting summary from Otter and I was curious about how it works. Have you been using it a lot for your meetings?', avatar: 'C' },
        { speaker: 'Lisa', time: '0:00', text: 'Yeah, I started using Otter a few months ago. And it saved me a lot of time from taking manual notes. It also helps me find answers from previous meetings and even write follow up emails.', avatar: 'L' },
        { speaker: 'Charlie', time: '0:00', text: 'Hey Lisa, I got your email with a meeting summary from Otter and I was curious about how it works. Have you been using it a lot for your meetings?', avatar: 'C' },
        { speaker: 'Lisa', time: '0:00', text: 'Yeah, I started using Otter a few months ago. And it saved me a lot of time from taking manual notes. It also helps me find answers from previous meetings and even write follow up emails.', avatar: 'L' }
      ],
      chatQuestions: [
        'What specific features are being demonstrated during the customer demos on Friday?',
        'How will the system issues encountered by team affect project timelines?',
        'What were the challenges faced with the credit scoring model adjustments?'
      ]
    },
    {
      id: 2,
      title: 'Daily Standup',
      date: 'Aug 5, 2025',
      time: '9:00AM',
      duration: '35 minutes',
      attendees: 4,
      actionItems: 3,
      summary: 'Team reported steady progress on the dashboard module. Grace flagged a blocker with the API response formatting. Paul will help troubleshoot after lunch. John is on leave today.',
      overview: 'Daily standup meeting to discuss progress and blockers.',
      actionItemsList: [],
      transcript: [
        { speaker: 'Grace', time: '0:00', text: 'I am blocked on the API response formatting. The data structure changed and our parsing logic needs updating.', avatar: 'G' },
        { speaker: 'Paul', time: '0:15', text: 'I can help you with that after lunch. Let me know what specific fields are causing issues.', avatar: 'P' }
      ],
      chatQuestions: [
        'What is the timeline for fixing the API issue?',
        'Who else can help with the dashboard module?'
      ]
    },
    {
      id: 3,
      title: 'Daily Standup',
      date: 'Aug 5, 2025',
      time: '9:00AM',
      duration: '35 minutes',
      attendees: 4,
      actionItems: 3,
      summary: 'Team reported steady progress on the dashboard module. Grace flagged a blocker with the API response formatting. Paul will help troubleshoot after lunch. John is on leave today.',
      overview: 'Daily standup meeting to discuss progress and blockers.',
      actionItemsList: [],
      transcript: [
        { speaker: 'John', time: '0:00', text: 'Working on the authentication module today. Should be ready for testing by end of week.', avatar: 'J' },
        { speaker: 'Sarah', time: '0:10', text: 'Great! I can help with testing once its ready.', avatar: 'S' }
      ],
      chatQuestions: [
        'When will the authentication module be complete?',
        'What testing approach will be used?'
      ]
    }
  ]);
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
    const fetchMeetings = async () => {
      try {
        setLoading(true);
        const response = await apiService.getMeetings();
        if (response.data) {
          setMeetings(response.data.meetings || []);
          setMeetingsData(response.data.stats || meetingsData);
        }
        setError('');
      } catch (err) {
        console.error('Failed to fetch meetings:', err);
        setError(`Failed to load meetings: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchMeetings();
  }, []);

  const handleMeetingClick = async (meeting) => {
    router.push(`/meetings/${meeting.id}`);
    setSelectedMeeting(meeting);
    
    try {
      const transcriptResponse = await apiService.getMeetingDetail(meeting.id);
      const transcriptData = transcriptResponse.data || {};
      
      const formattedTranscript = transcriptData.transcript_chunks?.map((chunk, index) => ({
        speaker: chunk.speaker || `Speaker ${index + 1}`,
        time: chunk.timestamp || '0:00',
        text: chunk.text || '',
        avatar: chunk.speaker ? chunk.speaker.charAt(0).toUpperCase() : 'S'
      })) || [];
      
      // Load tasks separately
      let formattedTasks = [];
      try {
        const tasksResponse = await apiService.getTasks(meeting.id);
        console.log('Raw tasks response:', tasksResponse);
        const tasksData = tasksResponse.data || [];
        console.log('Tasks data:', tasksData);
        formattedTasks = tasksData.map(task => ({
          id: task.id,
          text: task.title,
          completed: task.status === 'completed',
          assignee: task.assignee,
          priority: task.priority
        }));
        console.log('Formatted tasks:', formattedTasks);
      } catch (taskErr) {
        console.error('Failed to load tasks:', taskErr);
      }
      
      setSelectedMeeting({
        ...meeting,
        transcript: formattedTranscript,
        overview: transcriptData.transcript || meeting.summary,
        actionItemsList: formattedTasks,
        chatQuestions: meeting.chatQuestions || []
      });
      setLiveTranscript([]);
    } catch (err) {
      console.error('Failed to load meeting data:', err);
    }
  };

  const handleBackToList = () => {
    router.push('/meetings');
    setSelectedMeeting(null);
    setActiveTab('summary');
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

  if (selectedMeeting) {
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
                <span>{selectedMeeting.date} at 6:30 pm</span>
              </div>
              <div className="flex items-center gap-2">
                <span>⏱</span>
                <span>3 min</span>
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
                    {selectedMeeting.overview}
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
                    {(selectedMeeting.actionItemsList || []).length > 0 ? (
                      selectedMeeting.actionItemsList.map((item) => (
                        <div key={item.id} className="flex items-center gap-3">
                          <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                              item.completed
                                ? 'bg-blue-600 border-blue-600 text-white'
                                : 'border-gray-300'
                            }`}>
                            {item.completed && '✓'}
                          </div>
                          <div className="flex-1">
                            <span className={`${item.completed ? 'line-through text-gray-500' : 'text-gray-700'}`}>
                              {item.text}
                            </span>
                            {item.assignee && (
                              <span className="text-sm text-gray-500 ml-2">• {item.assignee}</span>
                            )}
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-gray-500 text-sm">No action items found for this meeting.</p>
                    )}

                  </div>
                </div>

                {/* Outline */}
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    📝 Outline
                  </h2>
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <p className="text-purple-800">Ollie Nicholson's Introduction and Overview of Unity Pro</p>
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
                
                {/* Audio Player */}
                <div className="mt-8 p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-4">
                    <button className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center">
                      ▶️
                    </button>
                    <div className="flex-1">
                      <div className="w-full bg-blue-200 rounded-full h-2">
                        <div className="bg-blue-600 h-2 rounded-full w-1/4"></div>
                      </div>
                    </div>
                    <span className="text-sm text-gray-600">0:31</span>
                    <button className="text-gray-600">⏪</button>
                    <button className="text-gray-600">⏩</button>
                    <span className="text-sm text-gray-600">1x</span>
                    <span className="text-sm text-gray-600">3:44</span>
                  </div>
                </div>
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
  }

  // Main meetings list view
  return (
    <div className="p-6 bg-gray-50 h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Meetings</h1>
          <p className="text-gray-600 mt-1">View meeting history and summaries</p>
        </div>
        <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2">
          📹 Add to live meeting
        </button>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="text-center py-12">
          <div className="text-gray-400 text-lg mb-2">Loading meetings...</div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="text-red-800 font-medium">Error Loading Meetings</div>
          <div className="text-red-600 text-sm mt-1">{error}</div>
        </div>
      )}

      {/* Stats Cards */}
      {!loading && (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="text-2xl font-bold text-gray-900">{meetingsData.totalMeetings}</div>
          <div className="text-gray-600 text-sm">Total Meetings</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="text-2xl font-bold text-gray-900">{meetingsData.completed}</div>
          <div className="text-gray-600 text-sm">Completed</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="text-2xl font-bold text-gray-900">{meetingsData.actionItems}</div>
          <div className="text-gray-600 text-sm">Action Items Created</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="text-2xl font-bold text-gray-900">{meetingsData.avgDuration}</div>
          <div className="text-gray-600 text-sm">Avg Meeting Duration</div>
        </div>
      </div>
      )}

      {/* Search and Filters */}
      <div className="flex items-center gap-4 mb-6">
        <div className="flex-1 relative">
          <input
            type="text"
            placeholder="Search meetings, action items, Project..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
            🔍
          </div>
        </div>
        <button 
          onClick={() => setFilterOpen(!filterOpen)}
          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
        >
          🔽 Filter
        </button>
        <button 
          onClick={() => setDateRangeOpen(!dateRangeOpen)}
          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
        >
          📅 Date Range
        </button>
      </div>

      {/* Meetings List */}
      {!loading && (
      <div className="space-y-4">
        {meetings.map((meeting) => (
          <div 
            key={meeting.id}
            onClick={() => handleMeetingClick(meeting)}
            className="bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-4 mb-2">
                  <h3 className="text-lg font-semibold text-gray-900">{meeting.title}</h3>
                  <span className="text-sm text-gray-500">{meeting.date}</span>
                  <span className="text-sm text-gray-500">{meeting.time}</span>
                  <span className="text-sm text-gray-500">{meeting.duration}</span>
                </div>
                <p className="text-gray-700 mb-4">{meeting.summary}</p>
                <div className="flex items-center gap-4">
                  <div className="flex -space-x-2">
                    {[1, 2, 3, 4].map((i) => (
                      <div 
                        key={i}
                        className="w-8 h-8 rounded-full bg-gray-600 border-2 border-white flex items-center justify-center text-white text-sm font-medium"
                      >
                        {String.fromCharCode(64 + i)}
                      </div>
                    ))}
                  </div>
                  <span className="text-sm text-gray-500">{meeting.attendees} Attendees</span>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <button className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50">
                  📄 Transcript
                </button>
                <div className="flex items-center gap-1 text-sm text-gray-600">
                  ☑️ {meeting.actionItems} Action Items
                </div>
                <button className="text-blue-600 hover:text-blue-700 text-sm">
                  View Details
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      )}

      {/* Empty state */}
      {!loading && !error && meetings.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 text-lg mb-2">No meetings found</div>
          <div className="text-gray-500">Start a meeting to see it appear here!</div>
        </div>
      )}
    </div>
  );
};

export default MeetingsPage;