import React, { useEffect, useState } from 'react';
import type { AuthorProfile } from '../../types';
import { apiRequest } from '../../lib/api';
import { Book, Clock, AlertCircle, CheckCircle, IndianRupee } from 'lucide-react';

interface AuthorDashboardProps {
  onNavigate: (tab: string) => void;
}

export const AuthorDashboard: React.FC<AuthorDashboardProps> = ({ onNavigate }) => {
  const [profile, setProfile] = useState<AuthorProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchProfile() {
      try {
        setLoading(true);
        const res = await apiRequest<{ success: boolean; data: AuthorProfile }>('/author/profile');
        setProfile(res.data);
      } catch (err: any) {
        setError(err.message || 'Failed to load profile');
      } finally {
        setLoading(false);
      }
    }
    fetchProfile();
  }, []);

  if (loading) {
    return <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>Loading author dashboard...</div>;
  }

  if (error || !profile) {
    return <div style={{ padding: '2rem', color: '#dc2626' }}>{error || 'Profile unavailable'}</div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      
      {/* Top Banner */}
      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }}>
            Welcome back, {profile.pen_name}
          </h1>
          <p style={{ fontSize: '0.875rem', color: '#64748b' }}>
            Author ID: <strong>{profile.author_id}</strong> | Email: {profile.email}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button onClick={() => onNavigate('tickets')} className="btn btn-primary btn-sm">
            Raise Support Request
          </button>
          <button onClick={() => onNavigate('books')} className="btn btn-secondary btn-sm">
            View Catalog
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
        
        {/* Books Card */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b', fontSize: '0.8rem', fontWeight: 600 }}>
            <span>TOTAL BOOKS</span>
            <Book size={16} color="#2563eb" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#0f172a' }}>
            {profile.total_books}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', display: 'flex', gap: '0.75rem' }}>
            <span>Published: <strong>{profile.published_books}</strong></span>
            <span>In Production: <strong>{profile.books_in_production}</strong></span>
          </div>
        </div>

        {/* Royalty Earned */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b', fontSize: '0.8rem', fontWeight: 600 }}>
            <span>ROYALTY EARNED</span>
            <IndianRupee size={16} color="#059669" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#0f172a' }}>
            ₹{Number(profile.total_royalties_earned).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#059669' }}>
            Cumulative sales across all distribution channels
          </div>
        </div>

        {/* Royalty Paid */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b', fontSize: '0.8rem', fontWeight: 600 }}>
            <span>ROYALTY PAID</span>
            <CheckCircle size={16} color="#16a34a" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#0f172a' }}>
            ₹{Number(profile.total_royalties_paid).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
            Disbursed to registered bank account
          </div>
        </div>

        {/* Royalty Pending */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b', fontSize: '0.8rem', fontWeight: 600 }}>
            <span>ROYALTY PENDING</span>
            <Clock size={16} color="#d97706" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: Number(profile.total_royalties_pending) > 0 ? '#b45309' : '#0f172a' }}>
            ₹{Number(profile.total_royalties_pending).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#b45309' }}>
            Quarterly disbursement cycle (within 45 days of quarter end; min. ₹1,000)
          </div>
        </div>

        {/* Open Tickets */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b', fontSize: '0.8rem', fontWeight: 600 }}>
            <span>OPEN TICKETS</span>
            <AlertCircle size={16} color="#ef4444" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: profile.open_tickets > 0 ? '#b91c1c' : '#0f172a' }}>
            {profile.open_tickets}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
            Active requests with publishing desk
          </div>
        </div>

      </div>

      {/* Operational Policies Quick Reference */}
      <div className="card">
        <h2 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '0.75rem', color: '#0f172a' }}>
          BookLeaf Operations Guidance & Policy Standards
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', fontSize: '0.8rem', color: '#475569' }}>
          <div style={{ background: '#f8fafc', padding: '0.75rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
            <div style={{ fontWeight: 600, color: '#0f172a', marginBottom: '0.25rem' }}>80/20 Royalty Split & Quarterly Payouts</div>
            80% of net profit (MRP minus printing, channel commission & shipping) to author. Calculated quarterly and paid within 45 days (₹1,000 rollover threshold).
          </div>
          <div style={{ background: '#f8fafc', padding: '0.75rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
            <div style={{ fontWeight: 600, color: '#0f172a', marginBottom: '0.25rem' }}>Printing Quality & In-House Facility</div>
            Managed via Delhi in-house facility, Repro India, and Epitome Books. Turnaround is 5–7 business days; free reprints arranged for verified batch defects.
          </div>
          <div style={{ background: '#f8fafc', padding: '0.75rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
            <div style={{ fontWeight: 600, color: '#0f172a', marginBottom: '0.25rem' }}>9-Stage Production & Distribution Sync</div>
            Tracked across 9 clear milestones. Channel listings on Amazon/Flipkart/BookLeaf Store re-sync within 24–48 hours if marked unavailable.
          </div>
        </div>
      </div>

    </div>
  );
};
