import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react';
import { useAuth } from './AuthContext';

export interface RealtimeEvent {
  event: string;
  ticket_id: string;
  payload?: any;
}

interface RealtimeContextType {
  lastEvent: RealtimeEvent | null;
  subscribe: (handler: (event: RealtimeEvent) => void) => () => void;
  notification: string | null;
}

const RealtimeContext = createContext<RealtimeContextType>({
  lastEvent: null,
  subscribe: () => () => {},
  notification: null,
});

export const RealtimeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { token } = useAuth();
  const [lastEvent, setLastEvent] = useState<RealtimeEvent | null>(null);
  const [notification, setNotification] = useState<string | null>(null);
  const subscribersRef = useRef<Set<(event: RealtimeEvent) => void>>(new Set());

  const subscribe = useCallback((handler: (event: RealtimeEvent) => void) => {
    subscribersRef.current.add(handler);
    return () => {
      subscribersRef.current.delete(handler);
    };
  }, []);

  useEffect(() => {
    if (!token) return;

    // Resolve WebSocket URL supporting cross-domain deployment (Vercel frontend -> Render backend)
    const resolveWsUrl = (): string => {
      const explicitWs = (import.meta.env.VITE_WS_URL || import.meta.env.VITE_WS_BASE_URL || '').trim();
      if (explicitWs) {
        const clean = explicitWs.replace(/\/+$/, '');
        return clean.endsWith('/ws') ? clean : `${clean}/api/v1/ws`;
      }
      const apiUrl = (import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || '').trim();
      if (apiUrl && apiUrl.startsWith('http')) {
        const wsScheme = apiUrl.startsWith('https:') ? 'wss:' : 'ws:';
        const hostAndPath = apiUrl.replace(/^https?:\/\//, '').replace(/\/api\/v1\/?$/, '').replace(/\/+$/, '');
        return `${wsScheme}//${hostAndPath}/api/v1/ws`;
      }
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      return `${protocol}//${window.location.host}/api/v1/ws`;
    };

    const wsUrl = resolveWsUrl();
    let socket: WebSocket | null = null;
    let reconnectTimeout: any = null;

    const connectWebSocket = () => {
      try {
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
          console.log('[WebSocket] Connected to BookLeaf Realtime Gateway');
          // Secure handshake: send authentication token via WebSocket frame
          socket?.send(JSON.stringify({ type: 'auth', token }));
        };

        socket.onmessage = (rawEvent) => {
          try {
            const data: RealtimeEvent = JSON.parse(rawEvent.data);
            if (data.event) {
              setLastEvent(data);
              // Notify all subscribed views (AuthorTicketView, AdminWorkspace, etc.)
              subscribersRef.current.forEach((handler) => {
                try {
                  handler(data);
                } catch (e) {
                  console.error('[WebSocket] Error in event subscriber:', e);
                }
              });

              // Set banner toast
              const formattedEvent = data.event.replace(/_/g, ' ');
              setNotification(`Live update on #${data.ticket_id || 'ticket'}: ${formattedEvent}`);
              setTimeout(() => setNotification(null), 4000);
            }
          } catch (e) {
            // Heartbeat or ping frame
          }
        };

        socket.onclose = () => {
          console.log('[WebSocket] Connection closed. Reconnecting in 3s...');
          reconnectTimeout = setTimeout(connectWebSocket, 3000);
        };

        socket.onerror = (err) => {
          console.warn('[WebSocket] Connection notice:', err);
        };
      } catch (err) {
        reconnectTimeout = setTimeout(connectWebSocket, 3000);
      }
    };

    connectWebSocket();

    return () => {
      if (socket) socket.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, [token]);

  return (
    <RealtimeContext.Provider value={{ lastEvent, subscribe, notification }}>
      {children}
    </RealtimeContext.Provider>
  );
};

export const useRealtime = () => useContext(RealtimeContext);
