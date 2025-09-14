'use client';

import { useState } from 'react';

const ChatSection = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = { role: 'user', content: inputMessage };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // Use proper chat endpoint for conversational responses
      const response = await fetch('http://127.0.0.1:8001/chat', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'accept': 'application/json' 
        },
        body: JSON.stringify({
          message: inputMessage,
          session_id: sessionId || `frontend_${Date.now()}`,
          context: { source: 'frontend_dashboard' }
        })
      });

      const data = await response.json();
      
      // Set session ID from response for conversation continuity
      if (!sessionId && data.session_id) {
        setSessionId(data.session_id);
      }
      
      const botMessage = { 
        role: 'assistant', 
        content: data.response,
        sources: data.metadata?.context_used ? 'Context used' : 'No context',
        similarity_scores: data.metadata?.similarity_scores || []
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const testQuestions = [
    "What meetings do I have data for?",
    "What tasks were assigned to David Chen?",
    "Show me all tasks from meeting meet.google.com_849975",
    "Who is assigned to review the database schema?",
    "What are the upcoming deadlines?"
  ];

  const handleTestQuestion = (question) => {
    setInputMessage(question);
  };

  const formatMessage = (content) => {
    // Parse markdown-style formatting from chatbot responses
    const lines = content.split('\n');
    const formatted = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      if (line.startsWith('**') && line.endsWith('**')) {
        // Bold headers
        formatted.push(
          <div key={i} className="font-semibold text-gray-800 mt-3 mb-1">
            {line.replace(/\*\*/g, '')}
          </div>
        );
      } else if (line.startsWith('- ')) {
        // Bullet points
        formatted.push(
          <div key={i} className="ml-4 mb-1 flex items-start">
            <span className="text-blue-500 mr-2 mt-1">•</span>
            <span>{line.substring(2)}</span>
          </div>
        );
      } else if (line.trim() === '') {
        // Empty lines for spacing
        formatted.push(<div key={i} className="h-2"></div>);
      } else {
        // Regular text
        formatted.push(
          <div key={i} className="mb-1">
            {line}
          </div>
        );
      }
    }
    
    return formatted;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border h-full flex flex-col">
      <div className="p-4 border-b">
        <h3 className="text-lg font-semibold text-gray-900">AI Assistant</h3>
        <p className="text-sm text-gray-600">Ask questions about your meetings and tasks</p>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            <p>👋 Hi! I can help you with questions about your meetings and tasks.</p>
            <p className="text-sm mt-2 mb-4">Try these test questions to validate contextual data access:</p>
            <div className="space-y-2">
              {testQuestions.map((question, index) => (
                <button
                  key={index}
                  onClick={() => handleTestQuestion(question)}
                  className="block w-full text-left px-3 py-2 text-sm bg-blue-50 hover:bg-blue-100 rounded-lg border border-blue-200 text-blue-700 transition-colors"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}
        
        {messages.map((message, index) => (
          <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`${
              message.role === 'user' 
                ? 'max-w-xs lg:max-w-md bg-blue-600 text-white' 
                : 'max-w-lg lg:max-w-2xl bg-gray-50 text-gray-900 border'
            } px-4 py-3 rounded-lg`}>
              <div className="text-sm">
                {message.role === 'assistant' ? formatMessage(message.content) : message.content}
              </div>
              {message.sources && (
                <div className="mt-3 pt-2 border-t border-gray-200">
                  <div className="flex items-center text-xs text-gray-500">
                    <span className="bg-green-100 text-green-700 px-2 py-1 rounded-full mr-2">
                      📚 {message.sources}
                    </span>
                    {message.similarity_scores.length > 0 && (
                      <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                        Similarity: {message.similarity_scores.map(s => s.toFixed(2)).join(', ')}
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-900 px-4 py-2 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                <span className="text-sm">Thinking...</span>
              </div>
            </div>
          </div>
        )}
      </div>
      
      <div className="p-4 border-t">
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about your meetings..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={isLoading || !inputMessage.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg className="w-4 h-4 transform rotate-45" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatSection;