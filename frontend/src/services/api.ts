import { Citation, Conversation, DocumentItem, KnowledgeBaseStats } from '../types';

const API_BASE = '/api/v1';

export interface SSECallbacks {
  onToken: (token: string, requestId: string) => void;
  onCitations: (citations: Citation[], requestId: string) => void;
  onDone: (latencyMs: number, requestId: string) => void;
  onAbstention: (message: string, reason: string, requestId: string) => void;
  onError: (message: string, code: string, requestId: string) => void;
}

export const api = {
  // Chat Streaming
  async streamChat(
    query: string,
    conversationId: string | null,
    callbacks: SSECallbacks,
    abortSignal?: AbortSignal
  ): Promise<void> {
    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        conversation_id: conversationId,
      }),
      signal: abortSignal,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) return;

    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('data: ')) {
          try {
            const data = JSON.parse(trimmed.slice(6));
            if (data.type === 'token') {
              callbacks.onToken(data.content, data.request_id);
            } else if (data.type === 'citations') {
              callbacks.onCitations(data.citations, data.request_id);
            } else if (data.type === 'done') {
              callbacks.onDone(data.total_latency_ms, data.request_id);
            } else if (data.type === 'abstention') {
              callbacks.onAbstention(data.message, data.reason, data.request_id);
            } else if (data.type === 'error') {
              callbacks.onError(data.message, data.code, data.request_id);
            }
          } catch (e) {
            console.error('Failed to parse SSE line', trimmed, e);
          }
        }
      }
    }
  },

  async cancelStream(requestId: string): Promise<void> {
    await fetch(`${API_BASE}/chat/stream/${requestId}`, {
      method: 'DELETE',
    });
  },

  // Conversations
  async getConversations(): Promise<Conversation[]> {
    const res = await fetch(`${API_BASE}/conversations`);
    const data = await res.json();
    return data.conversations || [];
  },

  async getConversation(id: string) {
    const res = await fetch(`${API_BASE}/conversations/${id}`);
    return await res.json();
  },

  async deleteConversation(id: string): Promise<void> {
    await fetch(`${API_BASE}/conversations/${id}`, { method: 'DELETE' });
  },

  // Documents
  async getDocuments(): Promise<DocumentItem[]> {
    const res = await fetch(`${API_BASE}/documents`);
    const data = await res.json();
    return data.documents || [];
  },

  async uploadDocuments(files: FileList | File[]): Promise<any> {
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }
    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || err.error?.message || 'Failed to upload document');
    }
    return await res.json();
  },

  async deleteDocument(id: string): Promise<void> {
    await fetch(`${API_BASE}/documents/${id}`, { method: 'DELETE' });
  },

  async getDocumentStatus(id: string) {
    const res = await fetch(`${API_BASE}/documents/${id}/status`);
    return await res.json();
  },

  // Knowledge Base Stats
  async getKnowledgeBaseStats(): Promise<KnowledgeBaseStats> {
    const res = await fetch(`${API_BASE}/knowledge-base/stats`);
    return await res.json();
  },

  // Suggestions
  async getSuggestions(query?: string): Promise<string[]> {
    const url = query ? `${API_BASE}/suggestions?q=${encodeURIComponent(query)}` : `${API_BASE}/suggestions`;
    const res = await fetch(url);
    const data = await res.json();
    return data.suggestions || [];
  },
};
