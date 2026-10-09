import React, { useEffect, useState, useCallback } from 'react';
import { apiRequest } from '../../lib/api';
import { useRealtime } from '../../context/RealtimeContext';
import { ArrowLeft, Send, Clock, BookOpen, CheckCircle2, Paperclip, X } from 'lucide-react';
import { AttachmentViewer } from '../../components/common/AttachmentViewer';

interface AuthorTicketViewProps {
  ticketNumber: string;
  onBack: () => void;
}

export const AuthorTicketView: React.FC<AuthorTicketViewProps> = ({ ticketNumber, onBack }) => {
  const { subscribe } = useRealtime();
  const [ticket, setTicket] = useState<any | null>(null);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [replyText, setReplyText] = useState<string>('');
  const [replyAttachmentName, setReplyAttachmentName] = useState<string>('');
  const [replyAttachmentData, setReplyAttachmentData] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [sending, setSending] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTicketData = useCallback(async (isSilent: boolean = false) => {
    try {
      if (!isSilent) setLoading(true);
      const res = await apiRequest(`/author/tickets/${ticketNumber}`);
      setTicket(res.data);

      // Fetch ticket-specific timeline directly from dedicated endpoint
      const tlRes = await apiRequest(`/author/tickets/${ticketNumber}/timeline`);
      setTimeline(tlRes.data || []);
    } catch (err: any) {
      if (!isSilent) setError(err.message || 'Failed to load ticket details');
    } finally {
      if (!isSilent) setLoading(false);
    }
  }, [ticketNumber]);

  useEffect(() => {
    fetchTicketData(false);
  }, [fetchTicketData]);

  // Live WebSocket update subscription
  useEffect(() => {
    const unsubscribe = subscribe((evt) => {
      if (evt.ticket_id === ticketNumber) {
        console.log(`[AuthorTicketView] Live event received for #${ticketNumber}:`, evt.event);
        fetchTicketData(true);
      }
    });
    return unsubscribe;
  }, [ticketNumber, subscribe, fetchTicketData]);

  const handleSendReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!replyText.trim() || sending) return;

    try {
      setSending(true);
      let fullMsg = replyText.trim();
      if (replyAttachmentName && replyAttachmentData) {
        fullMsg += `\n\n[Attachment: ${replyAttachmentName}](${replyAttachmentData})`;
      }

      await apiRequest(`/author/tickets/${ticketNumber}/messages`, {
        method: 'POST',
        body: JSON.stringify({ message: fullMsg }),
      });
      setReplyText('');
      setReplyAttachmentName('');
      setReplyAttachmentData('');
      await fetchTicketData();
    } catch (err: any) {
      setError(err.message || 'Failed to send reply');
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>Loading ticket details...</div>;
  }

  if (error || !ticket) {
    return (
      <div style={{ padding: '2rem' }}>
        <button onClick={onBack} className="btn btn-secondary btn-sm" style={{ marginBottom: '1rem' }}>
          <ArrowLeft size={14} /> Back to Tickets
        </button>
        <div style={{ color: '#dc2626' }}>{error || 'Ticket not found'}</div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      
      {/* Top Header Bar */}
      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <button onClick={onBack} className="btn btn-secondary btn-sm" style={{ marginBottom: '0.5rem' }}>
            <ArrowLeft size={14} /> Back to Tickets
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }}>
              {ticket.ticket_number}: {ticket.subject}
            </h1>
            <span className={`badge badge-${ticket.status.toLowerCase()}`}>
              {ticket.status.replace('_', ' ')}
            </span>
            {ticket.priority && (
              <span className={`badge badge-${ticket.priority.toLowerCase()}`}>
                {ticket.priority} Priority
              </span>
            )}
            {ticket.category && (
              <span className="badge badge-category">
                {ticket.category.replace('_', ' ')}
              </span>
            )}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.35rem' }}>
            Created on {new Date(ticket.created_at).toLocaleString()}
          </div>
        </div>

        {ticket.book && (
          <div style={{ background: '#f8fafc', padding: '0.6rem 0.85rem', borderRadius: '6px', border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <BookOpen size={16} color="#2563eb" />
            <div>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#0f172a' }}>{ticket.book.title}</div>
              <div style={{ fontSize: '0.75rem', color: '#64748b' }}>ID: {ticket.book.book_id} | Status: {ticket.book.status}</div>
            </div>
          </div>
        )}
      </div>

      {/* Main Grid: Conversation & Timeline */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.8fr) minmax(280px, 1fr)', gap: '1.25rem' }}>
        
        {/* Left Column: Conversation Thread */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          
          {/* Initial Ticket Description Card */}
          <div className="card" style={{ background: '#f8fafc', borderLeft: '4px solid #0f172a' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.8rem' }}>
              <span style={{ fontWeight: 600, color: '#0f172a' }}>Original Inquiry</span>
              <span style={{ color: '#64748b' }}>{new Date(ticket.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
            <div style={{ fontSize: '0.875rem', color: '#334155' }}>
              <AttachmentViewer content={ticket.description} />
            </div>
          </div>

          {/* Messages Stream */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {(ticket.messages || []).map((msg: any) => {
              const isAdmin = msg.sender_role === 'ADMIN';
              return (
                <div
                  key={msg.id}
                  style={{
                    alignSelf: isAdmin ? 'flex-start' : 'flex-end',
                    maxWidth: '85%',
                    background: isAdmin ? '#ffffff' : '#f1f5f9',
                    border: `1px solid ${isAdmin ? '#cbd5e1' : '#e2e8f0'}`,
                    borderLeft: isAdmin ? '4px solid #0284c7' : undefined,
                    borderRadius: '8px',
                    padding: '0.85rem 1rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', marginBottom: '0.35rem', fontSize: '0.75rem' }}>
                    <span style={{ fontWeight: 700, color: isAdmin ? '#0369a1' : '#0f172a' }}>
                      {isAdmin ? 'BookLeaf Operations Desk' : 'You (Author)'}
                    </span>
                    <span style={{ color: '#64748b' }}>
                      {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.875rem', color: '#1e293b' }}>
                    <AttachmentViewer content={msg.message} />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Reply Composer */}
          {ticket.status !== 'CLOSED' ? (
            <form onSubmit={handleSendReply} className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#334155' }}>
                Add Author Reply
              </label>
              <textarea
                rows={3}
                required
                placeholder="Type your reply to BookLeaf Operations..."
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.875rem', resize: 'vertical' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <label className="btn btn-secondary btn-sm" style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
                    <Paperclip size={13} /> {replyAttachmentName ? 'Change File' : 'Attach File'}
                    <input
                      type="file"
                      style={{ display: 'none' }}
                      accept="image/*,.pdf,.doc,.docx,.txt"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          setReplyAttachmentName(file.name);
                          const reader = new FileReader();
                          reader.onload = (ev) => {
                            setReplyAttachmentData(ev.target?.result as string);
                          };
                          reader.readAsDataURL(file);
                        }
                      }}
                    />
                  </label>
                  {replyAttachmentName && (
                    <span style={{ fontSize: '0.75rem', color: '#0f172a', fontWeight: 500, display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                      {replyAttachmentName}
                      <button
                        type="button"
                        onClick={() => {
                          setReplyAttachmentName('');
                          setReplyAttachmentData('');
                        }}
                        style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', padding: 0 }}
                        title="Remove attachment"
                      >
                        <X size={13} />
                      </button>
                    </span>
                  )}
                </div>
                <button type="submit" className="btn btn-primary btn-sm" disabled={sending}>
                  <Send size={13} /> {sending ? 'Sending...' : 'Send Message'}
                </button>
              </div>
            </form>
          ) : (
            <div className="card" style={{ background: '#f8fafc', textAlign: 'center', color: '#64748b', fontSize: '0.875rem' }}>
              This support request is closed. If you require further assistance, please raise a new support ticket.
            </div>
          )}

        </div>

        {/* Right Column: Author Ticket Timeline */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card">
            <h2 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Clock size={16} /> Ticket Timeline History
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {timeline.length === 0 ? (
                <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                  Operational events are logged automatically as actions take place.
                </div>
              ) : (
                timeline.map((event) => (
                  <div key={event.id} style={{ display: 'flex', gap: '0.6rem', fontSize: '0.8rem' }}>
                    <div style={{ marginTop: '0.2rem', color: '#2563eb' }}>
                      <CheckCircle2 size={14} />
                    </div>
                    <div>
                      <div style={{ fontWeight: 600, color: '#0f172a' }}>
                        {event.event_type.replace(/_/g, ' ')}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                        {new Date(event.created_at).toLocaleString()}
                      </div>
                      {event.metadata && Object.keys(event.metadata).length > 0 && (
                        <div style={{ fontSize: '0.75rem', color: '#475569', marginTop: '0.15rem' }}>
                          {event.metadata.new_status && <span>Status: {event.metadata.new_status}</span>}
                          {event.metadata.category && <span>Category: {event.metadata.category}</span>}
                          {event.metadata.priority && <span>Priority: {event.metadata.priority}</span>}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

      </div>

    </div>
  );
};
