import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../lib/api';
import type { TimelineEvent } from '../../types';
import { ArrowRight } from 'lucide-react';

interface AuthorTimelineViewProps {
  onOpenTicket: (ticketNumber: string) => void;
}

export const AuthorTimelineView: React.FC<AuthorTimelineViewProps> = ({ onOpenTicket }) => {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchTimeline() {
      try {
        setLoading(true);
        const res = await apiRequest<{ success: boolean; data: TimelineEvent[] }>('/author/timeline');
        setEvents(res.data);
      } catch (err: any) {
        setError(err.message || 'Failed to load timeline');
      } finally {
        setLoading(false);
      }
    }
    fetchTimeline();
  }, []);

  const getEventBadgeColor = (type: string) => {
    switch (type) {
      case 'TICKET_CREATED': return '#0284c7';
      case 'MESSAGE_ADDED': return '#059669';
      case 'RESPONSE_SENT': return '#2563eb';
      case 'STATUS_CHANGED': return '#d97706';
      case 'RESOLVED': return '#16a34a';
      case 'CLOSED': return '#475569';
      case 'DUPLICATE_LINKED': return '#7c3aed';
      default: return '#64748b';
    }
  };

  if (loading) {
    return <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>Loading operational timeline...</div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div>
        <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }}>Author Communication Timeline</h1>
        <p style={{ fontSize: '0.8rem', color: '#64748b' }}>
          Chronological audit history of all operational events, responses, and state updates across your publishing requests
        </p>
      </div>

      {error && <div style={{ color: '#dc2626', fontSize: '0.875rem' }}>{error}</div>}

      <div className="card">
        {events.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>
            No communication events recorded yet.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {events.map((evt, idx) => (
              <div key={evt.id} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                
                {/* Timeline Pin */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: getEventBadgeColor(evt.event_type), marginTop: '0.35rem' }} />
                  {idx < events.length - 1 && (
                    <div style={{ width: '2px', flexGrow: 1, backgroundColor: '#e2e8f0', minHeight: '35px', marginTop: '0.25rem' }} />
                  )}
                </div>

                {/* Event Details */}
                <div style={{ flexGrow: 1, background: '#f8fafc', padding: '0.75rem 1rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.25rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.85rem', color: '#0f172a' }}>
                        {evt.event_type.replace(/_/g, ' ')}
                      </span>
                      {evt.ticket_number && (
                        <button
                          onClick={() => onOpenTicket(evt.ticket_number!)}
                          style={{ background: 'transparent', border: 'none', color: '#2563eb', fontWeight: 600, fontSize: '0.8rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.2rem' }}
                        >
                          {evt.ticket_number} <ArrowRight size={12} />
                        </button>
                      )}
                    </div>
                    <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                      {new Date(evt.created_at).toLocaleString()}
                    </span>
                  </div>

                  {evt.ticket_subject && (
                    <div style={{ fontSize: '0.8rem', color: '#334155', fontWeight: 500, marginBottom: '0.35rem' }}>
                      Subject: {evt.ticket_subject}
                    </div>
                  )}

                  {/* Metadata pill displays */}
                  {evt.metadata && Object.keys(evt.metadata).length > 0 && (
                    <div style={{ fontSize: '0.75rem', color: '#475569', display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.25rem' }}>
                      {evt.metadata.new_status && (
                        <span style={{ background: '#ffffff', padding: '0.15rem 0.4rem', borderRadius: '4px', border: '1px solid #cbd5e1' }}>
                          Status: <strong>{evt.metadata.old_status || 'INIT'}</strong> → <strong>{evt.metadata.new_status}</strong>
                        </span>
                      )}
                      {evt.metadata.category && (
                        <span style={{ background: '#ffffff', padding: '0.15rem 0.4rem', borderRadius: '4px', border: '1px solid #cbd5e1' }}>
                          Category: <strong>{evt.metadata.category}</strong>
                        </span>
                      )}
                      {evt.metadata.priority && (
                        <span style={{ background: '#ffffff', padding: '0.15rem 0.4rem', borderRadius: '4px', border: '1px solid #cbd5e1' }}>
                          Priority: <strong>{evt.metadata.priority}</strong>
                        </span>
                      )}
                      {evt.metadata.target_ticket_number && (
                        <span style={{ background: '#ffffff', padding: '0.15rem 0.4rem', borderRadius: '4px', border: '1px solid #cbd5e1' }}>
                          Linked to: <strong>{evt.metadata.target_ticket_number}</strong>
                        </span>
                      )}
                    </div>
                  )}
                </div>

              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
