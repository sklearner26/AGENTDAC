import React, { useState } from 'react';
import { SessionsPage } from './pages/SessionsPage';
import { SessionPage } from './pages/SessionPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { ChatPage } from './pages/ChatPage';
import { IntegrationsPage } from './pages/IntegrationsPage';
import { Activity, BarChart3, Layers, MessageSquare, Terminal } from 'lucide-react';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<'sessions' | 'analytics' | 'detail' | 'chat' | 'integrations'>('sessions');
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);

  const handleSelectSession = (id: string) => {
    setSelectedSessionId(id);
    setCurrentPage('detail');
  };

  const handleBackToSessions = () => {
    setSelectedSessionId(null);
    setCurrentPage('sessions');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Header Navigation */}
      <header
        style={{
          borderBottom: '1px solid var(--border-subtle)',
          background: 'rgba(9, 13, 22, 0.8)',
          backdropFilter: 'blur(12px)',
          position: 'sticky',
          top: 0,
          zIndex: 50,
          padding: '12px 32px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
          {/* Logo */}
          <div
            onClick={handleBackToSessions}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              cursor: 'pointer',
            }}
          >
            <div
              style={{
                width: '34px',
                height: '34px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 15px rgba(99, 102, 241, 0.5)',
              }}
            >
              <Layers size={20} style={{ color: 'white' }} />
            </div>
            <div>
              <h1 style={{ fontSize: '17px', fontWeight: 800, letterSpacing: '-0.02em', background: 'linear-gradient(to right, #ffffff, #94a3b8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                AOG
              </h1>
              <span style={{ fontSize: '10px', color: '#818cf8', fontWeight: 600, letterSpacing: '0.05em' }}>
                OBSERVABILITY GRAPH
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={() => {
                setSelectedSessionId(null);
                setCurrentPage('sessions');
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 14px',
                borderRadius: '8px',
                fontSize: '13px',
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                background: currentPage === 'sessions' || currentPage === 'detail' ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                color: currentPage === 'sessions' || currentPage === 'detail' ? '#818cf8' : 'var(--text-secondary)',
                transition: 'all 0.15s ease',
              }}
            >
              <Activity size={16} /> Sessions & Traces
            </button>

            <button
              onClick={() => {
                setSelectedSessionId(null);
                setCurrentPage('analytics');
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 14px',
                borderRadius: '8px',
                fontSize: '13px',
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                background: currentPage === 'analytics' ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                color: currentPage === 'analytics' ? '#818cf8' : 'var(--text-secondary)',
                transition: 'all 0.15s ease',
              }}
            >
              <BarChart3 size={16} /> Analytics
            </button>
            <button
              onClick={() => {
                setSelectedSessionId(null);
                setCurrentPage('chat');
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 14px',
                borderRadius: '8px',
                fontSize: '13px',
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                background: currentPage === 'chat' ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                color: currentPage === 'chat' ? '#818cf8' : 'var(--text-secondary)',
                transition: 'all 0.15s ease',
              }}
            >
              <MessageSquare size={16} /> AI Chat
            </button>
            <button
              onClick={() => {
                setSelectedSessionId(null);
                setCurrentPage('integrations');
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 14px',
                borderRadius: '8px',
                fontSize: '13px',
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                background: currentPage === 'integrations' ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                color: currentPage === 'integrations' ? '#818cf8' : 'var(--text-secondary)',
                transition: 'all 0.15s ease',
              }}
            >
              <Terminal size={16} /> Integrations
            </button>
          </nav>
        </div>

        {/* Server Status Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '12px',
              color: '#34d399',
              background: 'rgba(16, 185, 129, 0.1)',
              padding: '5px 12px',
              borderRadius: '20px',
              border: '1px solid rgba(16, 185, 129, 0.2)',
            }}
          >
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 8px #10b981' }} />
            Ingestion Online
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={{ flex: 1, padding: '32px', maxWidth: '1440px', margin: '0 auto', width: '100%' }}>
        {currentPage === 'sessions' && <SessionsPage onSelectSession={handleSelectSession} />}
        {currentPage === 'detail' && selectedSessionId && (
          <SessionPage sessionId={selectedSessionId} onBack={handleBackToSessions} />
        )}
        {currentPage === 'analytics' && <AnalyticsPage />}
        {currentPage === 'chat' && <ChatPage />}
        {currentPage === 'integrations' && <IntegrationsPage onSelectSession={handleSelectSession} />}
      </main>

      {/* Footer */}
      <footer
        style={{
          borderTop: '1px solid var(--border-subtle)',
          padding: '16px 32px',
          textAlign: 'center',
          fontSize: '12px',
          color: 'var(--text-muted)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div>Agent Observability Graph (AOG) v0.1.0</div>
        <div style={{ display: 'flex', gap: '16px' }}>
          <span>PostgreSQL Durable Store</span>
          <span>OpenTelemetry Compatible</span>
          <span>Fail-Open Architecture</span>
        </div>
      </footer>
    </div>
  );
};
export default App;
