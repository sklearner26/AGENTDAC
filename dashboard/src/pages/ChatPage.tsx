import React, { useEffect, useRef, useState } from 'react';
import { chatWithTimeline, fetchSessions } from '../api/client';
import { SessionSummary } from '../types/graph';
import { Bot, Send, Cpu, MessageSquare, Loader2, RefreshCw, Sparkles, ChevronDown } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  context_spans?: number;
  session_id?: string | null;
  timestamp: Date;
}

const EXAMPLE_QUESTIONS = [
  'What tools were called and in what order?',
  'Which agent took the longest to complete?',
  'Were there any errors in this session?',
  'How many LLM tokens were consumed total?',
  'Summarize what this agent session accomplished.',
  'What was the reasoning chain from start to finish?',
];

export const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content:
        'Hello! I\'m the AgentDAC observability assistant. I have access to the complete execution timeline of your agent sessions — including every span, tool call, LLM invocation, token count, and error.\n\nAsk me anything about your agent\'s execution. I answer strictly from the recorded timeline data.',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [selectedSession, setSelectedSession] = useState<string>('');
  const [sessionLoading, setSessionLoading] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    setSessionLoading(true);
    fetchSessions()
      .then((s) => {
        setSessions(s);
        if (s.length > 0) setSelectedSession(s[0].id);
      })
      .catch(() => {})
      .finally(() => setSessionLoading(false));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (question?: string) => {
    const text = (question || input).trim();
    if (!text || loading) return;

    const userMessage: Message = { role: 'user', content: text, timestamp: new Date() };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const resp = await chatWithTimeline(text, selectedSession || undefined);
      const assistantMessage: Message = {
        role: 'assistant',
        content: resp.answer,
        context_spans: resp.context_spans,
        session_id: resp.session_id,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            'Sorry, the chat request failed. Make sure AGENTDAC_CHAT_API_KEY (or OPENAI_API_KEY) is set in the backend environment and the server is running.',
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatTime = (d: Date) =>
    d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 180px)', gap: '16px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Sparkles size={22} style={{ color: '#818cf8' }} />
            Timeline Intelligence
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
            Ask natural-language questions about any agent session. Answers are grounded in the actual execution timeline.
          </p>
        </div>

        {/* Session Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 600 }}>Session:</span>
          {sessionLoading ? (
            <Loader2 size={14} style={{ color: '#818cf8', animation: 'spin 1s linear infinite' }} />
          ) : (
            <div style={{ position: 'relative' }}>
              <select
                id="chat-session-selector"
                value={selectedSession}
                onChange={(e) => setSelectedSession(e.target.value)}
                style={{
                  background: 'rgba(15, 23, 42, 0.8)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '8px',
                  color: 'var(--text-primary)',
                  fontSize: '12px',
                  padding: '6px 28px 6px 10px',
                  appearance: 'none',
                  cursor: 'pointer',
                  minWidth: '220px',
                  maxWidth: '340px',
                }}
              >
                <option value="">Latest session (auto)</option>
                {sessions.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.agent_id} · {s.id.slice(0, 12)}… · {s.status}
                  </option>
                ))}
              </select>
              <ChevronDown size={12} style={{ position: 'absolute', right: '8px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)', pointerEvents: 'none' }} />
            </div>
          )}
          <button
            id="chat-refresh-sessions"
            className="btn-secondary"
            style={{ padding: '6px 8px' }}
            onClick={() => {
              setSessionLoading(true);
              fetchSessions().then((s) => { setSessions(s); if (s.length > 0 && !selectedSession) setSelectedSession(s[0].id); }).finally(() => setSessionLoading(false));
            }}
          >
            <RefreshCw size={13} />
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 220px', gap: '16px', flex: 1, minHeight: 0 }}>
        {/* Chat Panel */}
        <div
          className="glass-panel"
          style={{ display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'hidden' }}
        >
          {/* Messages */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {messages.map((msg, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  gap: '10px',
                  flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                  alignItems: 'flex-start',
                }}
              >
                {/* Avatar */}
                <div
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    flexShrink: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: msg.role === 'user'
                      ? 'linear-gradient(135deg, #6366f1, #a855f7)'
                      : 'linear-gradient(135deg, #0f172a, #1e293b)',
                    border: msg.role === 'assistant' ? '1px solid rgba(99,102,241,0.3)' : 'none',
                  }}
                >
                  {msg.role === 'user' ? (
                    <MessageSquare size={15} style={{ color: 'white' }} />
                  ) : (
                    <Bot size={15} style={{ color: '#818cf8' }} />
                  )}
                </div>

                {/* Bubble */}
                <div style={{ maxWidth: '78%' }}>
                  <div
                    style={{
                      padding: '12px 16px',
                      borderRadius: msg.role === 'user' ? '14px 4px 14px 14px' : '4px 14px 14px 14px',
                      background: msg.role === 'user'
                        ? 'linear-gradient(135deg, rgba(99,102,241,0.25), rgba(168,85,247,0.15))'
                        : 'rgba(15, 23, 42, 0.7)',
                      border: `1px solid ${msg.role === 'user' ? 'rgba(99,102,241,0.3)' : 'var(--border-subtle)'}`,
                      fontSize: '13.5px',
                      lineHeight: '1.6',
                      color: 'var(--text-primary)',
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {msg.content}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px', fontSize: '11px', color: 'var(--text-muted)', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                    <span>{formatTime(msg.timestamp)}</span>
                    {msg.context_spans != null && (
                      <span style={{ display: 'flex', alignItems: 'center', gap: '3px', color: '#818cf8' }}>
                        <Cpu size={10} /> {msg.context_spans} spans
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {loading && (
              <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                <div style={{ width: '32px', height: '32px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'linear-gradient(135deg, #0f172a, #1e293b)', border: '1px solid rgba(99,102,241,0.3)' }}>
                  <Bot size={15} style={{ color: '#818cf8' }} />
                </div>
                <div style={{ padding: '14px 16px', borderRadius: '4px 14px 14px 14px', background: 'rgba(15, 23, 42, 0.7)', border: '1px solid var(--border-subtle)', display: 'flex', gap: '6px', alignItems: 'center' }}>
                  <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#818cf8', animation: 'pulse 1.5s ease-in-out infinite' }} />
                  <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#818cf8', animation: 'pulse 1.5s ease-in-out 0.3s infinite' }} />
                  <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#818cf8', animation: 'pulse 1.5s ease-in-out 0.6s infinite' }} />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div
            style={{
              padding: '16px',
              borderTop: '1px solid var(--border-subtle)',
              display: 'flex',
              gap: '10px',
              alignItems: 'flex-end',
            }}
          >
            <textarea
              id="chat-input"
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about tool calls, token usage, agent reasoning, errors... (Enter to send)"
              rows={2}
              style={{
                flex: 1,
                background: 'rgba(15, 23, 42, 0.6)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '10px',
                color: 'var(--text-primary)',
                fontSize: '13px',
                padding: '10px 14px',
                resize: 'none',
                fontFamily: 'inherit',
                lineHeight: '1.5',
              }}
            />
            <button
              id="chat-send-btn"
              onClick={() => handleSend()}
              disabled={!input.trim() || loading}
              style={{
                padding: '10px 16px',
                borderRadius: '10px',
                background: input.trim() && !loading ? 'linear-gradient(135deg, #6366f1, #a855f7)' : 'rgba(99,102,241,0.2)',
                border: 'none',
                cursor: input.trim() && !loading ? 'pointer' : 'not-allowed',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '13px',
                fontWeight: 600,
                color: 'white',
                transition: 'all 0.15s ease',
                minHeight: '42px',
              }}
            >
              {loading ? <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> : <Send size={16} />}
            </button>
          </div>
        </div>

        {/* Suggested Questions sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <p style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: '4px' }}>
            Example Questions
          </p>
          {EXAMPLE_QUESTIONS.map((q, i) => (
            <button
              key={i}
              id={`chat-example-${i}`}
              onClick={() => handleSend(q)}
              disabled={loading}
              style={{
                textAlign: 'left',
                padding: '9px 12px',
                borderRadius: '8px',
                background: 'rgba(15, 23, 42, 0.6)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-secondary)',
                fontSize: '12px',
                lineHeight: '1.4',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'rgba(99,102,241,0.4)')}
              onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-subtle)')}
            >
              {q}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
