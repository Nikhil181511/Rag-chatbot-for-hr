import React from 'react';
import { X, FileText, MapPin, Hash, Sparkles } from 'lucide-react';
import { Citation } from '../types';

interface CitationPanelProps {
  citation: Citation | null;
  onClose: () => void;
}

export const CitationPanel: React.FC<CitationPanelProps> = ({
  citation,
  onClose,
}) => {
  if (!citation) return null;

  return (
    <div className="citation-panel">
      <div className="citation-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles size={18} color="#818CF8" />
          <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>Source Verification</span>
        </div>
        <button
          onClick={onClose}
          style={{ background: 'transparent', border: 'none', color: 'var(--text-dim)', cursor: 'pointer' }}
        >
          <X size={20} />
        </button>
      </div>

      <div className="citation-body">
        <div className="citation-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: '#818CF8' }}>
            <FileText size={16} />
            <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{citation.document_name}</span>
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            {citation.page_number && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(255,255,255,0.05)', padding: '2px 8px', borderRadius: '4px' }}>
                <MapPin size={12} />
                <span>Page {citation.page_number}</span>
              </div>
            )}
            {citation.section && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(255,255,255,0.05)', padding: '2px 8px', borderRadius: '4px' }}>
                <Hash size={12} />
                <span>Section: {citation.section}</span>
              </div>
            )}
            {citation.sheet_name && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(255,255,255,0.05)', padding: '2px 8px', borderRadius: '4px' }}>
                <Hash size={12} />
                <span>Sheet: {citation.sheet_name}</span>
              </div>
            )}
          </div>
        </div>

        <div>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '8px' }}>
            Document Excerpt
          </div>
          <div
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: '12px',
              padding: '14px',
              fontSize: '0.85rem',
              lineHeight: '1.6',
              color: 'var(--text-main)',
              fontFamily: 'var(--font-mono)',
              whiteSpace: 'pre-wrap',
            }}
          >
            {citation.excerpt}
          </div>
        </div>
      </div>
    </div>
  );
};
