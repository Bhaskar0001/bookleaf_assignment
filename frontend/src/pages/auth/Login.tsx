import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { BookOpen } from 'lucide-react';

export const Login: React.FC = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setError('Please enter both your email address and password.');
      return;
    }
    try {
      setLoading(true);
      setError(null);
      await login(email.trim(), password);
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1.5rem', background: '#f8fafc' }}>
      <div className="card" style={{ width: '100%', maxWidth: '420px', padding: '2.25rem' }}>
        
        {/* Brand */}
        <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
          <div style={{ display: 'inline-flex', background: '#0f172a', color: '#ffffff', padding: '0.65rem', borderRadius: '8px', marginBottom: '0.75rem' }}>
            <BookOpen size={24} />
          </div>
          <h1 style={{ fontSize: '1.3rem', fontWeight: 700, color: '#0f172a', letterSpacing: '-0.02em' }}>BookLeaf Publishing</h1>
          <p style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '0.25rem' }}>Author Support & Operations Portal</p>
        </div>

        {error && (
          <div style={{ background: '#fee2e2', color: '#b91c1c', padding: '0.65rem 0.85rem', borderRadius: '6px', fontSize: '0.8rem', marginBottom: '1.25rem' }}>
            {error}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
              Work Email Address
            </label>
            <input
              type="email"
              required
              autoComplete="email"
              placeholder="name@domain.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{ width: '100%', padding: '0.6rem 0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.875rem' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
              Password
            </label>
            <input
              type="password"
              required
              autoComplete="current-password"
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{ width: '100%', padding: '0.6rem 0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.875rem' }}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '0.5rem', padding: '0.7rem' }}
            disabled={loading}
          >
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>

      </div>
    </div>
  );
};
