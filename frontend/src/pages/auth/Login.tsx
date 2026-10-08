import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { BookOpen, Shield, User, ArrowRight } from 'lucide-react';

export const Login: React.FC = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState<string>('priya.sharma@bookleaf.com');
  const [password, setPassword] = useState<string>('Author@BookLeaf2026!');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      await login(email, password);
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = async (quickEmail: string, quickPass: string) => {
    setEmail(quickEmail);
    setPassword(quickPass);
    try {
      setLoading(true);
      setError(null);
      await login(quickEmail, quickPass);
    } catch (err: any) {
      setError(err.message || 'Quick login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1.5rem', background: '#f8fafc' }}>
      <div className="card" style={{ width: '100%', maxWidth: '440px', padding: '2rem' }}>
        
        {/* Brand */}
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <div style={{ display: 'inline-flex', background: '#0f172a', color: '#ffffff', padding: '0.6rem', borderRadius: '8px', marginBottom: '0.75rem' }}>
            <BookOpen size={24} />
          </div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a', letterSpacing: '-0.02em' }}>BookLeaf Publishing</h1>
          <p style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '0.25rem' }}>Author Support & Operations Portal</p>
        </div>

        {error && (
          <div style={{ background: '#fee2e2', color: '#b91c1c', padding: '0.6rem 0.85rem', borderRadius: '6px', fontSize: '0.8rem', marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#334155', marginBottom: '0.3rem' }}>
              Work Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{ width: '100%', padding: '0.55rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.875rem' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#334155', marginBottom: '0.3rem' }}>
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{ width: '100%', padding: '0.55rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.875rem' }}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '0.5rem', padding: '0.65rem' }}
            disabled={loading}
          >
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>

        {/* Quick Demo Logins Section */}
        <div style={{ marginTop: '1.75rem', paddingTop: '1.25rem', borderTop: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', marginBottom: '0.6rem', textAlign: 'center' }}>
            One-Click Demo Credentials
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            
            <button
              type="button"
              onClick={() => handleQuickLogin('admin@bookleaf.com', 'Admin@BookLeaf2026!')}
              className="btn btn-secondary btn-sm"
              style={{ justifyContent: 'space-between', width: '100%', fontSize: '0.75rem' }}
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontWeight: 600 }}>
                <Shield size={13} color="#0284c7" /> Operations Admin Desk
              </span>
              <ArrowRight size={12} />
            </button>

            <button
              type="button"
              onClick={() => handleQuickLogin('priya.sharma@bookleaf.com', 'Author@BookLeaf2026!')}
              className="btn btn-secondary btn-sm"
              style={{ justifyContent: 'space-between', width: '100%', fontSize: '0.75rem' }}
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <User size={13} color="#059669" /> Author Priya Sharma (AUTH001)
              </span>
              <ArrowRight size={12} />
            </button>

            <button
              type="button"
              onClick={() => handleQuickLogin('rohit.verma@bookleaf.com', 'Author@BookLeaf2026!')}
              className="btn btn-secondary btn-sm"
              style={{ justifyContent: 'space-between', width: '100%', fontSize: '0.75rem' }}
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <User size={13} color="#059669" /> Author Rohit Verma (AUTH002)
              </span>
              <ArrowRight size={12} />
            </button>

            <button
              type="button"
              onClick={() => handleQuickLogin('ananya.iyer@bookleaf.com', 'Author@BookLeaf2026!')}
              className="btn btn-secondary btn-sm"
              style={{ justifyContent: 'space-between', width: '100%', fontSize: '0.75rem' }}
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <User size={13} color="#059669" /> Author Ananya Iyer (AUTH003)
              </span>
              <ArrowRight size={12} />
            </button>

          </div>
        </div>

      </div>
    </div>
  );
};
