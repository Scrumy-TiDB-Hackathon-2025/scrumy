'use client';

import { useState } from 'react';

const MeetingsPage = () => {
  const [selectedMeeting, setSelectedMeeting] = useState(null);
  const [activeTab, setActiveTab] = useState('summary');
  const [filterOpen, setFilterOpen] = useState(false);
  const [dateRangeOpen, setDateRangeOpen] = useState(false);

  // Sample data - replace with your actual data source
  const meetingsData = {
    totalMeetings: 54,
    completed: 3,
    actionItems: 91,
    avgDuration: 74
  };

  const meetings = [
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
      actionItemsList: [
        { id: 1, text: 'Investigate the Unity Render Pipeline options', completed: false },
        { id: 2, text: 'Explore Unity Pro features and productivity tools.', completed: false }
      ],
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
      actionItemsList: [
        { id: 1, text: 'Fix API response formatting issue', completed: false },
        { id: 2, text: 'Review dashboard module progress', completed: true }
      ],
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
      actionItemsList: [
        { id: 1, text: 'Complete user authentication module', completed: false },
        { id: 2, text: 'Test new features on staging', completed: false }
      ],
      transcript: [
        { speaker: 'John', time: '0:00', text: 'Working on the authentication module today. Should be ready for testing by end of week.', avatar: 'J' },
        { speaker: 'Sarah', time: '0:10', text: 'Great! I can help with testing once its ready.', avatar: 'S' }
      ],
      chatQuestions: [
        'When will the authentication module be complete?',
        'What testing approach will be used?'
      ]
    }
  ];

  const handleMeetingClick = (meeting) => {
    setSelectedMeeting(meeting);
  };

  const handleBackToList = () => {
    setSelectedMeeting(null);
    setActiveTab('summary');
  };

  const toggleActionItem = (actionItemId) => {
    if (!selectedMeeting) return;
    
    const updatedActionItems = selectedMeeting.actionItemsList.map(item =>
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
      actionItemsList: [...selectedMeeting.actionItemsList, newActionItem]
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
                    {selectedMeeting.actionItemsList.map((item) => (
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
                    <p className="text-purple-800">Ollie Nicholson's Introduction and Overview of Unity Pro</p>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'transcript' && (
              <div className="space-y-4">
                <div className="text-sm text-gray-600 mb-6">
                  <strong>Speakers</strong>
                </div>
                
                {selectedMeeting.transcript.map((entry, index) => (
                  <div key={index} className="flex gap-4">
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
              {selectedMeeting.chatQuestions.map((question, index) => (
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

      {/* Stats Cards */}
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
    </div>
  );
};

export default MeetingsPage;