import React, { useState } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { MessageList } from './components/MessageList';
import { EmptyState } from './components/EmptyState';
import { ChatInput } from './components/ChatInput';
import { CitationPanel } from './components/CitationPanel';
import { DocumentModal } from './components/DocumentModal';
import { useChat } from './hooks/useChat';
import { useDocuments } from './hooks/useDocuments';

export const App: React.FC = () => {
  const [isDocModalOpen, setIsDocModalOpen] = useState(false);

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
          documentCount={documents.filter((d) => d.status === 'READY').length}
        />

        {messages.length === 0 ? (
          <EmptyState onSelectPrompt={sendMessage} />
        ) : (
          <MessageList
            messages={messages}
            onCitationClick={setSelectedCitation}
          />
        )}

        <ChatInput
          onSendMessage={sendMessage}
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
    </div>
  );
};
