import React, { useState, useRef, useEffect } from 'react';
import { Send, Square, Sparkles } from 'lucide-react';
import { api } from '../services/api';

interface ChatInputProps {
  onSendMessage: (query: string) => void;
  onStop: () => void;
  isGenerating: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  onStop,
  isGenerating,
}) => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Debounced auto-complete suggestions
  useEffect(() => {
    if (query.trim().length >= 3) {
      const timer = setTimeout(async () => {
        try {
          const res = await api.getSuggestions(query.trim());
          setSuggestions(res.slice(0, 3));
        } catch (e) {
          // ignore autocomplete errors
        }
      }, 250);
      return () => clearTimeout(timer);
    } else {
      setSuggestions([]);
    }
  }, [query]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    if (!query.trim() || isGenerating) return;
    onSendMessage(query.trim());
    setQuery('');
    setSuggestions([]);
  };

  return (
    <div className="input-area">
      {/* Dynamic Suggestions preview */}
      {suggestions.length > 0 && (
        <div style={{ display: 'flex', gap: '8px', marginBottom: '8px', overflowX: 'auto', paddingBottom: '4px' }}>
          {suggestions.map((s, idx) => (
            <button
              key={idx}
              onClick={() => {
                onSendMessage(s);
                setQuery('');
                setSuggestions([]);
              }}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                background: 'rgba(99, 102, 241, 0.1)',
                border: '1px solid rgba(99, 102, 241, 0.25)',
                borderRadius: '20px',
                fontSize: '0.78rem',
                color: '#C7D2FE',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              <Sparkles size={12} color="#818CF8" />
              <span>{s}</span>
            </button>
          ))}
        </div>
      )}

      <div className="input-box-wrapper">
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          placeholder="Ask any question about leave, benefits, onboarding, remote work..."
          rows={1}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isGenerating}
        />

        <div className="input-actions">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            Press <kbd style={{ background: 'rgba(255,255,255,0.08)', padding: '2px 5px', borderRadius: '4px' }}>Enter</kbd> to ask
          </div>

          <div>
            {isGenerating ? (
              <button className="btn-secondary" onClick={onStop} style={{ color: 'var(--accent-rose)', borderColor: 'rgba(244,63,94,0.3)' }}>
                <Square size={14} fill="currentColor" />
                <span>Stop Generation</span>
              </button>
            ) : (
              <button
                className="btn-primary"
                onClick={handleSubmit}
                disabled={!query.trim()}
              >
                <span>Ask HR</span>
                <Send size={14} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
