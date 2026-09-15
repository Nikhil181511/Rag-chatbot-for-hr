import React from 'react';
import { Bot, FileText, Sparkles } from 'lucide-react';

interface HeaderProps {
  onOpenDocs: () => void;
  documentCount: number;
}

export const Header: React.FC<HeaderProps> = ({ onOpenDocs, documentCount }) => {
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
      </div>
    </header>
  );
};
