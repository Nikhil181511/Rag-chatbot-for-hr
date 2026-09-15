import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, User, Bookmark, AlertCircle, Copy, Check } from 'lucide-react';
import { Message, Citation } from '../types';

interface MessageBubbleProps {
  message: Message;
  onCitationClick: (citation: Citation) => void;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  onCitationClick,
}) => {
  const [copied, setCopied] = React.useState(false);
  const isAssistant = message.role === 'assistant';

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`message-row ${message.role}`}>
      <div className={`message-avatar ${message.role}`}>
        {isAssistant ? <Bot size={20} /> : <User size={20} />}
      </div>

      <div
        className={`message-bubble ${message.role} ${
          message.isAbstention ? 'abstention' : ''
        }`}
      >
        {message.isAbstention && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-amber)', fontSize: '0.8rem', fontWeight: 600, marginBottom: '8px' }}>
            <AlertCircle size={15} />
            <span>Out of Document Scope / Abstention</span>
          </div>
        )}

        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {message.content || (message.isStreaming ? '...' : '')}
        </ReactMarkdown>

        {message.isStreaming && (
          <span
            style={{
              display: 'inline-block',
              width: '6px',
              height: '14px',
              background: '#818CF8',
              marginLeft: '4px',
              verticalAlign: 'middle',
              animation: 'pulse 1s infinite',
            }}
          />
        )}

        {/* Citations List */}
        {message.citations && message.citations.length > 0 && (
          <div className="citations-wrapper">
            <div style={{ width: '100%', fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '2px' }}>
              Verified Policy Sources:
            </div>
            {message.citations.map((citation, idx) => (
              <button
                key={`${citation.chunk_id}-${idx}`}
                className="citation-chip"
                onClick={() => onCitationClick(citation)}
              >
                <Bookmark size={12} />
                <span>
                  {citation.document_name}
                  {citation.page_number ? ` (p.${citation.page_number})` : ''}
                  {citation.section ? ` · ${citation.section}` : ''}
                </span>
              </button>
            ))}
          </div>
        )}

        {isAssistant && !message.isStreaming && message.content && (
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
            <button
              onClick={handleCopy}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-dim)',
                cursor: 'pointer',
                fontSize: '0.75rem',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              {copied ? <Check size={12} color="#10B981" /> : <Copy size={12} />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
