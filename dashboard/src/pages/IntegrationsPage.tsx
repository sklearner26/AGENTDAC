import React, { useEffect, useState } from 'react';
import {
  ClaudeCodeIntegrationStatus,
} from '../types/graph';
import {
  fetchClaudeCodeStatus,
  configureClaudeCodeIntegration,
  disconnectClaudeCodeIntegration,
  toggleClaudeCodePause,
  sendClaudeCodeTestEvent,
} from '../api/client';
import {
  Terminal,
  CheckCircle2,
  AlertCircle,
  Play,
  Pause,
  Trash2,
  RefreshCw,
  Shield,
  Layers,
  ArrowRight,
  Copy,
  Check,
  FileCode,
  Zap,
} from 'lucide-react';

interface Props {
  onSelectSession: (id: string) => void;
}

export const IntegrationsPage: React.FC<Props> = ({ onSelectSession }) => {
  const [status, setStatus] = useState<ClaudeCodeIntegrationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [copiedSnippet, setCopiedSnippet] = useState(false);

  const loadStatus = async () => {
    try {
      setLoading(true);
      const data = await fetchClaudeCodeStatus();
      setStatus(data);
    } catch (err: unknown) {
      setMessage({
        text: err instanceof Error ? err.message : 'Failed to query Claude Code status',
        type: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleConfigure = async () => {
    setActionLoading(true);
    setMessage(null);
    try {
      const res = await configureClaudeCodeIntegration();
      setMessage({ text: res.message || 'Claude Code hooks configured successfully!', type: 'success' });
      await loadStatus();
    } catch (err: unknown) {
      setMessage({ text: err instanceof Error ? err.message : 'Configuration failed', type: 'error' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleDisconnect = async () => {
    if (!window.confirm('Disconnect Claude Code integration? AgentDAC hooks will be removed from your ~/.claude/settings.json.')) {
      return;
    }
    setActionLoading(true);
    setMessage(null);
    try {
      const res = await disconnectClaudeCodeIntegration();
      setMessage({ text: res.message || 'Claude Code integration disconnected.', type: 'success' });
      await loadStatus();
    } catch (err: unknown) {
      setMessage({ text: err instanceof Error ? err.message : 'Disconnection failed', type: 'error' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleTogglePause = async () => {
    setActionLoading(true);
    setMessage(null);
    try {
      const res = await toggleClaudeCodePause();
      setMessage({
        text: res.paused ? 'Claude Code ingestion paused.' : 'Claude Code ingestion resumed.',
        type: 'success',
      });
      await loadStatus();
    } catch (err: unknown) {
      setMessage({ text: err instanceof Error ? err.message : 'Pause toggle failed', type: 'error' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleSendTestEvent = async () => {
    setActionLoading(true);
    setMessage(null);
    try {
      const res = await sendClaudeCodeTestEvent();
      setMessage({
        text: `Test Claude Code session created (${res.session_id})! Opening session graph...`,
        type: 'success',
      });
      await loadStatus();
      setTimeout(() => {
        onSelectSession(res.session_id);
      }, 800);
    } catch (err: unknown) {
      setMessage({ text: err instanceof Error ? err.message : 'Test event failed', type: 'error' });
    } finally {
      setActionLoading(false);
    }
  };

  const copyConfigSnippet = () => {
    if (!status) return;
    const snippet = {
      hooks: {
        SessionStart: [{ matcher: '', hooks: [{ type: 'command', command: `python "${status.hook_script_path}"` }] }],
        UserPromptSubmit: [{ matcher: '', hooks: [{ type: 'command', command: `python "${status.hook_script_path}"` }] }],
        PreToolUse: [{ matcher: '', hooks: [{ type: 'command', command: `python "${status.hook_script_path}"` }] }],
        PostToolUse: [{ matcher: '', hooks: [{ type: 'command', command: `python "${status.hook_script_path}"` }] }],
        Notification: [{ matcher: '', hooks: [{ type: 'command', command: `python "${status.hook_script_path}"` }] }],
        Stop: [{ matcher: '', hooks: [{ type: 'command', command: `python "${status.hook_script_path}"` }] }],
      },
    };
    navigator.clipboard.writeText(JSON.stringify(snippet, null, 2));
    setCopiedSnippet(true);
    setTimeout(() => setCopiedSnippet(false), 2000);
  };

  const getStatusBadge = () => {
    if (!status) return null;
    switch (status.status) {
      case 'running':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: 600, background: 'rgba(99, 102, 241, 0.2)', color: '#a5b4fc', border: '1px solid rgba(99, 102, 241, 0.4)' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#818cf8', boxShadow: '0 0 10px #818cf8' }} />
            Session Active & Emitting
          </span>
        );
      case 'connected':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: 600, background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
            <CheckCircle2 size={14} /> Connected & Ready
          </span>
        );
      case 'paused':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: 600, background: 'rgba(148, 163, 184, 0.15)', color: '#94a3b8', border: '1px solid rgba(148, 163, 184, 0.3)' }}>
            <Pause size={14} /> Telemetry Paused
          </span>
        );
      case 'setup_required':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: 600, background: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
            <AlertCircle size={14} /> Setup Required
          </span>
        );
      default:
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: 600, background: 'rgba(244, 63, 94, 0.15)', color: '#fb7185', border: '1px solid rgba(244, 63, 94, 0.3)' }}>
            <AlertCircle size={14} /> CLI Not Connected
          </span>
        );
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Page Header */}
      <div>
        <div className="eyebrow">AGENTDAC ECOSYSTEM</div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h1 className="page-title">CLI Integrations & Telemetry</h1>
            <p className="page-subtitle">Connect your local Claude Code CLI to visualize live execution DAGs, tools, and token metrics.</p>
          </div>
          <button className="btn-secondary" onClick={loadStatus} disabled={loading} style={{ padding: '8px 14px' }}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
        </div>
      </div>

      {message && (
        <div
          style={{
            padding: '12px 18px',
            borderRadius: '10px',
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: message.type === 'success' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(244, 63, 94, 0.12)',
            color: message.type === 'success' ? '#34d399' : '#fda4af',
            border: `1px solid ${message.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
          }}
        >
          <span>{message.text}</span>
          <button
            onClick={() => setMessage(null)}
            style={{ background: 'transparent', border: 'none', color: 'inherit', cursor: 'pointer', fontSize: '16px' }}
          >
            ×
          </button>
        </div>
      )}

      {/* Main Integration Card */}
      <div className="glass-panel" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div
              style={{
                width: '56px',
                height: '56px',
                borderRadius: '14px',
                background: 'linear-gradient(135deg, #cc6633 0%, #d97706 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 20px rgba(217, 119, 6, 0.4)',
              }}
            >
              <Terminal size={30} style={{ color: 'white' }} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>Claude Code CLI</h2>
                {getStatusBadge()}
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                Anthropic's official terminal agent. Hooks into lifecycle events to stream tools, file ops, and session DAGs.
              </p>
            </div>
          </div>

          {/* Action buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            {status?.hooks_configured ? (
              <>
                <button
                  className="btn-primary"
                  onClick={handleSendTestEvent}
                  disabled={actionLoading}
                  style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' }}
                >
                  <Zap size={14} /> Send Test Event
                </button>
                <button
                  className="btn-secondary"
                  onClick={handleTogglePause}
                  disabled={actionLoading}
                >
                  {status.paused ? <Play size={14} /> : <Pause size={14} />}
                  {status.paused ? 'Resume Telemetry' : 'Pause Telemetry'}
                </button>
                <button
                  className="btn-secondary"
                  onClick={handleDisconnect}
                  disabled={actionLoading}
                  style={{ color: '#fda4af', borderColor: 'rgba(244, 63, 94, 0.3)' }}
                >
                  <Trash2 size={14} /> Disconnect
                </button>
              </>
            ) : (
              <button
                className="btn-primary"
                onClick={handleConfigure}
                disabled={actionLoading}
              >
                <CheckCircle2 size={14} /> Enable & Auto-Configure
              </button>
            )}
          </div>
        </div>

        {/* Diagnostic Meta Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '14px',
            padding: '16px',
            background: 'rgba(15, 23, 42, 0.5)',
            borderRadius: '10px',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div>
            <div className="eyebrow" style={{ fontSize: '10px' }}>CLI VERSION</div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
              {status?.cli_version || (status?.cli_installed ? 'Installed' : 'Not detected in PATH')}
            </div>
          </div>
          <div>
            <div className="eyebrow" style={{ fontSize: '10px' }}>OBSERVED SESSIONS</div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
              {status?.observed_sessions_count || 0} sessions
            </div>
          </div>
          <div>
            <div className="eyebrow" style={{ fontSize: '10px' }}>LAST ACTIVITY</div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
              {status?.last_activity ? new Date(status.last_activity).toLocaleTimeString() : 'No events yet'}
            </div>
          </div>
          <div>
            <div className="eyebrow" style={{ fontSize: '10px' }}>INGESTION ENDPOINT</div>
            <div style={{ fontSize: '12px', fontFamily: 'JetBrains Mono', color: '#818cf8' }}>
              {status?.ingestion_endpoint || 'http://localhost:8000/v1/events'}
            </div>
          </div>
        </div>

        {/* Latest Session Shortcut if available */}
        {status?.last_session_id && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '14px 18px',
              borderRadius: '8px',
              background: 'rgba(99, 102, 241, 0.08)',
              border: '1px solid rgba(99, 102, 241, 0.2)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Layers size={18} style={{ color: '#818cf8' }} />
              <div>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Most Recent Claude Code Session: </span>
                <strong style={{ fontSize: '13px', color: '#818cf8', fontFamily: 'JetBrains Mono' }}>
                  {status.last_session_id}
                </strong>
              </div>
            </div>
            <button
              className="btn-primary"
              onClick={() => onSelectSession(status.last_session_id!)}
              style={{ padding: '6px 14px', fontSize: '12px' }}
            >
              Open Live DAG <ArrowRight size={13} />
            </button>
          </div>
        )}
      </div>

      {/* Guided Setup & Instructions */}
      <div className="glass-panel" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <h3 style={{ fontSize: '17px', fontWeight: 700, color: 'var(--text-primary)' }}>
          Guided Setup: How to Use Claude Code with AgentDAC
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
          {/* Step 1 */}
          <div style={{ padding: '18px', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <span style={{ width: '24px', height: '24px', borderRadius: '50%', background: '#6366f1', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: 700 }}>1</span>
              <strong style={{ fontSize: '14px', color: 'var(--text-primary)' }}>Install or Verify CLI</strong>
            </div>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Make sure Claude Code is installed on your machine. Test with <code style={{ color: '#818cf8' }}>claude --version</code> in your terminal.
            </p>
          </div>

          {/* Step 2 */}
          <div style={{ padding: '18px', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <span style={{ width: '24px', height: '24px', borderRadius: '50%', background: '#6366f1', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: 700 }}>2</span>
              <strong style={{ fontSize: '14px', color: 'var(--text-primary)' }}>Configure Hooks</strong>
            </div>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Click <strong>Enable & Auto-Configure</strong> above. AgentDAC safely registers hooks for PreToolUse, PostToolUse, and Stop in <code style={{ color: '#818cf8' }}>~/.claude/settings.json</code>.
            </p>
          </div>

          {/* Step 3 */}
          <div style={{ padding: '18px', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <span style={{ width: '24px', height: '24px', borderRadius: '50%', background: '#6366f1', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: 700 }}>3</span>
              <strong style={{ fontSize: '14px', color: 'var(--text-primary)' }}>Code & Observe Live</strong>
            </div>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Open your terminal, run <code style={{ color: '#818cf8' }}>claude</code>, and perform your usual coding tasks. Watch every tool execution appear live on your DAG!
            </p>
          </div>
        </div>

        {/* Manual Configuration Code Block */}
        <div style={{ marginTop: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>
              <FileCode size={16} /> Hook Configuration in ~/.claude/settings.json
            </div>
            <button className="btn-secondary" onClick={copyConfigSnippet} style={{ padding: '5px 10px', fontSize: '12px' }}>
              {copiedSnippet ? <Check size={13} style={{ color: '#34d399' }} /> : <Copy size={13} />}
              {copiedSnippet ? 'Copied!' : 'Copy Config'}
            </button>
          </div>
          <pre
            style={{
              padding: '16px',
              borderRadius: '8px',
              background: 'rgba(10, 15, 29, 0.9)',
              border: '1px solid var(--border-subtle)',
              fontSize: '12px',
              color: '#cbd5e1',
              overflowX: 'auto',
            }}
          >
            {`{
  "hooks": {
    "SessionStart": [{ "matcher": "", "hooks": [{ "type": "command", "command": "python \\"${status?.hook_script_path || '.../hook.py'}\\"" }] }],
    "UserPromptSubmit": [{ "matcher": "", "hooks": [{ "type": "command", "command": "python \\"${status?.hook_script_path || '.../hook.py'}\\"" }] }],
    "PreToolUse": [{ "matcher": "", "hooks": [{ "type": "command", "command": "python \\"${status?.hook_script_path || '.../hook.py'}\\"" }] }],
    "PostToolUse": [{ "matcher": "", "hooks": [{ "type": "command", "command": "python \\"${status?.hook_script_path || '.../hook.py'}\\"" }] }],
    "Notification": [{ "matcher": "", "hooks": [{ "type": "command", "command": "python \\"${status?.hook_script_path || '.../hook.py'}\\"" }] }],
    "Stop": [{ "matcher": "", "hooks": [{ "type": "command", "command": "python \\"${status?.hook_script_path || '.../hook.py'}\\"" }] }]
  }
}`}
          </pre>
        </div>
      </div>

      {/* Security & Privacy Notice */}
      <div
        className="glass-panel"
        style={{
          padding: '20px 24px',
          borderLeft: '4px solid #6366f1',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '16px',
        }}
      >
        <Shield size={24} style={{ color: '#818cf8', flexShrink: 0, marginTop: '2px' }} />
        <div>
          <h4 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
            Production Privacy & Fail-Open Guarantee
          </h4>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            The integration operates entirely on <strong>observable lifecycle events</strong> (tool arguments, durations, and outputs). Private chain-of-thought is never accessed or requested. Sensitive tokens, passwords, and API keys are recursively redacted by the AgentDAC Sanitizer before transmission. Telemetry delivery is strictly fail-open: any network blip or backend downtime will never fail, delay, or disrupt your terminal Claude Code session.
          </p>
        </div>
      </div>
    </div>
  );
};
export default IntegrationsPage;
