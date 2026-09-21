import React, { useState } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { MessageList } from './components/MessageList';
import { EmptyState } from './components/EmptyState';
import { ChatInput } from './components/ChatInput';
import { CitationPanel } from './components/CitationPanel';
import { DocumentModal } from './components/DocumentModal';
import { AuthModal } from './components/AuthModal';
import { useChat } from './hooks/useChat';
import { useDocuments } from './hooks/useDocuments';
import { useAuth } from './context/AuthContext';

export const AppContent: React.FC = () => {
  const [isDocModalOpen, setIsDocModalOpen] = useState(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const { isAuthenticated } = useAuth();

  const {
    messages,
    isGenerating,
    activeConversationId,
    selectedCitation,
    setSelectedCitation,
    sendMessage,
    stopGeneration,
    loadConversation,
    clearChat,
  } = useChat();

  const {
    documents,
    isUploading,
    uploadFiles,
    deleteDocument,
  } = useDocuments();

  const handleSendMessage = (query: string) => {
    if (!isAuthenticated) {
      setIsAuthModalOpen(true);
      return;
    }
    sendMessage(query);
  };

  return (
    <div className="app-container">
      {/* Sidebar with conversations */}
      <Sidebar
        activeId={activeConversationId}
        onSelectConversation={loadConversation}
        onNewChat={clearChat}
      />

      {/* Main Chat Workspace */}
      <main className="main-content">
        <Header
          onOpenDocs={() => setIsDocModalOpen(true)}
          onOpenAuth={() => setIsAuthModalOpen(true)}
          documentCount={documents.filter((d) => d.status === 'READY').length}
        />

        {messages.length === 0 ? (
          <EmptyState onSelectPrompt={handleSendMessage} />
        ) : (
          <MessageList
            messages={messages}
            onCitationClick={setSelectedCitation}
          />
        )}

        <ChatInput
          onSendMessage={handleSendMessage}
          onStop={stopGeneration}
          isGenerating={isGenerating}
        />
      </main>

      {/* Citation Slide-out Panel */}
      <CitationPanel
        citation={selectedCitation}
        onClose={() => setSelectedCitation(null)}
      />

      {/* Document Management Modal */}
      <DocumentModal
        isOpen={isDocModalOpen}
        onClose={() => setIsDocModalOpen(false)}
        documents={documents}
        isUploading={isUploading}
        onUpload={uploadFiles}
        onDelete={deleteDocument}
      />

      {/* Authentication Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
      />
    </div>
  );
};
