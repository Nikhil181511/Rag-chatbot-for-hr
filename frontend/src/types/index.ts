export interface Citation {
  document_id: string;
  chunk_id: string;
  document_name: string;
  page_number?: number;
  section?: string;
  sheet_name?: string;
  row_start?: number;
  row_end?: number;
  excerpt: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  citations?: Citation[];
  isStreaming?: boolean;
  isAbstention?: boolean;
  error?: string;
  createdAt: string;
  latencyMs?: number;
  chunksUsed?: number;
}

export interface Conversation {
  id: string;
  title: string;
  message_count: number;
  updated_at: string;
}

export interface DocumentItem {
  id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  status: 'PENDING' | 'UPLOADING' | 'PROCESSING' | 'INDEXING' | 'READY' | 'FAILED' | 'DELETED';
  title?: string;
  document_category?: string;
  chunk_count: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeBaseStats {
  document_count: number;
  ready_count: number;
  failed_count: number;
  total_chunks: number;
  last_indexed_at?: string;
}
