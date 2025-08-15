'use client';

import { useState, useEffect } from 'react';
import CalendarSection from '@/components/CalendarSection';
import MeetingCard from '@/components/MeetingCard';
import ChatSection from '@/components/ChatSection';

export default function Dashboard() {
  const [health, setHealth] = useState('Checking...');
  const [meetings, setMeetings] = useState([]);
  const [backendUrl] = useState(
    process.env.NEXT_PUBLIC_API_URL || 'https://b5462b7bbb65.ngrok-free.app'
  );
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const apiCall = async (endpoint) => {
    const url = `${backendUrl}${endpoint}`;
    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true',
        },
        mode: 'cors',
        credentials: 'omit',
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const contentType = response.headers.get('content-type');
      if (!contentType?.includes('application/json')) {
        const text = await response.text();
        if (text.includes('ngrok')) {
          throw new Error(
            'ngrok warning page detected - please visit the API URL directly first'
          );
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

      try {
        const healthData = await apiCall('/health');
        setHealth(
          healthData.status === 'healthy' ? 'healthy' : 'unhealthy'
        );
      } catch (err) {
        setHealth('Offline');
        setError(`Health check failed: ${err.message}`);
      }

      try {
        const meetingsData = await apiCall('/get-meetings');
        if (Array.isArray(meetingsData)) {
          setMeetings(meetingsData);
        } else if (
          meetingsData.meetings &&
          Array.isArray(meetingsData.meetings)
        ) {
          setMeetings(meetingsData.meetings);
        } else {
          setMeetings([]);
        }
        if (error.includes('Health check failed')) setError('');
      } catch (err) {
        setError(`API Error: ${err.message}`);
        setMeetings([]);
      }

      setLoading(false);
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [backendUrl, error]);

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Sidebar
      <aside className="w-64 bg-white border-r px-4 py-6">
        <div className="mb-8">
          <div className="h-8 w-8 bg-blue-600 rounded-sm"></div>
        </div>
        <nav className="space-y-4">
          <a className="flex items-center text-blue-600 font-medium">
            Home
          </a>
          <a className="flex items-center text-gray-600 hover:text-blue-600">
            Project Trackers
          </a>
          <a className="flex items-center text-gray-600 hover:text-blue-600">
            Meetings
          </a>
          <a className="flex items-center text-gray-600 hover:text-blue-600">
            Action Items
          </a>
          <a className="flex items-center text-gray-600 hover:text-blue-600">
            Integrate
          </a>
        </nav>
      </aside> */}

      {/* Main content */}
      <main className="flex-1 p-8">
        <header className="mb-6 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold">Good morning, John</h1>
            <p className="text-gray-500">
              Here's what's happening with your team today.
            </p>
          </div>
          <div className="flex items-center gap-4">
            <button className="bg-blue-600 text-white px-4 py-2 rounded">
              Add to live meeting
            </button>
            <div className="w-8 h-8 rounded-full bg-gray-300"></div>
          </div>
        </header>

        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-2 space-y-6">
            <CalendarSection />
            <MeetingCard
              meetings={meetings}
              loading={loading}
              backendUrl={backendUrl}
            />
          </div>
          <div>
            <ChatSection />
          </div>
        </div>
      </main>
    </div>
  );
}


// 'use client';

// import { useState, useEffect } from 'react';

// export default function Dashboard() {
//   const [health, setHealth] = useState('Checking...');
//   const [meetings, setMeetings] = useState([]);
//   const [backendUrl] = useState(process.env.NEXT_PUBLIC_API_URL || 'https://b5462b7bbb65.ngrok-free.app');
//   const [error, setError] = useState('');
//   const [loading, setLoading] = useState(true);

//   // Enhanced fetch function with ngrok support
//   const apiCall = async (endpoint) => {
//     const url = `${backendUrl}${endpoint}`;

//     try {
//       const response = await fetch(url, {
//         method: 'GET',
//         headers: {
//           'Accept': 'application/json',
//           'Content-Type': 'application/json',
//           'ngrok-skip-browser-warning': 'true', // Skip ngrok warning
//         },
//         mode: 'cors',
//         credentials: 'omit', // Don't send cookies
//       });

