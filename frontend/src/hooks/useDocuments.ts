import { useState, useEffect, useCallback } from 'react';
import { DocumentItem, KnowledgeBaseStats } from '../types';
import { api } from '../services/api';

export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [stats, setStats] = useState<KnowledgeBaseStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = useCallback(async () => {
    try {
      setIsLoading(true);
      const [docs, kbStats] = await Promise.all([
        api.getDocuments(),
        api.getKnowledgeBaseStats(),
      ]);
      setDocuments(docs);
      setStats(kbStats);
      setError(null);
    } catch (e: any) {
      setError(e.message || 'Failed to load documents');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const uploadFiles = useCallback(async (files: FileList | File[]) => {
    try {
      setIsUploading(true);
      setError(null);
      await api.uploadDocuments(files);
      await fetchDocuments();
    } catch (e: any) {
      setError(e.message || 'Failed to upload files');
      throw e;
    } finally {
      setIsUploading(false);
    }
  }, [fetchDocuments]);

  const deleteDoc = useCallback(async (id: string) => {
    try {
      await api.deleteDocument(id);
      await fetchDocuments();
    } catch (e: any) {
      setError(e.message || 'Failed to delete document');
      throw e;
    }
  }, [fetchDocuments]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  return {
    documents,
    stats,
    isLoading,
    isUploading,
    error,
    refreshDocuments: fetchDocuments,
    uploadFiles,
    deleteDocument: deleteDoc,
  };
}
