import React from 'react';
import { Bot, HelpCircle, Calendar, Home, Award } from 'lucide-react';

interface EmptyStateProps {
  onSelectPrompt: (prompt: string) => void;
}

const PROMPT_STARTERS = [
  {
    icon: Calendar,
    title: 'Annual & Sick Leave',
    query: 'How many days of paid annual leave do full-time employees get per year?',
  },
  {
    icon: Home,
    title: 'Remote Work Policy',
    query: 'What is the work from home equipment allowance and monthly internet stipend?',
  },
  {
    icon: Award,
    title: 'Health & Medical Benefits',
    query: 'When does health insurance coverage become effective for new hires?',
  },
  {
    icon: HelpCircle,
    title: 'Onboarding Checklist',
    query: 'What documents are required during the first week of onboarding?',
  },
];

export const EmptyState: React.FC<EmptyStateProps> = ({ onSelectPrompt }) => {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">
        <Bot size={32} />
      </div>

      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.02em', marginBottom: '8px' }}>
        How can I assist your HR needs today?
      </h1>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.92rem', lineHeight: '1.5' }}>
        Ask any policy question. Answers are grounded in your company's uploaded documents with source citations.
      </p>

      <div className="suggestions-grid">
        {PROMPT_STARTERS.map((starter, idx) => {
          const Icon = starter.icon;
          return (
            <div
              key={idx}
              className="suggestion-card"
              onClick={() => onSelectPrompt(starter.query)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, color: '#C7D2FE', marginBottom: '4px' }}>
                <Icon size={16} color="#818CF8" />
                <span>{starter.title}</span>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                "{starter.query}"
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