//       // Check if response is ok
//       if (!response.ok) {
//         throw new Error(`HTTP ${response.status}: ${response.statusText}`);
//       }

//       // Check if response is actually JSON
//       const contentType = response.headers.get('content-type');
//       if (!contentType || !contentType.includes('application/json')) {
//         // If we get HTML instead of JSON, it might be ngrok warning
//         const text = await response.text();
//         if (text.includes('ngrok')) {
//           throw new Error('ngrok warning page detected - please visit the API URL directly first');
//         }
//         throw new Error(`Expected JSON but received: ${contentType}`);
//       }

//       return await response.json();
//     } catch (error) {
//       console.error(`API call failed for ${endpoint}:`, error);
//       throw error;
//     }
//   };

//   useEffect(() => {
//     const fetchData = async () => {
//       setLoading(true);

//       // Check backend health
//       try {
//         const healthData = await apiCall('/health');
//         setHealth(healthData.status === 'healthy' ? 'healthy' : 'unhealthy');
//       } catch (err) {
//         console.error('Health check failed:', err);
//         setHealth('Offline');
//         setError(`Health check failed: ${err.message}`);
//       }

//       // Get meetings
//       try {
//         const meetingsData = await apiCall('/get-meetings');

//         // Handle the response structure
//         if (Array.isArray(meetingsData)) {
//           setMeetings(meetingsData);
//         } else if (meetingsData.meetings && Array.isArray(meetingsData.meetings)) {
//           setMeetings(meetingsData.meetings);
//         } else {
//           console.warn('Unexpected meetings response format:', meetingsData);
//           setMeetings([]);
//         }

//         // Clear error if meetings fetch succeeded
//         if (error.includes('Health check failed')) {
//           setError('');
//         }
//       } catch (err) {
//         console.error('Failed to fetch meetings:', err);
//         setError(`API Error: ${err.message}`);
//         setMeetings([]);
//       }

//       setLoading(false);
//     };

//     fetchData();

//     // Refresh every 30 seconds
//     const interval = setInterval(fetchData, 30000);
//     return () => clearInterval(interval);
//   }, [backendUrl, error]);

//   return (
//     <div className="min-h-screen bg-gray-100 p-8">
//       <div className="max-w-4xl mx-auto">
//         <h1 className="text-3xl font-bold text-gray-900 mb-8">
//           🤖 ScrumBot Dashboard
//         </h1>

//         {/* Backend Status Card */}
//         <div className="bg-white rounded-lg shadow p-6 mb-6">
//           <h2 className="text-xl font-semibold mb-4">Backend Status</h2>
//           <div className="flex items-center mb-2">
//             <div className={`w-3 h-3 rounded-full mr-2 ${health === 'healthy' ? 'bg-green-500' :
//                 health === 'Offline' ? 'bg-red-500' : 'bg-yellow-500'
//               }`}></div>
//             <span className="text-gray-700">Backend: {health}</span>
//           </div>
//           <p className="text-sm text-gray-500">Connected to: {backendUrl}</p>

//           {error && (
//             <div className="mt-3 p-3 bg-red-100 border border-red-300 rounded">
//               <p className="text-sm text-red-700">⚠️ {error}</p>
//               {error.includes('ngrok warning') && (
//                 <div className="mt-2">
//                   <p className="text-xs text-red-600">
//                     Quick fix: <a
//                       href={backendUrl}
//                       target="_blank"
//                       rel="noopener noreferrer"
//                       className="underline font-medium"
//                     >
//                       Click here to visit the API directly
//                     </a> and approve the ngrok warning, then refresh this page.
//                   </p>
//                 </div>
//               )}
//             </div>
//           )}
//         </div>

//         {/* Recent Meetings Card */}
//         <div className="bg-white rounded-lg shadow p-6 mb-6">
//           <h2 className="text-xl font-semibold mb-4">Recent Meetings</h2>

