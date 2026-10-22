-- AOG PostgreSQL Schema Initialization
-- This script creates the initial database schema for the Agent Observability Graph.

-- Agents table
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    framework TEXT,
    model TEXT,
    version TEXT,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(id),
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    status TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Spans table
CREATE TABLE IF NOT EXISTS spans (
    id TEXT PRIMARY KEY,
    trace_id TEXT NOT NULL,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    parent_span_id TEXT,
    agent_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    name TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    status TEXT NOT NULL,
    input JSONB,
    output JSONB,
    attributes JSONB NOT NULL DEFAULT '{}',
    tokens_in INTEGER,
    tokens_out INTEGER,
    model TEXT,
    provider TEXT,
    cost_usd DOUBLE PRECISION,
    error JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Events table
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    schema_version TEXT NOT NULL,
    trace_id TEXT NOT NULL,
    span_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    name TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_sessions_agent_time
    ON sessions(agent_id, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_spans_trace
    ON spans(trace_id);

CREATE INDEX IF NOT EXISTS idx_spans_session
    ON spans(session_id);

CREATE INDEX IF NOT EXISTS idx_spans_parent
    ON spans(parent_span_id);

CREATE INDEX IF NOT EXISTS idx_spans_type
    ON spans(event_type);

CREATE INDEX IF NOT EXISTS idx_events_trace
    ON events(trace_id);

CREATE INDEX IF NOT EXISTS idx_events_session_time
    ON events(session_id, timestamp);