import React, { useState } from 'react';
import { ShieldCheck, User as UserIcon, Lock, Mail, AlertCircle, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose }) => {
  const { login, register } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState<'hr' | 'employee'>('employee');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isLogin) {
        await login(email, password);
      } else {
        await register(email, password, fullName, role);
      }
      onClose();
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container" style={{ maxWidth: '440px' }} onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              backgroundColor: 'var(--primary-glow)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--primary)'
            }}>
              <ShieldCheck size={20} />
            </div>
            <div>
              <h2 className="modal-title" style={{ fontSize: '1.15rem' }}>
                {isLogin ? 'Sign In' : 'Create Account'}
              </h2>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                {isLogin ? 'Access HR policies and assistant' : 'Register with your organizational role'}
              </p>
            </div>
          </div>
          <button className="btn-icon" onClick={onClose}>✕</button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} style={{ padding: '20px' }}>
          {error && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 12px',
              borderRadius: '8px',
              background: 'rgba(244, 63, 94, 0.15)',
              border: '1px solid rgba(244, 63, 94, 0.3)',
              color: '#FDA4AF',
              fontSize: '0.85rem',
              marginBottom: '16px'
            }}>
              <AlertCircle size={16} style={{ flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}

          {!isLogin && (
            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                Full Name
              </label>
              <div style={{ position: 'relative' }}>
                <UserIcon size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-dim)' }} />
                <input
                  type="text"
                  required
                  placeholder="e.g. Jane Smith"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 12px 10px 36px',
                    borderRadius: '8px',
                    background: 'var(--bg-input)',
                    border: '1px solid var(--border-color)',
                    color: 'var(--text-main)',
                    fontSize: '0.9rem',
                    outline: 'none',
                  }}
                />
              </div>
            </div>
          )}

          <div style={{ marginBottom: '14px' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
              Corporate Email
            </label>
            <div style={{ position: 'relative' }}>
              <Mail size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-dim)' }} />
              <input
                type="email"
                required
                placeholder="name@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 12px 10px 36px',
                  borderRadius: '8px',
                  background: 'var(--bg-input)',
                  border: '1px solid var(--border-color)',
                  color: 'var(--text-main)',
                  fontSize: '0.9rem',
                  outline: 'none',
                }}
              />
            </div>
          </div>

          <div style={{ marginBottom: '14px' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-dim)' }} />
              <input
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 12px 10px 36px',
                  borderRadius: '8px',
                  background: 'var(--bg-input)',
                  border: '1px solid var(--border-color)',
                  color: 'var(--text-main)',
                  fontSize: '0.9rem',
                  outline: 'none',
                }}
              />
            </div>
          </div>

          {!isLogin && (
            <div style={{ marginBottom: '18px' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                Role in Organization
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                <button
                  type="button"
                  onClick={() => setRole('employee')}
                  style={{
                    padding: '8px',
                    borderRadius: '8px',
                    border: `1px solid ${role === 'employee' ? 'var(--accent-cyan)' : 'var(--border-color)'}`,
                    background: role === 'employee' ? 'rgba(6, 182, 212, 0.15)' : 'var(--bg-input)',
                    color: role === 'employee' ? '#67E8F9' : 'var(--text-muted)',
                    cursor: 'pointer',
                    fontSize: '0.85rem',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  <span style={{ fontWeight: 600 }}>Employee</span>
                  <span style={{ fontSize: '0.7rem', opacity: 0.8 }}>Chat & Queries</span>
                </button>
                <button
                  type="button"
                  onClick={() => setRole('hr')}
                  style={{
                    padding: '8px',
                    borderRadius: '8px',
                    border: `1px solid ${role === 'hr' ? 'var(--accent-rose)' : 'var(--border-color)'}`,
                    background: role === 'hr' ? 'rgba(244, 63, 94, 0.15)' : 'var(--bg-input)',
                    color: role === 'hr' ? '#FDA4AF' : 'var(--text-muted)',
                    cursor: 'pointer',
                    fontSize: '0.85rem',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  <span style={{ fontWeight: 600 }}>HR Admin</span>
                  <span style={{ fontSize: '0.7rem', opacity: 0.8 }}>Docs Upload & Mgmt</span>
                </button>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="btn-primary"
            style={{
              width: '100%',
              padding: '10px',
              fontSize: '0.9rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              marginTop: '8px'
            }}
          >
            <span>{loading ? 'Authenticating...' : isLogin ? 'Sign In' : 'Create Account'}</span>
            <ArrowRight size={16} />
          </button>

          <div style={{ marginTop: '16px', textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {isLogin ? "Don't have an account yet?" : 'Already have an account?'}{' '}
            <button
              type="button"
              onClick={() => {
                setIsLogin(!isLogin);
                setError(null);
              }}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--primary)',
                fontWeight: 600,
                cursor: 'pointer',
                textDecoration: 'underline'
              }}
            >
              {isLogin ? 'Register now' : 'Sign in'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
