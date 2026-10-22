import React from 'react';
import { GraphNode } from '../types/graph';
import { Clock, Bot, Wrench, Sparkles, AlertCircle, Terminal } from 'lucide-react';

interface Props {
  nodes: GraphNode[];
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string) => void;
}

export const Timeline: React.FC<Props> = ({ nodes, selectedNodeId, onSelectNode }) => {
  const sortedNodes = [...nodes].sort(
    (a, b) => new Date(a.started_at).getTime() - new Date(b.started_at).getTime()
  );

  const getIcon = (type: string, isError: boolean) => {
    if (isError) return <AlertCircle size={14} className="text-rose-400" />;
    switch (type.toLowerCase()) {
      case 'session':
        return <Bot size={14} style={{ color: '#a855f7' }} />;
      case 'agent':
        return <Bot size={14} style={{ color: '#6366f1' }} />;
      case 'llm':
        return <Sparkles size={14} style={{ color: '#f59e0b' }} />;
      case 'tool':
        return <Wrench size={14} style={{ color: '#10b981' }} />;
      default:
        return <Terminal size={14} style={{ color: '#06b6d4' }} />;
    }
  };

  const formatTime = (iso: string) => {
    try {
      const d = new Date(iso);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + String(d.getMilliseconds()).padStart(3, '0');
    } catch {
      return iso;
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '20px' }}>
      <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Clock size={16} className="text-indigo-400" />
        Execution Timeline Waterfall
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {sortedNodes.length === 0 && <p className="state-muted" style={{ padding: '24px', textAlign: 'center' }}>No timeline events recorded.</p>}
        {sortedNodes.map((node, index) => {
          const isSelected = node.id === selectedNodeId;
          const isError = node.status.toUpperCase() === 'ERROR';

          return (
            <div
              key={node.id}
              onClick={() => onSelectNode(node.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                borderRadius: '8px',
                background: isSelected ? 'rgba(99, 102, 241, 0.15)' : 'rgba(30, 41, 59, 0.4)',
                border: isSelected ? '1px solid #818cf8' : '1px solid var(--border-subtle)',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => {
                if (!isSelected) e.currentTarget.style.background = 'rgba(51, 65, 85, 0.4)';
              }}
              onMouseLeave={(e) => {
                if (!isSelected) e.currentTarget.style.background = 'rgba(30, 41, 59, 0.4)';
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'JetBrains Mono', minWidth: '24px' }}>
                  #{index + 1}
                </span>
                <div
                  style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '6px',
                    background: 'rgba(15, 23, 42, 0.8)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {getIcon(node.type, isError)}
                </div>
                <div>
                  <span style={{ fontSize: '13px', fontWeight: 600, color: isSelected ? '#a5b4fc' : 'var(--text-primary)' }}>
                    {node.label}
                  </span>
                  <span style={{ marginLeft: '8px', fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    [{node.type}]
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)', fontFamily: 'JetBrains Mono' }}>
                  {formatTime(node.started_at)}
                </span>
                <span
                  style={{
                    fontSize: '11px',
                    fontWeight: 600,
                    padding: '3px 8px',
                    borderRadius: '6px',
                    background: 'rgba(15, 23, 42, 0.6)',
                    color: 'var(--text-secondary)',
                    minWidth: '60px',
                    textAlign: 'right',
                  }}
                >
                  {node.duration_ms != null ? `${node.duration_ms}ms` : '—'}
                </span>
                <span
                  style={{
                    fontSize: '11px',
                    fontWeight: 600,
                    padding: '2px 8px',
                    borderRadius: '12px',
                    background: isError ? 'rgba(244, 63, 94, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                    color: isError ? '#fb7185' : '#34d399',
                  }}
                >
                  {node.status}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
