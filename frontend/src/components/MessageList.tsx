import React, { useEffect, useRef } from 'react';
import { Message, Citation } from '../types';
import { MessageBubble } from './MessageBubble';

interface MessageListProps {
  messages: Message[];
  onCitationClick: (citation: Citation) => void;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  onCitationClick,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="messages-container">
      {messages.map((msg) => (
        <MessageBubble
          key={msg.id}
          message={msg}
          onCitationClick={onCitationClick}
        />
      ))}
      <div ref={bottomRef} />
    </div>
  );
};
