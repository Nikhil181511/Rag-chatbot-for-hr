import React, { useEffect, useState } from 'react';
import { Plus, MessageSquare, Trash2 } from 'lucide-react';
import { Conversation } from '../types';
import { api } from '../services/api';

interface SidebarProps {
  activeId: string | null;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeId,
  onSelectConversation,
  onNewChat,
}) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);

  const loadList = async () => {
    try {
      const list = await api.getConversations();
      setConversations(list);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadList();
  }, [activeId]);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    try {
      await api.deleteConversation(id);
      if (activeId === id) {
        onNewChat();
      }
      loadList();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <aside className="sidebar">
      <div style={{ padding: '16px', borderBottom: '1px solid var(--border-color)' }}>
        <button
          className="btn-primary"
          style={{ width: '100%', justifyContent: 'center' }}
          onClick={onNewChat}
        >
          <Plus size={18} />
          <span>New Conversation</span>
        </button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '12px 8px' }}>
        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-dim)', padding: '8px 12px', textTransform: 'uppercase' }}>
          Recent Inquiries
        </div>
        {conversations.length === 0 ? (
          <div style={{ padding: '16px 12px', color: 'var(--text-dim)', fontSize: '0.85rem', textAlign: 'center' }}>
            No previous chats
          </div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => onSelectConversation(conv.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 12px',
                borderRadius: '8px',
                cursor: 'pointer',
                marginBottom: '4px',
                background: activeId === conv.id ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                color: activeId === conv.id ? '#818CF8' : 'var(--text-muted)',
                fontSize: '0.88rem',
                transition: 'all 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', overflow: 'hidden' }}>
                <MessageSquare size={16} style={{ flexShrink: 0 }} />
                <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {conv.title || 'Untitled Conversation'}
                </span>
              </div>
              <button
                onClick={(e) => handleDelete(e, conv.id)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-dim)',
                  cursor: 'pointer',
                  padding: '4px',
                }}
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))
        )}
      </div>
    </aside>
  );
};
