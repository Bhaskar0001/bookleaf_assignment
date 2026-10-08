import React, { useEffect, useState } from 'react';
import type { Book } from '../../types';
import { apiRequest } from '../../lib/api';
import { MessageSquarePlus } from 'lucide-react';

interface AuthorBooksProps {
  onSelectBookForTicket?: (bookId: string) => void;
}

export const AuthorBooks: React.FC<AuthorBooksProps> = ({ onSelectBookForTicket }) => {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchBooks() {
      try {
        setLoading(true);
        const res = await apiRequest<{ success: boolean; data: Book[] }>('/author/books');
        setBooks(res.data);
      } catch (err: any) {
        setError(err.message || 'Failed to load books');
      } finally {
        setLoading(false);
      }
    }
    fetchBooks();
  }, []);

  if (loading) {
    return <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>Loading book catalog...</div>;
  }

  if (error) {
    return <div style={{ padding: '2rem', color: '#dc2626' }}>{error}</div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }}>My Publications</h1>
          <p style={{ fontSize: '0.8rem', color: '#64748b' }}>
            Author-isolated catalog of published works and books currently in manufacturing
          </p>
        </div>
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Book Title & ID</th>
              <th>Status</th>
              <th>ISBN</th>
              <th>Genre</th>
              <th>Pub Date</th>
              <th>MRP</th>
              <th>Copies Sold</th>
              <th>Earned / Paid / Pending</th>
              <th>Print Partner</th>
              <th>Available On</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {books.length === 0 ? (
              <tr>
                <td colSpan={11} style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8' }}>
                  No books registered for this account.
                </td>
              </tr>
            ) : (
              books.map((b) => (
                <tr key={b.id}>
                  <td>
                    <div style={{ fontWeight: 600, color: '#0f172a' }}>{b.title}</div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{b.book_id}</div>
                  </td>
                  <td>
                    <span className={`badge ${b.status === 'PUBLISHED' ? 'badge-resolved' : 'badge-in_progress'}`}>
                      {b.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                    {b.isbn || <span style={{ color: '#94a3b8' }}>Pending Proof</span>}
                  </td>
                  <td>{b.genre || '—'}</td>
                  <td>{b.publication_date ? new Date(b.publication_date).toLocaleDateString() : <span style={{ color: '#94a3b8' }}>In Production</span>}</td>
                  <td>{b.mrp ? `₹${Number(b.mrp).toFixed(2)}` : <span style={{ color: '#94a3b8' }}>TBD</span>}</td>
                  <td style={{ fontWeight: 600 }}>{b.copies_sold.toLocaleString()}</td>
                  <td>
                    <div style={{ fontSize: '0.8rem' }}>
                      <div>Earned: <strong>₹{Number(b.royalty_earned).toLocaleString()}</strong></div>
                      <div style={{ color: '#16a34a' }}>Paid: ₹{Number(b.royalty_paid).toLocaleString()}</div>
                      <div style={{ color: Number(b.royalty_pending) > 0 ? '#b45309' : '#64748b', fontWeight: Number(b.royalty_pending) > 0 ? 600 : 400 }}>
                        Pending: ₹{Number(b.royalty_pending).toLocaleString()}
                      </div>
                    </div>
                  </td>
                  <td>{b.print_partner || <span style={{ color: '#94a3b8' }}>Unassigned</span>}</td>
                  <td>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                      {b.available_on && b.available_on.length > 0 ? (
                        b.available_on.map((ch, idx) => (
                          <span key={idx} style={{ background: '#f1f5f9', fontSize: '0.7rem', padding: '0.1rem 0.35rem', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                            {ch}
                          </span>
                        ))
                      ) : (
                        <span style={{ color: '#94a3b8', fontSize: '0.75rem' }}>None</span>
                      )}
                    </div>
                  </td>
                  <td>
                    {onSelectBookForTicket && (
                      <button
                        onClick={() => onSelectBookForTicket(b.book_id)}
                        className="btn btn-secondary btn-sm"
                        title="Raise ticket for this book"
                      >
                        <MessageSquarePlus size={14} /> Support
                      </button>
                    )}
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
