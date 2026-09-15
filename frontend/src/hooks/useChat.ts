import { useState, useRef, useCallback } from 'react';
import { Message, Citation } from '../types';
import { api } from '../services/api';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const activeRequestIdRef = useRef<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (query: string) => {
    if (!query.trim() || isGenerating) return;

    const userMessageId = `user-${Date.now()}`;
    const assistantMessageId = `assistant-${Date.now()}`;

    const userMsg: Message = {
      id: userMessageId,
      role: 'user',
      content: query,
      createdAt: new Date().toISOString(),
    };

    const assistantMsg: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      isStreaming: true,
      citations: [],
      createdAt: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsGenerating(true);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      await api.streamChat(
        query,
        activeConversationId,
        {
          onToken: (token, reqId) => {
            activeRequestIdRef.current = reqId;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: msg.content + token }
                  : msg
              )
            );
          },
          onCitations: (citations) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, citations }
                  : msg
              )
            );
          },
          onDone: () => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, isStreaming: false }
                  : msg
              )
            );
            setIsGenerating(false);
          },
          onAbstention: (message) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: message, isStreaming: false, isAbstention: true }
                  : msg
              )
            );
            setIsGenerating(false);
          },
          onError: (message) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: message, isStreaming: false, error: message }
                  : msg
              )
            );
            setIsGenerating(false);
          },
        },
        abortController.signal
      );
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? {
                  ...msg,
                  content: 'Unable to connect to the assistant. Please ensure the server is running.',
                  isStreaming: false,
                  error: 'Connection error',
                }
              : msg
          )
        );
      }
      setIsGenerating(false);
    }
  }, [activeConversationId, isGenerating]);

  const stopGeneration = useCallback(async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    if (activeRequestIdRef.current) {
      try {
        await api.cancelStream(activeRequestIdRef.current);
      } catch (e) {
        console.error('Failed to cancel backend stream', e);
      }
    }
    setIsGenerating(false);
    setMessages((prev) =>
      prev.map((msg) => (msg.isStreaming ? { ...msg, isStreaming: false } : msg))
    );
  }, []);

  const loadConversation = useCallback(async (conversationId: string) => {
    try {
      const data = await api.getConversation(conversationId);
      setActiveConversationId(conversationId);
      setMessages(
        data.messages.map((m: any) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          citations: m.citations || [],
          isStreaming: false,
          createdAt: m.created_at,
        }))
      );
    } catch (e) {
      console.error('Failed to load conversation', e);
    }
  }, []);

  const clearChat = useCallback(() => {
    setActiveConversationId(null);
    setMessages([]);
    setSelectedCitation(null);
  }, []);

  return {
    messages,
    isGenerating,
    activeConversationId,
    selectedCitation,
    setSelectedCitation,
    sendMessage,
    stopGeneration,
    loadConversation,
    clearChat,
  };
}
