import React, { useEffect, useState } from 'react';
import { TraceGraphResponse } from '../types/graph';
import { fetchTraceGraph } from '../api/client';
import { ExecutionGraph } from '../components/ExecutionGraph';
import { NodeInspector } from '../components/NodeInspector';
import { Timeline } from '../components/Timeline';
import { ArrowLeft, Clock, Cpu, DollarSign, Bot, RefreshCw } from 'lucide-react';

interface Props {
  sessionId: string;
  onBack: () => void;
}

export const SessionPage: React.FC<Props> = ({ sessionId, onBack }) => {
  const [traceData, setTraceData] = useState<TraceGraphResponse | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'graph' | 'timeline'>('graph');
  const [error, setError] = useState<string | null>(null);

  const loadTrace = (silent: boolean = false) => {
    if (!silent) setLoading(true);
    setError(null);
    fetchTraceGraph(sessionId)
      .then((data) => {
        setTraceData(data);
        if (data.nodes.length > 0 && !selectedNodeId) {
          setSelectedNodeId(data.nodes[0].id);
        }
      })
      .catch((err: unknown) => {
        if (!silent) setError(err instanceof Error ? err.message : 'Unable to load this trace.');
      })
      .finally(() => {
        if (!silent) setLoading(false);
      });
  };

  useEffect(() => {
    setSelectedNodeId(null);
    loadTrace(false);
  }, [sessionId]);

  // Live polling for running sessions
  useEffect(() => {
    const isRunning = !traceData?.session || traceData.session.status.toUpperCase() === 'RUNNING';
    if (!isRunning) return;

    const interval = setInterval(() => {
      loadTrace(true);
    }, 2500);

    return () => clearInterval(interval);
  }, [sessionId, traceData?.session?.status]);

  const handleManualRefresh = () => {
    loadTrace(false);
  };

  const session = traceData?.session;

  return (
    <div>
      {error && <div className="state-error" role="alert">{error}<button className="btn-secondary" onClick={handleManualRefresh}>Try again</button></div>}
      {!loading && !error && traceData && !traceData.session && <div className="state-empty">Session not found.</div>}
      {/* Session Top Bar */}
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <button className="btn-secondary" onClick={onBack} style={{ padding: '8px 12px' }}>
            <ArrowLeft size={16} /> Back
          </button>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>
                Session: <span style={{ color: '#818cf8', fontFamily: 'JetBrains Mono' }}>{sessionId}</span>
              </h2>
              {session && (
                <span
                  style={{
                    fontSize: '11px',
                    fontWeight: 600,
                    padding: '3px 10px',
                    borderRadius: '20px',
                    background: ['SUCCESS', 'OK'].includes(session.status.toUpperCase()) ? 'rgba(16, 185, 129, 0.15)' : session.status.toUpperCase() === 'RUNNING' ? 'rgba(99, 102, 241, 0.15)' : 'rgba(244, 63, 94, 0.15)',
                    color: ['SUCCESS', 'OK'].includes(session.status.toUpperCase()) ? '#34d399' : session.status.toUpperCase() === 'RUNNING' ? '#818cf8' : '#fb7185',
                  }}
                >
                  {session.status}
                </span>
              )}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Bot size={14} className="text-purple-400" /> Agent: <strong style={{ color: 'var(--text-primary)' }}>{session?.agent_id || 'unknown'}</strong>
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Clock size={14} className="text-indigo-400" /> Duration: {session?.duration_s != null ? `${session.duration_s}s` : '—'}
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Cpu size={14} className="text-amber-400" /> Tokens: {session?.total_tokens.toLocaleString() || 0}
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <DollarSign size={14} className="text-cyan-400" /> Cost: {session?.cost_usd != null ? `$${session.cost_usd.toFixed(4)}` : '$0.00'}
              </span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ display: 'flex', background: 'rgba(15, 23, 42, 0.6)', padding: '4px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
            <button
              style={{
                padding: '6px 14px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                background: activeTab === 'graph' ? '#6366f1' : 'transparent',
                color: activeTab === 'graph' ? '#ffffff' : 'var(--text-secondary)',
              }}
              onClick={() => setActiveTab('graph')}
            >
              Execution DAG
            </button>
            <button
              style={{
                padding: '6px 14px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                background: activeTab === 'timeline' ? '#6366f1' : 'transparent',
                color: activeTab === 'timeline' ? '#ffffff' : 'var(--text-secondary)',
              }}
              onClick={() => setActiveTab('timeline')}
            >
              Timeline View
            </button>
          </div>

          <button className="btn-secondary" onClick={handleManualRefresh} style={{ padding: '8px' }}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Main Inspection Layout (2 Column Split) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.8fr) minmax(340px, 1.2fr)', gap: '20px', marginBottom: '20px' }}>
        {/* Left Pane: Interactive Graph or Waterfall */}
        <div>
          {activeTab === 'graph' ? (
            <ExecutionGraph
              nodes={traceData?.nodes || []}
              edges={traceData?.edges || []}
              selectedNodeId={selectedNodeId}
              onSelectNode={setSelectedNodeId}
            />
          ) : (
            <Timeline
              nodes={traceData?.nodes || []}
              selectedNodeId={selectedNodeId}
              onSelectNode={setSelectedNodeId}
            />
          )}
        </div>

        {/* Right Pane: Deep Node Inspector */}
        <div>
           <NodeInspector spanId={selectedNodeId} />
        </div>
      </div>

      {/* Bottom Timeline Waterfall (if in graph mode) */}
      {activeTab === 'graph' && traceData && traceData.nodes.length > 0 && (
        <Timeline
          nodes={traceData.nodes}
          selectedNodeId={selectedNodeId}
          onSelectNode={setSelectedNodeId}
        />
      )}
    </div>
  );
};
