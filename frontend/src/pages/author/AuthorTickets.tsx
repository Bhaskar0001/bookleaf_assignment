import React, { useEffect, useState, useCallback } from 'react';
import type { Ticket, Book } from '../../types';
import { apiRequest } from '../../lib/api';
import { useRealtime } from '../../context/RealtimeContext';
import { PlusCircle, Paperclip, MessageSquare, ArrowRight, X } from 'lucide-react';

interface AuthorTicketsProps {
  onOpenTicket: (ticketNumber: string) => void;
  preselectedBookId?: string | null;
  onClearPreselectedBook?: () => void;
}

export const AuthorTickets: React.FC<AuthorTicketsProps> = ({
  onOpenTicket,
  preselectedBookId,
  onClearPreselectedBook,
}) => {
  const { subscribe } = useRealtime();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState<boolean>(!!preselectedBookId);
  const [subject, setSubject] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [selectedBookId, setSelectedBookId] = useState<string>(preselectedBookId || '');
  const [category, setCategory] = useState<string>('GENERAL');
  const [attachmentName, setAttachmentName] = useState<string>('');
  const [attachmentData, setAttachmentData] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  const fetchData = useCallback(async (isSilent: boolean = false) => {
    try {
      if (!isSilent) setLoading(true);
      const [ticketsRes, booksRes] = await Promise.all([
        apiRequest<{ success: boolean; data: Ticket[] }>('/author/tickets'),
        apiRequest<{ success: boolean; data: Book[] }>('/author/books'),
      ]);
      setTickets(ticketsRes.data);
      setBooks(booksRes.data);
    } catch (err: any) {
      if (!isSilent) setError(err.message || 'Failed to load tickets');
    } finally {
      if (!isSilent) setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData(false);
  }, [fetchData]);

  useEffect(() => {
    if (preselectedBookId) {
      setSelectedBookId(preselectedBookId);
      setIsModalOpen(true);
    }
  }, [preselectedBookId]);

  // Live WebSocket subscription
  useEffect(() => {
    const unsubscribe = subscribe(() => {
      fetchData(true);
    });
    return unsubscribe;
  }, [subscribe, fetchData]);

  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subject.trim() || !description.trim()) {
      setFormError('Please enter both subject and description.');
      return;
    }

    try {
      setSubmitting(true);
      setFormError(null);
      let fullDescription = description.trim();
      if (attachmentName && attachmentData) {
        fullDescription += `\n\n[Attachment: ${attachmentName}](${attachmentData})`;
      } else if (attachmentName) {
        fullDescription += `\n\n[Attachment: ${attachmentName}]`;
      }

      const payload: any = {
        subject: subject.trim(),
        description: fullDescription,
      };
      if (category && category !== 'AUTO') {
        payload.category = category;
      }
      if (selectedBookId) {
        payload.bookId = selectedBookId;
      }

      const res = await apiRequest<{ success: boolean; data: any }>('/author/tickets', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      // Reset form
      setSubject('');
      setDescription('');
      setSelectedBookId('');
      setCategory('');
      setAttachmentName('');
      setAttachmentData('');
      setIsModalOpen(false);
      if (onClearPreselectedBook) onClearPreselectedBook();

      // Refresh list
      await fetchData();

      // Automatically open the created ticket
      if (res.data && res.data.ticketNumber) {
        onOpenTicket(res.data.ticketNumber);
      }
    } catch (err: any) {
      setFormError(err.message || 'Failed to create ticket');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>Loading tickets...</div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }}>Support Requests</h1>
          <p style={{ fontSize: '0.8rem', color: '#64748b' }}>
            Track and communicate directly with BookLeaf Operations on active or resolved queries
          </p>
        </div>
        <button onClick={() => setIsModalOpen(true)} className="btn btn-primary btn-sm">
          <PlusCircle size={15} /> Raise Support Ticket
        </button>
      </div>

      {error && <div style={{ color: '#dc2626', fontSize: '0.875rem' }}>{error}</div>}

      {/* Ticket List Table */}
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Ticket #</th>
              <th>Subject</th>
              <th>Referenced Book</th>
              <th>Status</th>
              <th>Priority</th>
              <th>Category</th>
              <th>Created Date</th>
              <th>Messages</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {tickets.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: '2.5rem', color: '#94a3b8' }}>
                  No support requests raised yet. Click "Raise Support Ticket" to get help.
                </td>
              </tr>
            ) : (
              tickets.map((t) => (
                <tr key={t.id} style={{ cursor: 'pointer' }} onClick={() => onOpenTicket(t.ticket_number)}>
                  <td style={{ fontWeight: 700, color: '#0f172a', fontFamily: 'monospace' }}>
                    {t.ticket_number}
                  </td>
                  <td style={{ fontWeight: 600 }}>
                    {t.subject}
                  </td>
                  <td>
                    {t.book ? (
                      <span style={{ fontSize: '0.8rem', color: '#334155' }}>{t.book.title}</span>
                    ) : (
                      <span style={{ color: '#94a3b8', fontSize: '0.8rem' }}>General Account</span>
                    )}
                  </td>
                  <td>
                    <span className={`badge badge-${t.status.toLowerCase()}`}>
                      {t.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td>
                    {t.priority ? (
                      <span className={`badge badge-${t.priority.toLowerCase()}`}>
                        {t.priority}
                      </span>
                    ) : (
                      <span style={{ color: '#94a3b8', fontSize: '0.75rem' }}>Assessing</span>
                    )}
                  </td>
                  <td>
                    {t.category ? (
                      <span className="badge badge-category">
                        {t.category.replace('_', ' ')}
                      </span>
                    ) : (
                      <span style={{ color: '#94a3b8', fontSize: '0.75rem' }}>Classifying</span>
                    )}
                  </td>
                  <td style={{ fontSize: '0.8rem', color: '#64748b' }}>
                    {new Date(t.created_at).toLocaleDateString()}
                  </td>
                  <td>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.8rem', color: '#64748b' }}>
                      <MessageSquare size={13} /> {t.messages ? t.messages.length : 0}
                    </span>
                  </td>
                  <td>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onOpenTicket(t.ticket_number);
                      }}
                      className="btn btn-secondary btn-sm"
                    >
                      View <ArrowRight size={13} />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Create Ticket Modal */}
      {isModalOpen && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 50,
          padding: '1rem',
        }}>
          <div className="card" style={{ width: '100%', maxWidth: '580px', position: 'relative' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0f172a' }}>Raise New Support Request</h2>
              <button
                onClick={() => {
                  setIsModalOpen(false);
                  if (onClearPreselectedBook) onClearPreselectedBook();
                }}
                style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#64748b' }}
              >
                <X size={18} />
              </button>
            </div>

            {formError && (
              <div style={{ background: '#fee2e2', color: '#b91c1c', padding: '0.5rem 0.75rem', borderRadius: '6px', fontSize: '0.8rem', marginBottom: '1rem' }}>
                {formError}
              </div>
            )}

            <form onSubmit={handleCreateTicket} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              
              {/* Scope / Book */}
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                  Related Book (or General Inquiry)
                </label>
                <select
                  value={selectedBookId}
                  onChange={(e) => setSelectedBookId(e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.875rem' }}
                >
                  <option value="">General Account / Non-Book Inquiry</option>
                  {books.map((b) => (
                    <option key={b.book_id} value={b.book_id}>
                      {b.title} ({b.book_id} - {b.status})
                    </option>
                  ))}
                </select>
              </div>

              {/* Inquiry Category */}
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                  Inquiry Category *
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.875rem' }}
                >
                  <option value="GENERAL">General Inquiry / Platform Assistance</option>
                  <option value="ROYALTY_PAYMENT">Royalty & Payment Calculation</option>
                  <option value="ISBN_METADATA">ISBN, Title & Metadata</option>
                  <option value="PRINTING_QUALITY">Printing Quality & Manufacturing</option>
                  <option value="DISTRIBUTION_AVAILABILITY">Distribution & Retail Availability</option>
                  <option value="BOOK_STATUS">Production Stage & Book Status</option>
                </select>
              </div>

              {/* Subject */}
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                  Subject *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Royalty for Code & Karma has not been received"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.875rem' }}
                />
              </div>

              {/* Description */}
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                  Detailed Description *
                </label>
                <textarea
                  required
                  rows={4}
                  placeholder="Provide complete details so operations can address your request without delay..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.875rem', resize: 'vertical' }}
                />
              </div>

              {/* Attachment Picker */}
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                  Attachment (Optional)
                </label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <label
                    className="btn btn-secondary btn-sm"
                    style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
                  >
                    <Paperclip size={13} /> {attachmentName ? 'Change File' : 'Choose File'}
                    <input
                      type="file"
                      style={{ display: 'none' }}
                      accept="image/*,.pdf,.doc,.docx,.txt"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          if (file.size > 8 * 1024 * 1024) {
                            setFormError('Attachment exceeds 8MB limit.');
                            return;
                          }
                          setAttachmentName(file.name);
                          const reader = new FileReader();
                          reader.onload = (ev) => {
                            setAttachmentData(ev.target?.result as string);
                          };
                          reader.readAsDataURL(file);
                        }
                      }}
                    />
                  </label>
                  {attachmentName ? (
                    <span style={{ fontSize: '0.8rem', color: '#0f172a', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                      {attachmentName}
                      <button
                        type="button"
                        onClick={() => {
                          setAttachmentName('');
                          setAttachmentData('');
                        }}
                        style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', padding: 0 }}
                        title="Remove attachment"
                      >
                        <X size={13} />
                      </button>
                    </span>
                  ) : (
                    <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>No file selected</span>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '0.5rem' }}>
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="btn btn-secondary btn-sm"
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary btn-sm"
                  disabled={submitting}
                >
                  {submitting ? 'Submitting...' : 'Submit Request'}
                </button>
              </div>

            </form>
          </div>
        </div>
      )}

    </div>
  );
};
