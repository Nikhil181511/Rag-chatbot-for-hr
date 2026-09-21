import React from 'react';
import { AuthProvider } from './context/AuthContext';
import { AppContent } from './AppContent';

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};
