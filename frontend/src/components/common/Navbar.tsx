import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { BookOpen, Shield, User as UserIcon, LogOut } from 'lucide-react';

interface NavbarProps {
  currentTab: string;
  onTabChange: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, onTabChange }) => {
  const { user, logout } = useAuth();

  return (
    <header style={{ background: '#ffffff', borderBottom: '1px solid #e2e8f0', position: 'sticky', top: 0, zIndex: 40 }}>
      <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '0.75rem 1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ background: '#0f172a', color: '#ffffff', padding: '0.4rem', borderRadius: '6px', display: 'flex', alignItems: 'center' }}>
            <BookOpen size={20} />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '1rem', letterSpacing: '-0.02em', color: '#0f172a' }}>BookLeaf Publishing</div>
            <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 500 }}>Author Support & Operations Portal</div>
          </div>
        </div>

        {/* Navigation Tabs */}
        {user && (
          <nav style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            {user.role === 'AUTHOR' ? (
              <>
                <button
                  onClick={() => onTabChange('dashboard')}
                  className={`btn btn-sm ${currentTab === 'dashboard' ? 'btn-primary' : 'btn-secondary'}`}
                >
                  Dashboard
                </button>
                <button
                  onClick={() => onTabChange('books')}
                  className={`btn btn-sm ${currentTab === 'books' ? 'btn-primary' : 'btn-secondary'}`}
                >
                  My Books
                </button>
                <button
                  onClick={() => onTabChange('tickets')}
                  className={`btn btn-sm ${currentTab === 'tickets' || currentTab === 'ticket_detail' ? 'btn-primary' : 'btn-secondary'}`}
                >
                  Support Tickets
                </button>
                <button
                  onClick={() => onTabChange('timeline')}
                  className={`btn btn-sm ${currentTab === 'timeline' ? 'btn-primary' : 'btn-secondary'}`}
                >
                  Communication Timeline
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => onTabChange('admin_queue')}
                  className={`btn btn-sm ${currentTab === 'admin_queue' ? 'btn-primary' : 'btn-secondary'}`}
                >
                  Support Queue
                </button>
                <button
                  onClick={() => onTabChange('admin_workspace')}
                  className={`btn btn-sm ${currentTab === 'admin_workspace' ? 'btn-primary' : 'btn-secondary'}`}
                >
                  Ticket Workspace
                </button>
              </>
            )}
          </nav>
        )}

        {/* User Profile & Logout */}
        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {/* Profile Tag */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', fontSize: '0.825rem', color: '#334155' }}>
              {user.role === 'ADMIN' ? <Shield size={16} color="#0284c7" /> : <UserIcon size={16} color="#059669" />}
              <span style={{ fontWeight: 600 }}>{user.fullName || user.email}</span>
              <span className={`badge ${user.role === 'ADMIN' ? 'badge-open' : 'badge-resolved'}`}>
                {user.role}
              </span>
            </div>

            {/* Logout */}
            <button
              onClick={logout}
              title="Sign Out"
              className="btn btn-secondary btn-sm"
              style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.775rem' }}
            >
              <LogOut size={14} /> Sign Out
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
