import { useEffect, useRef, useState } from 'react';
import { config } from '@/lib/config';

export const useWebSocket = (meetingId, onTranscriptUpdate) => {
  const ws = useRef(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!meetingId) return;

    const wsUrl = `${config.websocketUrl}/ws`;
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      setIsConnected(true);
      ws.current.send(JSON.stringify({
        type: 'register_meeting',
        meeting_id: meetingId
      }));
    };

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'transcript_update' && data.meeting_id === meetingId) {
          onTranscriptUpdate(data);
        }
      } catch (err) {
        console.error('WebSocket message error:', err);
      }
    };

    ws.current.onclose = () => setIsConnected(false);
    ws.current.onerror = () => setIsConnected(false);

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [meetingId, onTranscriptUpdate]);

  return { isConnected };
};