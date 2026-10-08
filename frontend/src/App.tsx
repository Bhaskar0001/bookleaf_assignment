import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/common/Navbar';
import { Login } from './pages/auth/Login';
import { AuthorDashboard } from './pages/author/AuthorDashboard';
import { AuthorBooks } from './pages/author/AuthorBooks';
import { AuthorTickets } from './pages/author/AuthorTickets';
import { AuthorTicketView } from './pages/author/AuthorTicketView';
import { AuthorTimelineView } from './pages/author/AuthorTimelineView';
import { AdminQueue } from './pages/admin/AdminQueue';
import { AdminWorkspace } from './pages/admin/AdminWorkspace';

const MainLayout: React.FC = () => {
  const { user, token, loading } = useAuth();
  
  // Navigation State
  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [selectedTicketNumber, setSelectedTicketNumber] = useState<string>('');
  const [preselectedBookId, setPreselectedBookId] = useState<string | null>(null);

  // Real-time notification banner
  const [realtimeNotification, setRealtimeNotification] = useState<string | null>(null);

  // WebSocket Connection for Live Events
  useEffect(() => {
    if (!token) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v1/ws?token=${token}`;
    let socket: WebSocket | null = null;
    let reconnectTimeout: any = null;

    const connectWebSocket = () => {
      try {
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
          console.log('[WebSocket] Connected to BookLeaf realtime gateway');
        };

        socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.event) {
              setRealtimeNotification(`Real-time update: ${data.event.replace(/_/g, ' ')}`);
              setTimeout(() => setRealtimeNotification(null), 4000);
            }
          } catch (e) {
            // Heartbeat
          }
        };

        socket.onclose = () => {
          console.log('[WebSocket] Disconnected. Reconnecting in 3 seconds...');
          reconnectTimeout = setTimeout(connectWebSocket, 3000);
        };

        socket.onerror = (err) => {
          console.warn('[WebSocket] Encountered connection event:', err);
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

  // Adjust default tab based on user role
  useEffect(() => {
    if (user) {
      if (user.role === 'ADMIN') {
        setCurrentTab('admin_queue');
      } else {
        setCurrentTab('dashboard');
      }
    }
  }, [user?.role]);

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
        Initializing BookLeaf Portal...
      </div>
    );
  }

  if (!user) {
    return <Login />;
  }

  const handleOpenAuthorTicket = (ticketNum: string) => {
    setSelectedTicketNumber(ticketNum);
    setCurrentTab('ticket_detail');
  };

  const handleOpenAdminWorkspace = (ticketNum: string) => {
    setSelectedTicketNumber(ticketNum);
    setCurrentTab('admin_workspace');
  };

  const handleSelectBookForTicket = (bookId: string) => {
    setPreselectedBookId(bookId);
    setCurrentTab('tickets');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar currentTab={currentTab} onTabChange={setCurrentTab} />

      {/* Real-time Notification Banner */}
      {realtimeNotification && (
        <div style={{ background: '#0f172a', color: '#ffffff', padding: '0.4rem 1rem', fontSize: '0.75rem', textAlign: 'center', transition: 'all 0.3s ease' }}>
          {realtimeNotification}
        </div>
      )}

      {/* Content Area */}
      <main style={{ flexGrow: 1, maxWidth: '1280px', width: '100%', margin: '0 auto', padding: '1.5rem' }}>
        {/* AUTHOR VIEWS */}
        {user.role === 'AUTHOR' && (
          <>
            {currentTab === 'dashboard' && <AuthorDashboard onNavigate={setCurrentTab} />}
            {currentTab === 'books' && <AuthorBooks onSelectBookForTicket={handleSelectBookForTicket} />}
            {currentTab === 'tickets' && (
              <AuthorTickets
                onOpenTicket={handleOpenAuthorTicket}
                preselectedBookId={preselectedBookId}
                onClearPreselectedBook={() => setPreselectedBookId(null)}
              />
            )}
            {currentTab === 'ticket_detail' && (
              <AuthorTicketView
                ticketNumber={selectedTicketNumber}
                onBack={() => setCurrentTab('tickets')}
              />
            )}
            {currentTab === 'timeline' && <AuthorTimelineView onOpenTicket={handleOpenAuthorTicket} />}
          </>
        )}

        {/* ADMIN VIEWS */}
        {user.role === 'ADMIN' && (
          <>
            {currentTab === 'admin_queue' && (
              <AdminQueue onOpenWorkspace={handleOpenAdminWorkspace} />
            )}
            {currentTab === 'admin_workspace' && (
              <AdminWorkspace
                ticketNumber={selectedTicketNumber || 'BL-10001'}
                onBackToQueue={() => setCurrentTab('admin_queue')}
              />
            )}
          </>
        )}
      </main>
    </div>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <MainLayout />
    </AuthProvider>
  );
}
