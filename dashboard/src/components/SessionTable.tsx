import React from 'react';
import { SessionSummary } from '../types/graph';
import { Clock, Cpu, ExternalLink, Hash } from 'lucide-react';

interface Props {
  sessions: SessionSummary[];
  onSelectSession: (id: string) => void;
}

export const SessionTable: React.FC<Props> = ({ sessions, onSelectSession }) => {
  const getStatusBadge = (status: string) => {
    const s = status.toUpperCase();
    if (s === 'SUCCESS' || s === 'OK') {
      return <span className="badge-ok" style={{ padding: '4px 10px', borderRadius: '20px', fontSize: '12px', fontWeight: 600 }}>SUCCESS</span>;
    }
    if (s === 'ERROR' || s === 'FAILED') {
      return <span className="badge-error" style={{ padding: '4px 10px', borderRadius: '20px', fontSize: '12px', fontWeight: 600 }}>ERROR</span>;
    }
    return <span className="badge-running" style={{ padding: '4px 10px', borderRadius: '20px', fontSize: '12px', fontWeight: 600 }}>RUNNING</span>;
  };

  const formatDate = (iso: string) => {
    try {
      const d = new Date(iso);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' ' + d.toLocaleDateString([], { month: 'short', day: 'numeric' });
    } catch {
      return iso;
    }
  };

  if (sessions.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '48px', textAlign: 'center', color: 'var(--text-secondary)' }}>
        <Cpu size={40} style={{ margin: '0 auto 16px', opacity: 0.4 }} />
        <h4 style={{ fontSize: '18px', color: 'var(--text-primary)', marginBottom: '8px' }}>No Sessions Recorded Yet</h4>
        <p style={{ fontSize: '14px', maxWidth: '400px', margin: '0 auto' }}>
          Instrument your agent using the AOG Python SDK or Claude Code adapter to view real-time traces and DAGs.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-panel" style={{ overflow: 'hidden' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
        <thead>
          <tr style={{ background: 'rgba(30, 41, 59, 0.5)', borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-secondary)' }}>
            <th style={{ padding: '14px 20px', fontWeight: 600 }}>Session ID</th>
            <th style={{ padding: '14px 20px', fontWeight: 600 }}>Agent</th>
            <th style={{ padding: '14px 20px', fontWeight: 600 }}>Started</th>
            <th style={{ padding: '14px 20px', fontWeight: 600 }}>Duration</th>
            <th style={{ padding: '14px 20px', fontWeight: 600 }}>Events</th>
            <th style={{ padding: '14px 20px', fontWeight: 600 }}>Tokens</th>
            <th style={{ padding: '14px 20px', fontWeight: 600 }}>Cost</th>
            <th style={{ padding: '14px 20px', fontWeight: 600 }}>Status</th>
            <th style={{ padding: '14px 20px', fontWeight: 600, textAlign: 'right' }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {sessions.map((session) => (
            <tr
              key={session.id}
              onClick={() => onSelectSession(session.id)}
              style={{
                borderBottom: '1px solid var(--border-subtle)',
                cursor: 'pointer',
                transition: 'background 0.15s ease',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)')}
              onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
            >
              <td style={{ padding: '16px 20px', fontFamily: 'JetBrains Mono', fontSize: '13px', color: '#818cf8', fontWeight: 500 }}>
                {session.id.slice(0, 16)}...
              </td>
              <td style={{ padding: '16px 20px', fontWeight: 500, color: 'var(--text-primary)' }}>
                {session.agent_id}
              </td>
              <td style={{ padding: '16px 20px', color: 'var(--text-secondary)' }}>
                {formatDate(session.started_at)}
              </td>
              <td style={{ padding: '16px 20px', color: 'var(--text-secondary)' }}>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                  <Clock size={14} style={{ opacity: 0.6 }} />
                  {session.duration_s != null ? `${session.duration_s}s` : '—'}
                </span>
              </td>
              <td style={{ padding: '16px 20px', color: 'var(--text-secondary)' }}>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                  <Hash size={14} style={{ opacity: 0.6 }} />
                  {session.event_count}
                </span>
              </td>
              <td style={{ padding: '16px 20px', color: 'var(--text-secondary)' }}>
                {session.total_tokens.toLocaleString()}
              </td>
              <td style={{ padding: '16px 20px', color: 'var(--text-secondary)' }}>
                {session.cost_usd != null ? `$${session.cost_usd.toFixed(4)}` : '—'}
              </td>
              <td style={{ padding: '16px 20px' }}>
                {getStatusBadge(session.status)}
              </td>
              <td style={{ padding: '16px 20px', textAlign: 'right' }}>
                <button
                  className="btn-secondary"
                  style={{ padding: '6px 12px', fontSize: '12px' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectSession(session.id);
                  }}
                >
                  Inspect DAG <ExternalLink size={14} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