//           {loading ? (
//             <div className="text-center py-4">
//               <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
//               <p className="text-gray-500 mt-2">Loading meetings...</p>
//             </div>
//           ) : meetings.length === 0 ? (
//             <div className="text-center py-8">
//               <div className="text-6xl mb-4">🎤</div>
//               <p className="text-gray-500 mb-4">No meetings yet. Start a meeting with the Chrome extension!</p>
//               <div className="text-sm text-gray-400 space-y-1">
//                 <p>📱 Install the Chrome extension</p>
//                 <p>🎥 Join a Google Meet, Zoom, or Teams call</p>
//                 <p>🎙️ Start recording to see transcripts here</p>
//               </div>
//             </div>
//           ) : (
//             <div className="space-y-4">
//               {meetings.map((meeting, index) => (
//                 <div key={meeting.id || index} className="border border-gray-200 rounded p-4 hover:bg-gray-50">
//                   <h3 className="font-medium text-gray-900">{meeting.title || 'Untitled Meeting'}</h3>
//                   <p className="text-sm text-gray-500">{meeting.created_at || 'Just created'}</p>
//                   {meeting.transcript && (
//                     <p className="text-sm text-gray-700 mt-2 truncate">{meeting.transcript}</p>
//                   )}
//                 </div>
//               ))}
//             </div>
//           )}
//         </div>

//         {/* Debug Panel (only show if there are errors) */}
//         {error && (
//           <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
//             <h3 className="text-sm font-semibold text-yellow-800 mb-2">🔧 Debug Information</h3>
//             <div className="text-xs text-yellow-700 space-y-1">
//               <p><strong>Backend URL:</strong> {backendUrl}</p>
//               <p><strong>Error:</strong> {error}</p>
//               <p><strong>Health Status:</strong> {health}</p>
//               <p><strong>Meetings Count:</strong> {meetings.length}</p>
//             </div>
//             <div className="mt-3 flex gap-2">
//               <a
//                 href={`${backendUrl}/health`}
//                 target="_blank"
//                 rel="noopener noreferrer"
//                 className="text-xs bg-yellow-200 hover:bg-yellow-300 px-2 py-1 rounded"
//               >
//                 Test Health Endpoint
//               </a>
//               <a
//                 href={`${backendUrl}/get-meetings`}
//                 target="_blank"
//                 rel="noopener noreferrer"
//                 className="text-xs bg-yellow-200 hover:bg-yellow-300 px-2 py-1 rounded"
//               >
//                 Test Meetings Endpoint
//               </a>
//             </div>
//           </div>
//         )}

//         {/* Hackathon Demo Card */}
//         <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-6">
//           <h3 className="text-lg font-semibold text-blue-800 mb-2">🚀 TiDB AgentX Hackathon Demo</h3>
//           <p className="text-blue-700 mb-4">
//             This is a live demo of ScrumBot - an AI-powered meeting intelligence system built for the TiDB AgentX Hackathon 2025.
//           </p>

//           <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
//             <span className="bg-blue-200 text-blue-800 px-3 py-1 rounded-full text-sm font-medium text-center">
//               Multi-step AI
//             </span>
//             <span className="bg-green-200 text-green-800 px-3 py-1 rounded-full text-sm font-medium text-center">
//               TiDB Vector Search
//             </span>
//             <span className="bg-purple-200 text-purple-800 px-3 py-1 rounded-full text-sm font-medium text-center">
//               Real-time Transcription
//             </span>
//             <span className="bg-orange-200 text-orange-800 px-3 py-1 rounded-full text-sm font-medium text-center">
//               Chrome Extension
//             </span>
//           </div>

//           <div className="flex flex-wrap gap-3 text-sm">
//             <a
//               href={backendUrl}
//               target="_blank"
//               rel="noopener noreferrer"
//               className="text-blue-600 hover:text-blue-800 font-medium"
//             >
//               🔗 API Endpoint
//             </a>
//             <span className="text-gray-400">•</span>
//             <span className="text-gray-600">
//               Status: <span className={health === 'healthy' ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
//                 {health}
//               </span>
//             </span>
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// }