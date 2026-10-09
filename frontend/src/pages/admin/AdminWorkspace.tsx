import React, { useEffect, useState, useCallback } from 'react';
import { apiRequest } from '../../lib/api';
import { useRealtime } from '../../context/RealtimeContext';
import type { Ticket, DuplicateCandidate, ConfirmedRelationship, TimelineEvent, DraftResponse } from '../../types';
import {
  ArrowLeft,
  Send,
  Link2,
  Unlink,
  CheckCircle2,
  Clock,
  BookOpen,
  User,
  Shield,
  RefreshCw,
  Sparkles,
  Bot,
  AlertTriangle,
} from 'lucide-react';
import { AttachmentViewer } from '../../components/common/AttachmentViewer';

interface AdminWorkspaceProps {
  ticketNumber: string;
  onBackToQueue: () => void;
}

export const AdminWorkspace: React.FC<AdminWorkspaceProps> = ({ ticketNumber, onBackToQueue }) => {
  const { subscribe } = useRealtime();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [candidates, setCandidates] = useState<DuplicateCandidate[]>([]);
  const [confirmedRelationships, setConfirmedRelationships] = useState<ConfirmedRelationship[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionError, setActionError] = useState<string | null>(null);

  // Composer State
  const [activeTab, setActiveTab] = useState<'messages' | 'internal_notes'>('messages');
  const [responseText, setResponseText] = useState<string>('');
  const [internalNoteText, setInternalNoteText] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);

  // AI Assist State
  const [generatingDraft, setGeneratingDraft] = useState<boolean>(false);
  const [aiDraft, setAiDraft] = useState<DraftResponse | null>(null);
  const [reclassifying, setReclassifying] = useState<boolean>(false);

  const fetchWorkspaceData = useCallback(async (isSilent: boolean = false) => {
    if (!ticketNumber) return;
    try {
      if (!isSilent) setLoading(true);
      setActionError(null);

      // Load full ticket bundle, timeline, and duplicate relationships in parallel
      const [ticketRes, timelineRes, relsRes] = await Promise.all([
        apiRequest<{ success: boolean; data: Ticket }>(`/admin/tickets/${ticketNumber}`),
        apiRequest<{ success: boolean; data: TimelineEvent[] }>(`/admin/tickets/${ticketNumber}/timeline`),
        apiRequest<{ success: boolean; data: { candidates: DuplicateCandidate[]; confirmedRelationships: ConfirmedRelationship[] } }>(
          `/admin/tickets/${ticketNumber}/relationships`
        ),
      ]);

      setTicket(ticketRes.data);
      setTimeline(timelineRes.data);
      setCandidates(relsRes.data.candidates);
      setConfirmedRelationships(relsRes.data.confirmedRelationships);
    } catch (err: any) {
      if (!isSilent) setActionError(err.message || 'Failed to load workspace data');
    } finally {
      if (!isSilent) setLoading(false);
    }
  }, [ticketNumber]);

  useEffect(() => {
    fetchWorkspaceData(false);
  }, [ticketNumber, fetchWorkspaceData]);

  // Live WebSocket update subscription
  useEffect(() => {
    const unsubscribe = subscribe((evt) => {
      if (evt.ticket_id === ticketNumber) {
        fetchWorkspaceData(true);
      }
    });
    return unsubscribe;
  }, [ticketNumber, subscribe, fetchWorkspaceData]);

  // Action Handlers
  const handleStatusChange = async (newStatus: string) => {
    try {
      await apiRequest(`/admin/tickets/${ticketNumber}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status: newStatus }),
      });
      await fetchWorkspaceData(true);
    } catch (err: any) {
      setActionError(err.message);
    }
  };

  const handleCategoryOverride = async (newCategory: string) => {
    try {
      await apiRequest(`/admin/tickets/${ticketNumber}/category`, {
        method: 'PATCH',
        body: JSON.stringify({ category: newCategory }),
      });
      await fetchWorkspaceData(true);
    } catch (err: any) {
      setActionError(err.message);
    }
  };

  const handlePriorityOverride = async (newPriority: string) => {
    try {
      await apiRequest(`/admin/tickets/${ticketNumber}/priority`, {
        method: 'PATCH',
        body: JSON.stringify({ priority: newPriority }),
      });
      await fetchWorkspaceData(true);
    } catch (err: any) {
      setActionError(err.message);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!responseText.trim() || submitting) return;

    try {
      setSubmitting(true);
      await apiRequest(`/admin/tickets/${ticketNumber}/messages`, {
        method: 'POST',
        body: JSON.stringify({ message: responseText.trim() }),
      });
      setResponseText('');
      await fetchWorkspaceData();
    } catch (err: any) {
      setActionError(err.message || 'Failed to send response');
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddInternalNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!internalNoteText.trim() || submitting) return;

    try {
      setSubmitting(true);
      await apiRequest(`/admin/tickets/${ticketNumber}/internal-notes`, {
        method: 'POST',
        body: JSON.stringify({ note: internalNoteText.trim() }),
      });
      setInternalNoteText('');
      await fetchWorkspaceData();
    } catch (err: any) {
      setActionError(err.message || 'Failed to save internal note');
    } finally {
      setSubmitting(false);
    }
  };

  const handleLinkDuplicate = async (targetTicketNumber: string) => {
    try {
      await apiRequest(`/admin/tickets/${ticketNumber}/link-duplicate`, {
        method: 'POST',
        body: JSON.stringify({ target_ticket_id: targetTicketNumber }),
      });
      await fetchWorkspaceData();
    } catch (err: any) {
      setActionError(err.message);
    }
  };

  const handleUnlinkDuplicate = async (targetTicketNumber: string) => {
    try {
      await apiRequest(`/admin/tickets/${ticketNumber}/unlink-duplicate`, {
        method: 'POST',
        body: JSON.stringify({ target_ticket_id: targetTicketNumber }),
      });
      await fetchWorkspaceData();
    } catch (err: any) {
      setActionError(err.message);
    }
  };

  const handleConfirmNotDuplicate = async (targetTicketNumber: string) => {
    try {
      await apiRequest(`/admin/tickets/${ticketNumber}/confirm-not-duplicate`, {
        method: 'POST',
        body: JSON.stringify({ target_ticket_id: targetTicketNumber }),
      });
      await fetchWorkspaceData();
    } catch (err: any) {
      setActionError(err.message);
    }
  };

  const handleGenerateDraft = async () => {
    try {
      setGeneratingDraft(true);
      setActionError(null);
      const res = await apiRequest<{ success: boolean; data: DraftResponse }>(
        `/admin/tickets/${ticketNumber}/draft-response`,
        { method: 'POST' }
      );
      setAiDraft(res.data);
    } catch (err: any) {
      setActionError(err.message || 'Failed to generate AI draft response');
    } finally {
      setGeneratingDraft(false);
    }
  };

  const handleApplyDraft = () => {
    if (aiDraft?.draft_response) {
      setResponseText(aiDraft.draft_response);
    }
  };

  const handleReclassify = async () => {
    try {
      setReclassifying(true);
      setActionError(null);
      await apiRequest(`/admin/tickets/${ticketNumber}/reclassify`, { method: 'POST' });
      await fetchWorkspaceData(true);
    } catch (err: any) {
      setActionError(err.message || 'Failed to reclassify ticket');
    } finally {
      setReclassifying(false);
    }
  };

  if (!ticketNumber) {
    return (
      <div className="card" style={{ padding: '2.5rem', textAlign: 'center' }}>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#0f172a', marginBottom: '0.5rem' }}>No Ticket Selected</h2>
        <p style={{ color: '#64748b', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
          Please select a ticket from the Operational Support Queue to view and manage it.
        </p>
        <button onClick={onBackToQueue} className="btn btn-primary btn-sm">
          <ArrowLeft size={13} /> Return to Queue
        </button>
      </div>
    );
  }

  if (loading) {
    return <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>Loading operational workspace...</div>;
  }

  if (!ticket) {
    return (
      <div style={{ padding: '2rem' }}>
        <button onClick={onBackToQueue} className="btn btn-secondary btn-sm" style={{ marginBottom: '1rem' }}>
          <ArrowLeft size={14} /> Back to Queue
        </button>
        <div style={{ color: '#dc2626' }}>Ticket {ticketNumber} not found.</div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      
      {/* Top Bar */}
      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <button onClick={onBackToQueue} className="btn btn-secondary btn-sm" style={{ marginBottom: '0.5rem' }}>
            <ArrowLeft size={14} /> Back to Queue
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
                {ticket.priority} ({ticket.priority_source || 'SYSTEM'})
              </span>
            )}
            {ticket.category && (
              <span className="badge badge-category">
                {ticket.category.replace('_', ' ')} ({ticket.category_source || 'SYSTEM'})
              </span>
            )}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>
            Opened on {new Date(ticket.created_at).toLocaleString()} | Assignee: {ticket.assigned_admin_name || 'Unassigned'}
          </div>
        </div>

        {/* Operational State Controls */}
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
          
          {/* Status select with state-machine validation */}
          <select
            value={ticket.status}
            onChange={(e) => handleStatusChange(e.target.value)}
            style={{ padding: '0.4rem 0.6rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.8rem', fontWeight: 600 }}
          >
            <option value={ticket.status} disabled>Current: {ticket.status.replace('_', ' ')}</option>
            {ticket.status === 'OPEN' && (
              <>
                <option value="IN_PROGRESS">Set IN PROGRESS</option>
                <option value="RESOLVED">Set RESOLVED</option>
                <option value="CLOSED">Set CLOSED</option>
              </>
            )}
            {ticket.status === 'IN_PROGRESS' && (
              <>
                <option value="RESOLVED">Set RESOLVED</option>
                <option value="CLOSED">Set CLOSED</option>
              </>
            )}
            {ticket.status === 'RESOLVED' && (
              <>
                <option value="IN_PROGRESS">Reopen to IN PROGRESS</option>
                <option value="CLOSED">Set CLOSED</option>
              </>
            )}
            {ticket.status === 'CLOSED' && (
              <option value="IN_PROGRESS">Reopen to IN PROGRESS</option>
            )}
          </select>

          {/* Priority override */}
          <select
            value={ticket.priority || ''}
            onChange={(e) => handlePriorityOverride(e.target.value)}
            style={{ padding: '0.4rem 0.6rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.8rem' }}
          >
            <option value="">Priority...</option>
            <option value="CRITICAL">Override CRITICAL</option>
            <option value="HIGH">Override HIGH</option>
            <option value="MEDIUM">Override MEDIUM</option>
            <option value="LOW">Override LOW</option>
          </select>

          {/* Category override */}
          <select
            value={ticket.category || ''}
            onChange={(e) => handleCategoryOverride(e.target.value)}
            style={{ padding: '0.4rem 0.6rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.8rem' }}
          >
            <option value="">Category...</option>
            <option value="ROYALTY_PAYMENT">ROYALTY PAYMENT</option>
            <option value="ISBN_METADATA">ISBN METADATA</option>
            <option value="PRINTING_QUALITY">PRINTING QUALITY</option>
            <option value="DISTRIBUTION_AVAILABILITY">DISTRIBUTION AVAILABILITY</option>
            <option value="BOOK_STATUS">BOOK STATUS</option>
            <option value="GENERAL">GENERAL</option>
          </select>

          <button onClick={() => fetchWorkspaceData(false)} className="btn btn-secondary btn-sm" title="Refresh">
            <RefreshCw size={13} />
          </button>
        </div>
      </div>

      {actionError && (
        <div style={{ background: '#fee2e2', color: '#b91c1c', padding: '0.75rem 1rem', borderRadius: '6px', fontSize: '0.85rem' }}>
          {actionError}
        </div>
      )}

      {/* 3-Column / Main Layout Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(300px, 1fr) minmax(0, 1.8fr) minmax(320px, 1.2fr)', gap: '1rem' }}>
        
        {/* Column 1: Context & Relationships */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          
          {/* Author Card */}
          <div className="card">
            <h2 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: '0.6rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <User size={15} /> Author Profile
            </h2>
            <div style={{ fontSize: '0.85rem', color: '#0f172a' }}>
              <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>{ticket.author?.pen_name}</div>
              <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Author ID: {ticket.author?.author_id}</div>
              <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Email: {ticket.author?.email || 'Registered'}</div>
            </div>
          </div>

          {/* AI Support Assist Card */}
          <div className="card" style={{ borderLeft: '4px solid #6366f1' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
              <h2 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#4338ca', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '0.4rem', margin: 0 }}>
                <Sparkles size={15} /> AI Support Assist
              </h2>
              <button
                type="button"
                onClick={handleReclassify}
                disabled={reclassifying}
                className="btn btn-secondary btn-sm"
                style={{ padding: '0.2rem 0.45rem', fontSize: '0.7rem' }}
                title="Re-run AI Classification and Prioritization"
              >
                <RefreshCw size={11} className={reclassifying ? 'spin' : ''} /> {reclassifying ? 'Analyzing...' : 'Re-analyze'}
              </button>
            </div>
            <div style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
              <div>
                <span style={{ color: '#64748b', fontSize: '0.75rem' }}>System Category: </span>
                <span style={{ fontWeight: 600, color: '#0f172a' }}>
                  {ticket.system_category ? ticket.system_category.replace(/_/g, ' ') : (ticket.category || 'Pending')}
                </span>
                {ticket.system_category_confidence != null && (
                  <span style={{ marginLeft: '0.35rem', fontSize: '0.7rem', color: '#6366f1', background: '#eef2ff', padding: '0.1rem 0.35rem', borderRadius: '4px', fontWeight: 600 }}>
                    {Math.round(ticket.system_category_confidence * 100)}% conf
                  </span>
                )}
              </div>
              <div>
                <span style={{ color: '#64748b', fontSize: '0.75rem' }}>System Priority: </span>
                <span style={{ fontWeight: 600, color: '#0f172a' }}>
                  {ticket.system_priority || ticket.priority || 'Pending'}
                </span>
                {ticket.system_priority_confidence != null && (
                  <span style={{ marginLeft: '0.35rem', fontSize: '0.7rem', color: '#6366f1', background: '#eef2ff', padding: '0.1rem 0.35rem', borderRadius: '4px', fontWeight: 600 }}>
                    {Math.round(ticket.system_priority_confidence * 100)}% conf
                  </span>
                )}
              </div>
              <div style={{ fontSize: '0.7rem', color: '#94a3b8', borderTop: '1px solid #f1f5f9', paddingTop: '0.35rem' }}>
                Classification source: <strong>{ticket.category_source || 'SYSTEM'}</strong>
              </div>
            </div>
          </div>

          {/* Book Details */}
          <div className="card">
            <h2 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: '0.6rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <BookOpen size={15} /> Book Context
            </h2>
            {ticket.book ? (
              <div style={{ fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                <div style={{ fontWeight: 700, color: '#0f172a' }}>{ticket.book.title}</div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>ID: {ticket.book.book_id}</div>
                <div style={{ fontSize: '0.75rem' }}>Status: <span className="badge badge-resolved" style={{ fontSize: '0.7rem' }}>{ticket.book.status}</span></div>
                <div style={{ fontSize: '0.75rem', color: '#475569' }}>ISBN: {ticket.book.isbn || 'Pending registration'}</div>
              </div>
            ) : (
              <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>General / Account level inquiry (No book attached).</div>
            )}
          </div>

          {/* Duplicate Candidates Panel (Deterministic - No LLM) */}
          <div className="card">
            <h2 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: '0.6rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Link2 size={15} /> Duplicate Candidates
            </h2>
            
            {/* Confirmed links */}
            {confirmedRelationships.length > 0 && (
              <div style={{ marginBottom: '0.75rem', paddingBottom: '0.75rem', borderBottom: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#16a34a', marginBottom: '0.35rem' }}>
                  Confirmed Linked Tickets:
                </div>
                {confirmedRelationships.map((cr) => {
                  const otherTicketNumber = cr.source_ticket_number === ticketNumber ? cr.target_ticket_number : cr.source_ticket_number;
                  return (
                    <div key={cr.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#f0fdf4', padding: '0.4rem 0.6rem', borderRadius: '4px', border: '1px solid #bbf7d0', fontSize: '0.75rem', marginBottom: '0.25rem' }}>
                      <span>
                        {otherTicketNumber} (DUPLICATE)
                      </span>
                      <button
                        onClick={() => handleUnlinkDuplicate(otherTicketNumber || '')}
                        className="btn btn-secondary btn-sm"
                        style={{ padding: '0.15rem 0.35rem', fontSize: '0.7rem' }}
                        title="Unlink"
                      >
                        <Unlink size={12} />
                      </button>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Candidate list */}
            {candidates.length === 0 ? (
              <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                No candidate duplicates detected for this ticket scope.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {candidates.map((cand, idx) => {
                  const candNum = cand.ticket_number || cand.ticketNumber || '';
                  const candId = cand.ticket_id || cand.ticketId || candNum || `cand-${idx}`;
                  return (
                    <div
                      key={candId}
                      style={{
                        background: '#f8fafc',
                        padding: '0.6rem',
                        borderRadius: '6px',
                        border: '1px solid #e2e8f0',
                        fontSize: '0.75rem',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.2rem' }}>
                        <span style={{ fontWeight: 700, color: '#0f172a' }}>{candNum}</span>
                        <span style={{ background: '#e0f2fe', color: '#0369a1', padding: '0.1rem 0.35rem', borderRadius: '4px', fontWeight: 600 }}>
                          {Math.round(cand.similarity * 100)}% match
                        </span>
                      </div>
                      <div style={{ color: '#334155', fontWeight: 500, marginBottom: '0.25rem' }}>
                        {cand.subject}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: '#64748b', marginBottom: '0.4rem' }}>
                        Signals: {cand.reason}
                      </div>
                      <div style={{ display: 'flex', gap: '0.35rem' }}>
                        <button
                          onClick={() => handleLinkDuplicate(candNum)}
                          className="btn btn-primary btn-sm"
                          style={{ fontSize: '0.7rem', padding: '0.2rem 0.4rem' }}
                        >
                          <Link2 size={11} /> Link Duplicate
                        </button>
                        <button
                          onClick={() => handleConfirmNotDuplicate(candNum)}
                          className="btn btn-secondary btn-sm"
                          style={{ fontSize: '0.7rem', padding: '0.2rem 0.4rem' }}
                        >
                          Not Duplicate
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

        </div>

        {/* Column 2: Center Conversation & Response Composer */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          
          {/* Tab Selector: Messages vs Internal Notes */}
          <div style={{ display: 'flex', borderBottom: '1px solid #e2e8f0', gap: '1rem' }}>
            <button
              onClick={() => setActiveTab('messages')}
              style={{
                padding: '0.5rem 0.25rem',
                border: 'none',
                background: 'transparent',
                fontWeight: 600,
                fontSize: '0.85rem',
                color: activeTab === 'messages' ? '#0f172a' : '#64748b',
                borderBottom: activeTab === 'messages' ? '2px solid #0f172a' : 'none',
                cursor: 'pointer',
              }}
            >
              Author Conversation ({ticket.messages ? ticket.messages.length : 0})
            </button>
            <button
              onClick={() => setActiveTab('internal_notes')}
              style={{
                padding: '0.5rem 0.25rem',
                border: 'none',
                background: 'transparent',
                fontWeight: 600,
                fontSize: '0.85rem',
                color: activeTab === 'internal_notes' ? '#0f172a' : '#64748b',
                borderBottom: activeTab === 'internal_notes' ? '2px solid #0f172a' : 'none',
                cursor: 'pointer',
              }}
            >
              Privileged Internal Notes ({ticket.internalNotes ? ticket.internalNotes.length : 0})
            </button>
          </div>

          {activeTab === 'messages' ? (
            <>
              {/* Original Author Request */}
              <div className="card" style={{ background: '#f8fafc', borderLeft: '4px solid #0f172a' }}>
                <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '0.35rem', display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontWeight: 600, color: '#0f172a' }}>Initial Inquiry by Author</span>
                  <span>{new Date(ticket.created_at).toLocaleString()}</span>
                </div>
                <div style={{ fontSize: '0.875rem', color: '#1e293b' }}>
                  <AttachmentViewer content={ticket.description} />
                </div>
              </div>

              {/* Message History */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '380px', overflowY: 'auto' }}>
                {(ticket.messages || []).map((m) => {
                  const isAdmin = m.sender_role === 'ADMIN';
                  return (
                    <div
                      key={m.id}
                      style={{
                        alignSelf: isAdmin ? 'flex-end' : 'flex-start',
                        maxWidth: '85%',
                        background: isAdmin ? '#f0f9ff' : '#ffffff',
                        border: `1px solid ${isAdmin ? '#bae6fd' : '#e2e8f0'}`,
                        borderRadius: '6px',
                        padding: '0.75rem',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', fontSize: '0.75rem', marginBottom: '0.25rem' }}>
                        <span style={{ fontWeight: 700, color: isAdmin ? '#0369a1' : '#0f172a' }}>
                          {isAdmin ? `${m.sender_name || 'Admin'} (Operations)` : `${m.sender_name || 'Author'}`}
                        </span>
                        <span style={{ color: '#64748b' }}>
                          {new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.85rem', color: '#0f172a' }}>
                        <AttachmentViewer content={m.message} />
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Response Composer */}
              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.65rem' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#334155' }}>
                    Author Response Composer
                  </span>
                  <button
                    type="button"
                    onClick={handleGenerateDraft}
                    disabled={generatingDraft}
                    className="btn btn-secondary btn-sm"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.35rem',
                      background: '#f5f3ff',
                      color: '#6d28d9',
                      border: '1px solid #ddd6fe',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                    }}
                  >
                    <Sparkles size={13} className={generatingDraft ? 'spin' : ''} />
                    {generatingDraft ? 'Generating Gemini Draft...' : '✨ Generate AI Draft Response'}
                  </button>
                </div>

                {/* AI Draft Display Card */}
                {aiDraft && (
                  <div
                    style={{
                      background: '#f8fafc',
                      border: '1px solid #c7d2fe',
                      borderRadius: '8px',
                      padding: '0.85rem',
                      marginBottom: '0.85rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.5rem',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 700, fontSize: '0.8rem', color: '#4338ca' }}>
                        <Bot size={15} />
                        Gemini Assistive Draft
                      </div>
                      <div style={{ display: 'flex', gap: '0.35rem' }}>
                        <button
                          type="button"
                          onClick={handleApplyDraft}
                          className="btn btn-primary btn-sm"
                          style={{ fontSize: '0.72rem', padding: '0.2rem 0.5rem' }}
                        >
                          Insert into Composer
                        </button>
                        <button
                          type="button"
                          onClick={() => setAiDraft(null)}
                          className="btn btn-secondary btn-sm"
                          style={{ fontSize: '0.72rem', padding: '0.2rem 0.4rem' }}
                        >
                          Dismiss
                        </button>
                      </div>
                    </div>

                    {aiDraft.suggested_action && (
                      <div style={{ fontSize: '0.75rem', color: '#0369a1', background: '#e0f2fe', padding: '0.3rem 0.5rem', borderRadius: '4px' }}>
                        <strong>Suggested Action:</strong> {aiDraft.suggested_action}
                      </div>
                    )}

                    {aiDraft.requires_manual_verification && (
                      <div style={{ fontSize: '0.75rem', color: '#b45309', background: '#fef3c7', padding: '0.3rem 0.5rem', borderRadius: '4px', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                        <AlertTriangle size={13} />
                        <span><strong>Manual Verification Required:</strong> {aiDraft.verification_notes || 'Verify details before sending to author.'}</span>
                      </div>
                    )}

                    <div
                      style={{
                        background: '#ffffff',
                        border: '1px solid #e2e8f0',
                        borderRadius: '6px',
                        padding: '0.6rem 0.75rem',
                        fontSize: '0.8rem',
                        color: '#334155',
                        whiteSpace: 'pre-wrap',
                        lineHeight: 1.45,
                        maxHeight: '160px',
                        overflowY: 'auto',
                      }}
                    >
                      {aiDraft.draft_response}
                    </div>
                  </div>
                )}

                <form onSubmit={handleSendMessage} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <textarea
                    rows={4}
                    required
                    placeholder="Compose message to author..."
                    value={responseText}
                    onChange={(e) => setResponseText(e.target.value)}
                    style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem', resize: 'vertical' }}
                  />
                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                    <button type="submit" className="btn btn-primary btn-sm" disabled={submitting}>
                      <Send size={13} /> {submitting ? 'Sending...' : 'Send Response'}
                    </button>
                  </div>
                </form>
              </div>
            </>
          ) : (
            /* Privileged Internal Notes Tab */
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ background: '#fef2f2', border: '1px solid #fecaca', padding: '0.6rem 0.85rem', borderRadius: '6px', fontSize: '0.75rem', color: '#991b1b', display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                <Shield size={14} />
                <span>Privileged Operations Notes: These notes are strictly isolated and never visible to the author.</span>
              </div>

              {/* Existing Notes */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {(ticket.internalNotes || []).map((n) => (
                  <div key={n.id} style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '0.75rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#64748b', marginBottom: '0.25rem' }}>
                      <span style={{ fontWeight: 600, color: '#0f172a' }}>{n.admin_name || 'Admin'}</span>
                      <span>{new Date(n.created_at).toLocaleString()}</span>
                    </div>
                    <p style={{ fontSize: '0.85rem', color: '#334155', whiteSpace: 'pre-wrap' }}>
                      {n.note}
                    </p>
                  </div>
                ))}
              </div>

              {/* Add Note Form */}
              <form onSubmit={handleAddInternalNote} className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#334155' }}>
                  Add Confidential Operational Note
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder="Record internal escalation, print partner call details, or ledger verification..."
                  value={internalNoteText}
                  onChange={(e) => setInternalNoteText(e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem', resize: 'vertical' }}
                />
                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <button type="submit" className="btn btn-secondary btn-sm" disabled={submitting}>
                    Save Internal Note
                  </button>
                </div>
              </form>
            </div>
          )}

        </div>

        {/* Column 3: Full Operational History / Timeline */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card">
            <h2 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Clock size={15} /> Complete Operational Timeline
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', maxHeight: '600px', overflowY: 'auto' }}>
              {timeline.map((evt) => (
                <div key={evt.id} style={{ display: 'flex', gap: '0.5rem', fontSize: '0.75rem' }}>
                  <div style={{ marginTop: '0.2rem', color: '#0284c7' }}>
                    <CheckCircle2 size={13} />
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, color: '#0f172a' }}>
                      {evt.event_type.replace(/_/g, ' ')}
                    </div>
                    <div style={{ color: '#64748b' }}>
                      {new Date(evt.created_at).toLocaleString()}
                      {evt.actor_name && <span> by <strong>{evt.actor_name}</strong></span>}
                    </div>
                    {evt.metadata && Object.keys(evt.metadata).length > 0 && (
                      <div style={{ color: '#475569', marginTop: '0.2rem', background: '#f8fafc', padding: '0.25rem 0.45rem', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                        {evt.metadata.new_status && <div>Status: {evt.metadata.old_status} → {evt.metadata.new_status}</div>}
                        {evt.metadata.category && <div>Category: {evt.metadata.category}</div>}
                        {evt.metadata.priority && <div>Priority: {evt.metadata.priority}</div>}
                        {evt.metadata.target_ticket_number && <div>Linked to: {evt.metadata.target_ticket_number}</div>}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>

    </div>
  );
};
