import React, { useEffect, useState } from 'react';
import { OverviewAnalytics, SessionSummary } from '../types/graph';
import { fetchOverviewAnalytics, fetchSessions } from '../api/client';
import { StatsCards } from '../components/StatsCards';
import { SessionTable } from '../components/SessionTable';
import { RefreshCw, Search, Filter } from 'lucide-react';

interface Props {
  onSelectSession: (id: string) => void;
}

export const SessionsPage: React.FC<Props> = ({ onSelectSession }) => {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [analytics, setAnalytics] = useState<OverviewAnalytics | null>(null);
  const [loading, setLoading] = useState(false);
  const [agentFilter, setAgentFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState<string | null>(null);

  const loadData = () => {
    setLoading(true);
    setError(null);
    Promise.all([
      fetchSessions(agentFilter || undefined, statusFilter || undefined),
      fetchOverviewAnalytics(),
    ])
      .then(([sessionsData, analyticsData]) => {
        setSessions(sessionsData);
        setAnalytics(analyticsData);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'Unable to load sessions.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000); // Auto-refresh every 5s
    return () => clearInterval(interval);
  }, [agentFilter, statusFilter]);

  const filteredSessions = sessions.filter((s) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return s.id.toLowerCase().includes(q) || s.agent_id.toLowerCase().includes(q);
  });

  return (
    <div>
      {/* Top Stats */}
      <div style={{ marginBottom: '22px' }}>
        <p className="eyebrow">AgentDAC / overview</p>
        <h2 className="page-title">Sessions & traces</h2>
        <p className="page-subtitle">Inspect execution paths, costs, and model activity from live telemetry.</p>
      </div>
      <StatsCards analytics={analytics} />
      {error && <div className="state-error" role="alert">{error}<button className="btn-secondary" onClick={loadData}>Try again</button></div>}

      {/* Filter and Search Bar */}
      <div
        className="glass-panel"
        style={{
          padding: '16px 20px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1, minWidth: '260px' }}>
          <div style={{ position: 'relative', width: '100%', maxWidth: '320px' }}>
            <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search by Session ID or Agent..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                background: 'rgba(15, 23, 42, 0.6)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                padding: '8px 12px 8px 36px',
                color: 'var(--text-primary)',
                fontSize: '13px',
                outline: 'none',
              }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Filter size={16} style={{ color: 'var(--text-muted)' }} />
            <select
              value={agentFilter}
              onChange={(e) => setAgentFilter(e.target.value)}
              style={{
                background: 'rgba(15, 23, 42, 0.6)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                padding: '8px 12px',
                color: 'var(--text-primary)',
                fontSize: '13px',
                outline: 'none',
              }}
            >
              <option value="">All Agents</option>
              {Array.from(new Set(sessions.map((session) => session.agent_id))).sort().map((agent) => (
                <option value={agent} key={agent}>{agent}</option>
              ))}
            </select>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{
                background: 'rgba(15, 23, 42, 0.6)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                padding: '8px 12px',
                color: 'var(--text-primary)',
                fontSize: '13px',
                outline: 'none',
              }}
            >
              <option value="">All Statuses</option>
              <option value="SUCCESS">SUCCESS</option>
              <option value="RUNNING">RUNNING</option>
              <option value="ERROR">ERROR</option>
            </select>
          </div>
        </div>

        <button className="btn-secondary" onClick={loadData} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Sessions Table */}
      <SessionTable sessions={filteredSessions} onSelectSession={onSelectSession} />
    </div>
  );
};
