import { useState } from 'react';

export default function ChatSection() {
  const [isOpen, setIsOpen] = useState(false);

  const toggleChat = () => {
    setIsOpen(!isOpen);
  };

  return (
    <>
      {/* Chat Toggle Button - Fixed positioned with text and logo */}
      <button
        onClick={toggleChat}
        className="fixed bottom-6 right-6 bg-blue-500 hover:bg-blue-600 text-white rounded-full shadow-lg flex items-center gap-3 px-4 py-3 transition-all duration-300 z-50"
      >
        {isOpen ? (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <>
            {/* Scrumy Logo Placeholder - Replace with actual scrumy.svg */}
            <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center">
              <img src="/scrumy.svg" alt="ScrumAI Logo" className="h-6 w-6" />
            </div>
            <span className="text-sm font-medium whitespace-nowrap">Ask Scrumy</span>
          </>
        )}
      </button>

      {/* Chat Overlay */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 bg-black bg-opacity-25 z-40"
            onClick={toggleChat}
          />
          
          {/* Chat Panel */}
          <div className="fixed bottom-24 right-6 w-96 h-96 bg-white rounded-lg border shadow-xl z-50 flex flex-col animate-in slide-in-from-bottom-4 duration-300">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="font-semibold">ScrumAI Chat</h2>
              <button
                onClick={toggleChat}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              <div className="flex justify-end">
                <div className="bg-blue-500 text-white px-4 py-2 rounded-lg max-w-xs">
                  Can you summarize today's standup?
                </div>
              </div>
              <div className="flex justify-start">
                <div className="bg-gray-100 p-3 rounded-lg max-w-xs">
                  Today's standup covered sprint progress updates...
                </div>
              </div>
              <div className="flex justify-end">
                <div className="bg-blue-500 text-white px-4 py-2 rounded-lg max-w-xs">
                  What are the main blockers?
                </div>
              </div>
              <div className="flex justify-start">
                <div className="bg-gray-100 p-3 rounded-lg max-w-xs">
                  The main blocker is the payment API access...
                </div>
              </div>
            </div>

            {/* Input Area */}
            <div className="p-4 border-t">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  placeholder="Ask Scrum AI..."
                  className="flex-1 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button className="px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors">
                  🎤
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}