import React from 'react';
import { Bot, FileText, User as UserIcon, LogOut, ShieldAlert, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface HeaderProps {
  onOpenDocs: () => void;
  onOpenAuth: () => void;
  documentCount: number;
}

export const Header: React.FC<HeaderProps> = ({ onOpenDocs, onOpenAuth, documentCount }) => {
  const { user, isAuthenticated, isHR, logout } = useAuth();

  return (
    <header className="app-header">
      <div className="brand">
        <div className="brand-icon">
          <Bot size={22} className="text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="brand-title">HR Knowledge Assistant</span>
            <span className="brand-badge">RAG AI</span>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <button className="btn-secondary" onClick={onOpenDocs}>
          <FileText size={16} />
          <span>Knowledge Base ({documentCount})</span>
        </button>

        {isAuthenticated && user ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '4px 10px',
                borderRadius: '8px',
                background: isHR ? 'rgba(244, 63, 94, 0.12)' : 'rgba(6, 182, 212, 0.12)',
                border: `1px solid ${isHR ? 'rgba(244, 63, 94, 0.3)' : 'rgba(6, 182, 212, 0.3)'}`,
              }}
            >
              {isHR ? (
                <ShieldAlert size={14} style={{ color: '#FDA4AF' }} />
              ) : (
                <ShieldCheck size={14} style={{ color: '#67E8F9' }} />
              )}
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-main)', lineHeight: 1.1 }}>
                  {user.full_name || user.email.split('@')[0]}
                </span>
                <span
                  style={{
                    fontSize: '0.65rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    color: isHR ? '#FDA4AF' : '#67E8F9',
                    letterSpacing: '0.04em',
                  }}
                >
                  {isHR ? 'HR Admin' : 'Employee'}
                </span>
              </div>
            </div>

            <button
              className="btn-secondary"
              title="Sign Out"
              onClick={logout}
              style={{ padding: '6px 10px' }}
            >
              <LogOut size={15} />
            </button>
          </div>
        ) : (
          <button className="btn-primary" onClick={onOpenAuth} style={{ padding: '6px 14px', fontSize: '0.85rem' }}>
            <UserIcon size={15} />
            <span>Sign In</span>
          </button>
        )}
      </div>
    </header>
  );
};
