import React, { useEffect, useState } from 'react';
import type { Ticket } from '../../types';
import { apiRequest } from '../../lib/api';
import { Search, ArrowRight, RefreshCw } from 'lucide-react';

interface AdminQueueProps {
  onOpenWorkspace: (ticketNumber: string) => void;
}

export const AdminQueue: React.FC<AdminQueueProps> = ({ onOpenWorkspace }) => {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [priorityFilter, setPriorityFilter] = useState<string>('');
  const [search, setSearch] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('recent');

  useEffect(() => {
    fetchQueue();
  }, [statusFilter, categoryFilter, priorityFilter, sortBy]);

  async function fetchQueue() {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      if (categoryFilter) params.append('category', categoryFilter);
      if (priorityFilter) params.append('priority', priorityFilter);
      if (search) params.append('search', search);
      if (sortBy) params.append('sort_by', sortBy);

      const res = await apiRequest<{ success: boolean; data: { total: number; items: Ticket[] } }>(
        `/admin/tickets?${params.toString()}`
      );
      setTickets(res.data.items);
      setTotalCount(res.data.total);
    } catch (err: any) {
      setError(err.message || 'Failed to load ticket queue');
    } finally {
      setLoading(false);
    }
  }

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchQueue();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      
      {/* Queue Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }}>Operational Support Queue</h1>
          <p style={{ fontSize: '0.8rem', color: '#64748b' }}>
            Author support requests with classification, deterministic duplicate detection, and triage priority
          </p>
        </div>
        <button onClick={fetchQueue} className="btn btn-secondary btn-sm">
          <RefreshCw size={13} /> Refresh Queue ({totalCount})
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="card" style={{ padding: '0.85rem 1rem' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'center' }}>
          
          {/* Search */}
          <form onSubmit={handleSearchSubmit} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', flex: 1, minWidth: '220px' }}>
            <div style={{ position: 'relative', width: '100%' }}>
              <Search size={15} style={{ position: 'absolute', left: '0.6rem', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
              <input
                type="text"
                placeholder="Search ticket #, subject, author, book..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{ width: '100%', padding: '0.45rem 0.5rem 0.45rem 2rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
              />
            </div>
          </form>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.8rem', background: '#ffffff' }}
          >
            <option value="">All Statuses</option>
            <option value="OPEN">OPEN</option>
            <option value="IN_PROGRESS">IN PROGRESS</option>
            <option value="RESOLVED">RESOLVED</option>
            <option value="CLOSED">CLOSED</option>
          </select>

          {/* Priority Filter */}
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            style={{ padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.8rem', background: '#ffffff' }}
          >
            <option value="">All Priorities</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>

          {/* Category Filter */}
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            style={{ padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.8rem', background: '#ffffff' }}
          >
            <option value="">All Categories</option>
            <option value="ROYALTY_PAYMENT">ROYALTY PAYMENT</option>
            <option value="ISBN_METADATA">ISBN & METADATA</option>
            <option value="PRINTING_QUALITY">PRINTING & QUALITY</option>
            <option value="DISTRIBUTION_AVAILABILITY">DISTRIBUTION & AVAILABILITY</option>
            <option value="BOOK_STATUS">BOOK STATUS</option>
            <option value="GENERAL">GENERAL</option>
          </select>

          {/* Sort Option */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            style={{ padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.8rem', background: '#ffffff' }}
          >
            <option value="recent">Recently Updated</option>
            <option value="highest_priority">Highest Priority First</option>
            <option value="oldest_unresolved">Oldest Unresolved</option>
          </select>

        </div>
      </div>

      {error && <div style={{ color: '#dc2626', fontSize: '0.875rem' }}>{error}</div>}

      {/* Queue Table */}
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Ticket #</th>
              <th>Author</th>
              <th>Subject</th>
              <th>Referenced Book</th>
              <th>Priority</th>
              <th>Category</th>
              <th>Status</th>
              <th>Assignee</th>
              <th>Last Updated</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={10} style={{ textAlign: 'center', padding: '2.5rem', color: '#64748b' }}>
                  Loading operational queue...
                </td>
              </tr>
            ) : tickets.length === 0 ? (
              <tr>
                <td colSpan={10} style={{ textAlign: 'center', padding: '2.5rem', color: '#94a3b8' }}>
                  No tickets matching active filters.
                </td>
              </tr>
            ) : (
              tickets.map((t) => (
                <tr key={t.id} style={{ cursor: 'pointer' }} onClick={() => onOpenWorkspace(t.ticket_number)}>
                  <td style={{ fontFamily: 'monospace', fontWeight: 700, color: '#0f172a' }}>
                    {t.ticket_number}
                  </td>
                  <td>
                    <div style={{ fontWeight: 600, color: '#0f172a' }}>{t.author ? t.author.pen_name : '—'}</div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{t.author?.author_id}</div>
                  </td>
                  <td style={{ fontWeight: 600, maxWidth: '280px' }}>
                    {t.subject}
                  </td>
                  <td>
                    {t.book ? (
                      <div>
                        <div style={{ fontSize: '0.8rem', color: '#1e293b' }}>{t.book.title}</div>
                        <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{t.book.book_id}</div>
                      </div>
                    ) : (
                      <span style={{ color: '#94a3b8', fontSize: '0.8rem' }}>Account Level</span>
                    )}
                  </td>
                  <td>
                    {t.priority ? (
                      <span className={`badge badge-${t.priority.toLowerCase()}`}>
                        {t.priority}
                      </span>
                    ) : (
                      <span style={{ color: '#94a3b8', fontSize: '0.75rem' }}>Pending</span>
                    )}
                  </td>
                  <td>
                    {t.category ? (
                      <span className="badge badge-category">
                        {t.category.replace('_', ' ')}
                      </span>
                    ) : (
                      <span style={{ color: '#94a3b8', fontSize: '0.75rem' }}>Unclassified</span>
                    )}
                  </td>
                  <td>
                    <span className={`badge badge-${t.status.toLowerCase()}`}>
                      {t.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.8rem', color: t.assigned_admin_name ? '#0f172a' : '#94a3b8' }}>
                      {t.assigned_admin_name || 'Unassigned'}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.8rem', color: '#64748b' }}>
                    {new Date(t.updated_at).toLocaleString()}
                  </td>
                  <td>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onOpenWorkspace(t.ticket_number);
                      }}
                      className="btn btn-secondary btn-sm"
                    >
                      Workspace <ArrowRight size={13} />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

    </div>
  );
};
