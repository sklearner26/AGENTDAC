import React, { useEffect, useState } from 'react';
import { ErrorStat, ModelUsageStat, OverviewAnalytics, SessionSummary, ToolUsageStat } from '../types/graph';
import {
  fetchErrorAnalytics,
  fetchModelAnalytics,
  fetchOverviewAnalytics,
  fetchToolAnalytics,
  fetchSessions,
} from '../api/client';
import { StatsCards } from '../components/StatsCards';
import { Wrench, Sparkles, AlertTriangle, RefreshCw } from 'lucide-react';

export const AnalyticsPage: React.FC = () => {
  const [overview, setOverview] = useState<OverviewAnalytics | null>(null);
  const [tools, setTools] = useState<ToolUsageStat[]>([]);
  const [models, setModels] = useState<ModelUsageStat[]>([]);
  const [errors, setErrors] = useState<ErrorStat[]>([]);
  const [recentSessions, setRecentSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = () => {
    setLoading(true);
    setError(null);
    Promise.all([
      fetchOverviewAnalytics(),
      fetchToolAnalytics(),
      fetchModelAnalytics(),
      fetchErrorAnalytics(),
      fetchSessions(),
    ])
      .then(([ov, tl, md, er, sessions]) => {
        setOverview(ov);
        setTools(tl);
        setModels(md);
        setErrors(er);
        setRecentSessions(sessions.slice(0, 6));
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'Unable to load analytics.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div>
          <p className="eyebrow">AgentDAC / analytics</p>
          <h2 className="page-title">Analytics overview</h2>
          <p className="page-subtitle">Requests, latency, errors, tokens, spend, and the latest traces.</p>
        </div>
        <button className="btn-secondary" onClick={loadData} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>
      {error && <div className="state-error" role="alert">{error}<button className="btn-secondary" onClick={loadData}>Try again</button></div>}

      <StatsCards analytics={overview} />

      {/* Grid for Tool and Model Analytics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        {/* Tool Usage Breakdown */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Wrench size={18} className="text-emerald-400" /> Tool Invocations & Frequency
          </h3>
          {tools.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>No tool executions recorded yet.</p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ color: 'var(--text-secondary)', borderBottom: '1px solid var(--border-subtle)' }}>
                  <th style={{ padding: '8px 0', fontWeight: 600 }}>Tool Name</th>
                  <th style={{ padding: '8px 0', fontWeight: 600, textAlign: 'right' }}>Calls</th>
                </tr>
              </thead>
              <tbody>
                {tools.map((t, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '10px 0', fontFamily: 'JetBrains Mono', color: '#34d399' }}>{t.name}</td>
                    <td style={{ padding: '10px 0', textAlign: 'right', fontWeight: 600 }}>{t.count.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Model Usage Breakdown */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Sparkles size={18} className="text-amber-400" /> Model Usage & Tokens
          </h3>
          {models.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>No model calls recorded yet.</p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ color: 'var(--text-secondary)', borderBottom: '1px solid var(--border-subtle)' }}>
                  <th style={{ padding: '8px 0', fontWeight: 600 }}>Model</th>
                  <th style={{ padding: '8px 0', fontWeight: 600, textAlign: 'right' }}>Calls</th>
                  <th style={{ padding: '8px 0', fontWeight: 600, textAlign: 'right' }}>Tokens In/Out</th>
                  <th style={{ padding: '8px 0', fontWeight: 600, textAlign: 'right' }}>Cost</th>
                </tr>
              </thead>
              <tbody>
                {models.map((m, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '10px 0', fontFamily: 'JetBrains Mono', color: '#fbbf24' }}>{m.model}</td>
                    <td style={{ padding: '10px 0', textAlign: 'right' }}>{m.calls}</td>
                    <td style={{ padding: '10px 0', textAlign: 'right' }}>{(m.tokens_in + m.tokens_out).toLocaleString()}</td>
                    <td style={{ padding: '10px 0', textAlign: 'right', color: '#38bdf8' }}>${m.cost_usd.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Errors Table */}
      <div className="glass-panel" style={{ padding: '20px' }}>
        <h3 style={{ fontSize: '16px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <AlertTriangle size={18} className="text-rose-400" /> Error Frequency & Recent Failures
        </h3>
        {errors.length === 0 ? (
          <p style={{ color: '#34d399', fontSize: '13px' }}>No execution errors detected across sessions.</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
            <thead>
              <tr style={{ color: 'var(--text-secondary)', borderBottom: '1px solid var(--border-subtle)' }}>
                <th style={{ padding: '8px 0', fontWeight: 600 }}>Error Type</th>
                <th style={{ padding: '8px 0', fontWeight: 600 }}>Message</th>
                <th style={{ padding: '8px 0', fontWeight: 600, textAlign: 'right' }}>Count</th>
              </tr>
            </thead>
            <tbody>
              {errors.map((e, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '10px 0', color: '#fb7185', fontWeight: 600 }}>{e.error_type}</td>
                  <td style={{ padding: '10px 0', color: 'var(--text-secondary)' }}>{e.message}</td>
                  <td style={{ padding: '10px 0', textAlign: 'right', fontWeight: 600 }}>{e.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      <div className="glass-panel" style={{ padding: '20px', marginTop: '20px' }}>
        <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '14px' }}>Recent traces</h3>
        {recentSessions.length === 0 ? <p className="state-muted">No recent traces recorded.</p> : <div className="trace-list">{recentSessions.map((session) => <div className="trace-row" key={session.id}><span><strong>{session.agent_id}</strong><small>{session.id}</small></span><span>{session.duration_s != null ? `${session.duration_s.toFixed(2)}s` : '—'}</span><span>{session.total_tokens.toLocaleString()} tokens</span><span className={session.status.toUpperCase() === 'ERROR' ? 'text-rose-400' : 'text-emerald-400'}>{session.status}</span></div>)}</div>}
      </div>
    </div>
  );
};
