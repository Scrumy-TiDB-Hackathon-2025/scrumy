import React from "react";

export default function MeetingCard({ meetings = [], loading }) {
  return (
    <div className="bg-gray-50 rounded-lg shadow-sm p-4 mb-4">
      <h2 className="text-lg font-semibold mb-3">Recent Meetings</h2>
      {loading ? (
        <div className="text-center py-3">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-gray-500 mt-2 text-sm">Loading meetings...</p>
        </div>
      ) : meetings.length === 0 ? (
        <div className="text-center py-6">
          <div className="text-4xl mb-2">🎤</div>
          <p className="text-gray-500 mb-2 text-sm">
            No meetings yet. Start a meeting with the Chrome extension!
          </p>
          <div className="text-xs text-gray-400 space-y-1">
            <p>📱 Install the Chrome extension</p>
            <p>🎥 Join a Google Meet, Zoom, or Teams call</p>
            <p>🎙️ Start recording to see transcripts here</p>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {meetings.map((meeting, index) => (
            <div
              key={meeting.id || index}
              className="border border-gray-200 rounded p-3 hover:bg-gray-100"
            >
              <h3 className="font-medium text-gray-900">
                {meeting.title || "Untitled Meeting"}
              </h3>
              <p className="text-xs text-gray-500">
                {meeting.created_at || "Just created"}
              </p>
              {meeting.transcript && (
                <p className="text-xs text-gray-700 mt-1 truncate">
                  {meeting.transcript}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}