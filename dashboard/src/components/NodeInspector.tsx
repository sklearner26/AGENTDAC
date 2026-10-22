import React, { useEffect, useState } from 'react';
import { SpanDetail } from '../types/graph';
import { fetchSpan } from '../api/client';
import { Copy, Check, Info, FileCode, AlertTriangle, Cpu, DollarSign, Clock } from 'lucide-react';

interface Props {
  spanId: string | null;
}

export const NodeInspector: React.FC<Props> = ({ spanId }) => {
  const [span, setSpan] = useState<SpanDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!spanId) {
      setSpan(null);
      return;
    }
    setLoading(true);
    setError(null);
    fetchSpan(spanId)
      .then(setSpan)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'Unable to load node details.'))
      .finally(() => setLoading(false));
  }, [spanId]);

  const handleCopyJson = () => {
    if (!span) return;
    navigator.clipboard.writeText(JSON.stringify(span, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!spanId) {
    return (
      <div className="glass-panel" style={{ padding: '32px', textAlign: 'center', color: 'var(--text-secondary)', height: '100%' }}>
        <Info size={32} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
        <h4 style={{ fontSize: '16px', color: 'var(--text-primary)', marginBottom: '6px' }}>No Node Selected</h4>
        <p style={{ fontSize: '13px' }}>Click any node on the DAG or Timeline to inspect inputs, outputs, tokens, and errors.</p>
      </div>
    );
  }

  if (loading || !span) {
    return (
      <div className="glass-panel" style={{ padding: '32px', textAlign: 'center', color: 'var(--text-secondary)' }}>
        <div style={{ fontSize: '14px' }}>{error ?? 'Loading node details...'}</div>
      </div>
    );
  }

  const isError = span.status.toUpperCase() === 'ERROR';

  return (
    <div className="glass-panel" style={{ padding: '20px', height: '100%', overflowY: 'auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '16px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '16px' }}>
        <div>
          <span style={{ fontSize: '11px', textTransform: 'uppercase', fontWeight: 700, color: '#818cf8', letterSpacing: '0.05em' }}>
            {span.event_type}
          </span>
          <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
            {span.name}
          </h3>
          <p style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'JetBrains Mono', marginTop: '2px' }}>
            ID: {span.id}
          </p>
        </div>

        <button className="btn-secondary" style={{ padding: '6px 10px', fontSize: '12px' }} onClick={handleCopyJson}>
          {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
          {copied ? 'Copied' : 'Copy JSON'}
        </button>
      </div>

      <div className="inspector-meta">
        <span className={isError ? 'badge-error' : 'badge-ok'} style={{ padding: '4px 9px', borderRadius: '999px', fontSize: '11px', fontWeight: 700 }}>{span.status}</span>
        <span>{span.model ?? 'Model unavailable'}</span>
        <span>{span.provider ?? 'Provider unavailable'}</span>
      </div>

      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', marginBottom: '16px' }}>
        <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '10px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <span style={{ fontSize: '11px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Clock size={12} /> Duration
          </span>
          <p style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', marginTop: '4px' }}>
            {span.duration_ms != null ? `${span.duration_ms}ms` : '—'}
          </p>
        </div>
        <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '10px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Input / output</span>
          <p style={{ fontSize: '14px', fontWeight: 600, marginTop: '4px' }}>{(span.tokens_in ?? 0).toLocaleString()} / {(span.tokens_out ?? 0).toLocaleString()}</p>
        </div>

        <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '10px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <span style={{ fontSize: '11px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Cpu size={12} /> Tokens
          </span>
          <p style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', marginTop: '4px' }}>
            {((span.tokens_in || 0) + (span.tokens_out || 0)).toLocaleString()}
          </p>
        </div>

        <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '10px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <span style={{ fontSize: '11px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <DollarSign size={12} /> Cost
          </span>
          <p style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', marginTop: '4px' }}>
            {span.cost_usd != null ? `$${span.cost_usd.toFixed(4)}` : '—'}
          </p>
        </div>
      </div>

      <div className="detail-grid">
        {(['reason', 'skill', 'tool'] as const).map((key) => {
          const value = span.attributes?.[key];
          return value == null ? null : <div key={key}><span className="detail-label">{key}</span><strong>{String(value)}</strong></div>;
        })}
      </div>

      {/* Error Banner */}
      {isError && span.error && (
        <div style={{ background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)', borderRadius: '8px', padding: '12px', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#fb7185', fontWeight: 600, fontSize: '13px', marginBottom: '4px' }}>
            <AlertTriangle size={16} />
            {span.error.type}: {span.error.message}
          </div>
          {span.error.stacktrace && (
            <pre style={{ fontSize: '11px', color: '#fca5a5', background: 'rgba(0,0,0,0.3)', padding: '8px', borderRadius: '6px', overflowX: 'auto', marginTop: '6px' }}>
              {span.error.stacktrace}
            </pre>
          )}
        </div>
      )}

      {/* Input Payload */}
      {span.input && (
        <div style={{ marginBottom: '16px' }}>
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
            <FileCode size={14} /> Input Data
          </span>
          <pre style={{ fontSize: '12px', color: '#cbd5e1', background: 'rgba(15, 23, 42, 0.8)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)', overflowX: 'auto' }}>
            {JSON.stringify(span.input, null, 2)}
          </pre>
        </div>
      )}

      {/* Output Payload */}
      {span.output && (
        <div style={{ marginBottom: '16px' }}>
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
            <FileCode size={14} /> Output Data
          </span>
          <pre style={{ fontSize: '12px', color: '#cbd5e1', background: 'rgba(15, 23, 42, 0.8)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)', overflowX: 'auto' }}>
            {JSON.stringify(span.output, null, 2)}
          </pre>
        </div>
      )}

      {/* Attributes & Metadata */}
      {span.attributes && Object.keys(span.attributes).length > 0 && (
        <div>
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px', display: 'block' }}>
            Attributes
          </span>
          <pre style={{ fontSize: '12px', color: '#94a3b8', background: 'rgba(15, 23, 42, 0.8)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)', overflowX: 'auto' }}>
            {JSON.stringify(span.attributes, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
