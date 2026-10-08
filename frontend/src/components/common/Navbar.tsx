import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { BookOpen, Shield, User as UserIcon, LogOut, ArrowRightLeft } from 'lucide-react';

interface NavbarProps {
  currentTab: string;
  onTabChange: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, onTabChange }) => {
  const { user, logout, switchUser } = useAuth();

  const demoAccounts = [
    { label: 'Admin: Operations Desk', email: 'admin@bookleaf.com', pass: 'Admin@BookLeaf2026!' },
    { label: 'AUTH001: Priya Sharma (Fiction / Pending Royalties)', email: 'priya.sharma@bookleaf.com', pass: 'Author@BookLeaf2026!' },
    { label: 'AUTH002: Rohit Verma (Self-Help / Zero Royalties)', email: 'rohit.verma@bookleaf.com', pass: 'Author@BookLeaf2026!' },
    { label: 'AUTH003: Ananya Iyer (Poetry / High Royalties)', email: 'ananya.iyer@bookleaf.com', pass: 'Author@BookLeaf2026!' },
    { label: 'AUTH004: Vikram Malhotra (Thriller / In Production)', email: 'vikram.malhotra@bookleaf.com', pass: 'Author@BookLeaf2026!' },
    { label: 'AUTH005: Sneha Patel (Romance / Ingram Spark)', email: 'sneha.patel@bookleaf.com', pass: 'Author@BookLeaf2026!' },
    { label: 'AUTH006: Amitav Ghosh (Historical / Replika Press)', email: 'amitav.ghosh@bookleaf.com', pass: 'Author@BookLeaf2026!' },
    { label: 'AUTH007: Kavita Krishnan (Non-Fiction / Thomson Press)', email: 'kavita.krishnan@bookleaf.com', pass: 'Author@BookLeaf2026!' },
    { label: 'AUTH008: Devdutt Pattanaik (Mythology / Active Sales)', email: 'devdutt.pattanaik@bookleaf.com', pass: 'Author@BookLeaf2026!' },
    { label: 'AUTH009: Arundhati Roy (Literary / Multiple Books)', email: 'arundhati.roy@bookleaf.com', pass: 'Author@BookLeaf2026!' },
    { label: 'AUTH010: Chetan Bhagat (Commercial / High Volume)', email: 'chetan.bhagat@bookleaf.com', pass: 'Author@BookLeaf2026!' },
  ];

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

        {/* User context & Quick Switch */}
        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            {/* Quick Switch Dropdown */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', background: '#f8fafc', padding: '0.25rem 0.5rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
              <ArrowRightLeft size={14} color="#64748b" />
              <select
                aria-label="Switch User Account"
                style={{ background: 'transparent', border: 'none', fontSize: '0.75rem', color: '#334155', outline: 'none', cursor: 'pointer' }}
                value={user.email}
                onChange={(e) => {
                  const target = demoAccounts.find(d => d.email === e.target.value);
                  if (target) {
                    switchUser(target.email, target.pass);
                  }
                }}
              >
                {demoAccounts.map(d => (
                  <option key={d.email} value={d.email}>{d.label}</option>
                ))}
              </select>
            </div>

            {/* Profile Tag */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', color: '#334155' }}>
              {user.role === 'ADMIN' ? <Shield size={16} color="#0284c7" /> : <UserIcon size={16} color="#059669" />}
              <span style={{ fontWeight: 600 }}>{user.fullName}</span>
              <span className={`badge ${user.role === 'ADMIN' ? 'badge-open' : 'badge-resolved'}`}>
                {user.role}
              </span>
            </div>

            {/* Logout */}
            <button
              onClick={logout}
              title="Sign Out"
              className="btn btn-secondary btn-sm"
              style={{ padding: '0.35rem' }}
            >
              <LogOut size={15} />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
