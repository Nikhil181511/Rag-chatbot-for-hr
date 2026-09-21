import React, { useRef } from 'react';
import { X, UploadCloud, File, Trash2, CheckCircle2, Clock, AlertTriangle, Lock } from 'lucide-react';
import { DocumentItem } from '../types';
import { useAuth } from '../context/AuthContext';

interface DocumentModalProps {
  isOpen: boolean;
  onClose: () => void;
  documents: DocumentItem[];
  isUploading: boolean;
  error?: string | null;
  onUpload: (files: FileList) => Promise<void> | void;
  onDelete: (id: string) => void;
}

export const DocumentModal: React.FC<DocumentModalProps> = ({
  isOpen,
  onClose,
  documents,
  isUploading,
  error: externalError,
  onUpload,
  onDelete,
}) => {
  const { isHR } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [localError, setLocalError] = React.useState<string | null>(null);

  if (!isOpen) return null;

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setLocalError(null);
      try {
        await onUpload(e.target.files);
      } catch (err: any) {
        setLocalError(err.message || 'Failed to upload document');
      } finally {
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }
    }
  };

  const getStatusBadge = (status: DocumentItem['status']) => {
    switch (status) {
      case 'READY':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: 'var(--accent-emerald)', fontSize: '0.78rem' }}>
            <CheckCircle2 size={13} /> Ready
          </span>
        );
      case 'PROCESSING':
      case 'INDEXING':
      case 'UPLOADING':
      case 'PENDING':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: 'var(--accent-cyan)', fontSize: '0.78rem' }}>
            <Clock size={13} /> {status}
          </span>
        );
      case 'FAILED':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: 'var(--accent-rose)', fontSize: '0.78rem' }}>
            <AlertTriangle size={13} /> Failed
          </span>
        );
      default:
        return <span>{status}</span>;
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h2 style={{ fontSize: '1.15rem', fontWeight: 600 }}>HR Knowledge Base Documents</h2>
              {isHR ? (
                <span style={{ fontSize: '0.7rem', background: 'rgba(244, 63, 94, 0.15)', color: '#FDA4AF', padding: '2px 8px', borderRadius: '6px', fontWeight: 600 }}>
                  HR Admin (Upload Allowed)
                </span>
              ) : (
                <span style={{ fontSize: '0.7rem', background: 'rgba(6, 182, 212, 0.15)', color: '#67E8F9', padding: '2px 8px', borderRadius: '6px', fontWeight: 600 }}>
                  Employee (Read Only)
                </span>
              )}
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-dim)', marginTop: '2px' }}>
              {isHR
                ? 'Upload and manage company policies, benefits guides, onboarding handbooks (PDF, DOCX, XLSX, TXT)'
                : 'Browse indexed HR reference documents available to the assistant for answering queries.'}
            </p>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-dim)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <div style={{ padding: '24px', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Error Banner if upload or operation fails */}
          {(localError || externalError) && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '12px 16px',
                borderRadius: '8px',
                background: 'rgba(244, 63, 94, 0.15)',
                border: '1px solid rgba(244, 63, 94, 0.3)',
                color: '#FDA4AF',
                fontSize: '0.85rem',
              }}
            >
              <AlertTriangle size={18} style={{ flexShrink: 0 }} />
              <span style={{ flex: 1 }}>{localError || externalError}</span>
              <button
                onClick={() => setLocalError(null)}
                style={{ background: 'transparent', border: 'none', color: '#FDA4AF', cursor: 'pointer', fontSize: '14px' }}
              >
                ✕
              </button>
            </div>
          )}

          {/* Upload Dropzone - ONLY VISIBLE TO HR */}
          {isHR ? (
            <div
              onClick={() => fileInputRef.current?.click()}
              style={{
                border: '2px dashed var(--border-color)',
                borderRadius: '12px',
                padding: '24px',
                textAlign: 'center',
                cursor: 'pointer',
                background: 'rgba(255, 255, 255, 0.02)',
                transition: 'all 0.2s ease',
              }}
            >
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                multiple
                accept=".pdf,.docx,.txt,.md,.xlsx,.xls,.csv"
                style={{ display: 'none' }}
              />
              <UploadCloud size={36} style={{ color: '#818CF8', margin: '0 auto 12px auto' }} />
              <div style={{ fontWeight: 500, fontSize: '0.95rem' }}>
                {isUploading ? 'Uploading & Indexing files...' : 'Click to select HR documents'}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)', marginTop: '4px' }}>
                Supports PDF, Word (.docx), Excel (.xlsx), CSV, Text (.txt, .md) up to 50MB
              </div>
            </div>
          ) : (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '14px 18px',
                background: 'rgba(6, 182, 212, 0.08)',
                border: '1px solid rgba(6, 182, 212, 0.25)',
                borderRadius: '10px',
                color: '#67E8F9',
                fontSize: '0.85rem',
              }}
            >
              <Lock size={20} style={{ flexShrink: 0 }} />
              <div>
                <strong>Read-Only Access:</strong> Document uploading and knowledge base indexing are restricted to HR Administrators. As an employee, you can ask any question in the chat based on these documents.
              </div>
            </div>
          )}

          {/* Documents Table / List */}
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '12px' }}>
              Indexed Policy Documents ({documents.length})
            </div>

            {documents.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.88rem' }}>
                No documents indexed yet.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      background: 'var(--bg-card)',
                      border: '1px solid var(--border-color)',
                      borderRadius: '10px',
                      padding: '12px 16px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <File size={20} color="#818CF8" />
                      <div>
                        <div style={{ fontWeight: 500, fontSize: '0.9rem' }}>{doc.file_name}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'flex', gap: '10px', marginTop: '2px' }}>
                          <span>{(doc.file_size / 1024).toFixed(1)} KB</span>
                          <span>•</span>
                          <span>{doc.chunk_count} Chunks</span>
                          {doc.document_category && (
                            <>
                              <span>•</span>
                              <span style={{ color: '#A5B4FC' }}>{doc.document_category}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                      {getStatusBadge(doc.status)}
                      {/* Delete button only available for HR */}
                      {isHR && (
                        <button
                          onClick={() => onDelete(doc.id)}
                          title="Delete Document (HR Only)"
                          style={{
                            background: 'transparent',
                            border: 'none',
                            color: 'var(--text-dim)',
                            cursor: 'pointer',
                          }}
                        >
                          <Trash2 size={16} />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
