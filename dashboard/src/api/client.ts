import {
  ErrorStat,
  ModelUsageStat,
  OverviewAnalytics,
  SessionSummary,
  SpanDetail,
  ToolUsageStat,
  TraceGraphResponse,
  ClaudeCodeIntegrationStatus,
} from '../types/graph';

const API_BASE = '/v1';

export async function fetchSessions(agentId?: string, status?: string): Promise<SessionSummary[]> {
  const params = new URLSearchParams();
  if (agentId) params.append('agent_id', agentId);
  if (status) params.append('status', status);
  
  const res = await fetch(`${API_BASE}/sessions?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch sessions: ${res.statusText}`);
  const data: { sessions?: SessionSummary[] } = await res.json();
  return data.sessions ?? [];
}

export async function fetchSession(sessionId: string): Promise<SessionSummary> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`);
  if (!res.ok) throw new Error(`Failed to fetch session: ${res.statusText}`);
  return res.json();
}

export async function fetchTraceGraph(sessionId: string): Promise<TraceGraphResponse> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/trace`);
  if (!res.ok) throw new Error(`Failed to fetch trace graph: ${res.statusText}`);
  return res.json();
}

export async function fetchSpan(spanId: string): Promise<SpanDetail> {
  const res = await fetch(`${API_BASE}/spans/${spanId}`);
  if (!res.ok) throw new Error(`Failed to fetch span: ${res.statusText}`);
  return res.json();
}

export async function fetchOverviewAnalytics(): Promise<OverviewAnalytics> {
  const res = await fetch(`${API_BASE}/analytics/overview`);
  if (!res.ok) throw new Error(`Failed to fetch overview analytics: ${res.statusText}`);
  return res.json();
}

export async function fetchToolAnalytics(): Promise<ToolUsageStat[]> {
  const res = await fetch(`${API_BASE}/analytics/tools`);
  if (!res.ok) throw new Error(`Failed to fetch tool analytics: ${res.statusText}`);
  return res.json();
}

export async function fetchModelAnalytics(): Promise<ModelUsageStat[]> {
  const res = await fetch(`${API_BASE}/analytics/models`);
  if (!res.ok) throw new Error(`Failed to fetch model analytics: ${res.statusText}`);
  return res.json();
}

export async function fetchErrorAnalytics(): Promise<ErrorStat[]> {
  const res = await fetch(`${API_BASE}/analytics/errors`);
  if (!res.ok) throw new Error(`Failed to fetch error analytics: ${res.statusText}`);
  return res.json();
}
export async function chatWithTimeline(question: string, sessionId?: string): Promise<{ answer: string; session_id: string | null; context_spans: number }> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, session_id: sessionId || null }),
  });
  if (!res.ok) throw new Error(`Chat failed: ${res.statusText}`);
  return res.json();
}

export async function fetchClaudeCodeStatus(): Promise<ClaudeCodeIntegrationStatus> {
  const res = await fetch(`${API_BASE}/integrations/claude-code/status`);
  if (!res.ok) throw new Error(`Failed to fetch Claude Code status: ${res.statusText}`);
  return res.json();
}

export async function configureClaudeCodeIntegration(): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/integrations/claude-code/configure`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`Configuration failed: ${res.statusText}`);
  return res.json();
}

export async function disconnectClaudeCodeIntegration(): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/integrations/claude-code/disconnect`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`Disconnect failed: ${res.statusText}`);
  return res.json();
}

export async function toggleClaudeCodePause(): Promise<{ paused: boolean }> {
  const res = await fetch(`${API_BASE}/integrations/claude-code/toggle-pause`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`Toggle pause failed: ${res.statusText}`);
  return res.json();
}

export async function sendClaudeCodeTestEvent(): Promise<{ success: boolean; session_id: string }> {
  const res = await fetch(`${API_BASE}/integrations/claude-code/test-event`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`Test event failed: ${res.statusText}`);
  return res.json();
}
