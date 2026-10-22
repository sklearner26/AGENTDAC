export type GraphNode = {
  id: string;
  type: string;
  label: string;
  status: string;
  started_at: string;
  ended_at?: string;
  duration_ms?: number;
  tokens_in?: number;
  tokens_out?: number;
  cost_usd?: number;
  model?: string;
  provider?: string;
  metadata?: Record<string, unknown>;
};

export type GraphEdge = {
  id: string;
  source: string;
  target: string;
  type?: string;
  label?: string;
  reason?: string;
};

export type SessionSummary = {
  id: string;
  agent_id: string;
  started_at: string;
  ended_at?: string;
  duration_s?: number;
  status: string;
  event_count: number;
  total_tokens: number;
  cost_usd?: number;
  metadata?: Record<string, unknown>;
};

export type TraceGraphResponse = {
  session: SessionSummary | null;
  nodes: GraphNode[];
  edges: GraphEdge[];
};

export type OverviewAnalytics = {
  total_sessions: number;
  success_rate: number;
  error_rate: number;
  total_tokens: number;
  total_cost_usd: number;
  avg_session_duration_s: number;
};

export type SessionListResponse = {
  sessions: SessionSummary[];
  total: number;
};

export type ToolUsageStat = {
  name: string;
  count: number;
  avg_duration_ms: number;
  p95_duration_ms: number;
  error_count: number;
};

export type ModelUsageStat = {
  model: string;
  calls: number;
  tokens_in: number;
  tokens_out: number;
  cost_usd: number;
};

export type ErrorStat = {
  error_type: string;
  message: string;
  count: number;
  last_occurred: string;
};

export type SpanDetail = {
  id: string;
  trace_id: string;
  session_id: string;
  parent_span_id?: string;
  agent_id: string;
  event_type: string;
  name: string;
  started_at: string;
  ended_at?: string;
  duration_ms?: number;
  status: string;
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
  attributes?: Record<string, unknown>;
  tokens_in?: number;
  tokens_out?: number;
  model?: string;
  provider?: string;
  cost_usd?: number;
  error?: {
    type: string;
    message: string;
    stacktrace?: string;
    retryable?: boolean;
  };
};

export type ClaudeCodeIntegrationStatus = {
  integration: string;
  name: string;
  status: 'connected' | 'running' | 'setup_required' | 'not_connected' | 'paused' | 'error';
  cli_installed: boolean;
  cli_version: string | null;
  hooks_configured: boolean;
  paused: boolean;
  hook_script_path: string;
  hook_script_exists: boolean;
  settings_path: string;
  settings_exists: boolean;
  observed_sessions_count: number;
  last_activity: string | null;
  last_session_id: string | null;
  ingestion_endpoint: string;
};
