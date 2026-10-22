import React from 'react';
import { OverviewAnalytics } from '../types/graph';
import { Activity, CheckCircle2, DollarSign, Gauge, TriangleAlert, Zap } from 'lucide-react';

interface Props {
  analytics: OverviewAnalytics | null;
}

export const StatsCards: React.FC<Props> = ({ analytics }) => {
  const stats = [
    {
      title: 'Total Sessions',
      value: analytics ? analytics.total_sessions.toLocaleString() : '—',
      icon: Activity,
      color: 'text-indigo-400',
      bg: 'rgba(99, 102, 241, 0.1)',
      border: 'rgba(99, 102, 241, 0.2)',
    },
    {
      title: 'Success rate',
      value: analytics ? `${(analytics.success_rate * 100).toFixed(1)}%` : '—',
      icon: CheckCircle2,
      color: 'text-emerald-400',
      bg: 'rgba(16, 185, 129, 0.1)',
      border: 'rgba(16, 185, 129, 0.2)',
    },
    {
      title: 'Tokens processed',
      value: analytics ? analytics.total_tokens.toLocaleString() : '—',
      icon: Zap,
      color: 'text-amber-400',
      bg: 'rgba(245, 158, 11, 0.1)',
      border: 'rgba(245, 158, 11, 0.2)',
    },
    {
      title: 'Spend',
      value: analytics ? `$${analytics.total_cost_usd.toFixed(4)}` : '$0.00',
      icon: DollarSign,
      color: 'text-cyan-400',
      bg: 'rgba(6, 182, 212, 0.1)',
      border: 'rgba(6, 182, 212, 0.2)',
    },
    {
      title: 'Error rate',
      value: analytics ? `${(analytics.error_rate * 100).toFixed(1)}%` : '—',
      icon: TriangleAlert,
      color: 'text-rose-400',
      bg: 'rgba(244, 63, 94, 0.1)',
      border: 'rgba(244, 63, 94, 0.2)',
    },
    {
      title: 'Avg latency',
      value: analytics ? `${analytics.avg_session_duration_s.toFixed(2)}s` : '—',
      icon: Gauge,
      color: 'text-purple-400',
      bg: 'rgba(168, 85, 247, 0.1)',
      border: 'rgba(168, 85, 247, 0.2)',
    },
  ];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '24px' }}>
      {stats.map((s, idx) => {
        const Icon = s.icon;
        return (
          <div
            key={idx}
            className="glass-panel"
            style={{
              padding: '20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderLeft: `4px solid ${s.color.includes('indigo') ? '#6366f1' : s.color.includes('emerald') ? '#10b981' : s.color.includes('amber') ? '#f59e0b' : s.color.includes('rose') ? '#f43f5e' : s.color.includes('purple') ? '#a855f7' : '#06b6d4'}`,
            }}
          >
            <div>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 500, marginBottom: '6px' }}>
                {s.title}
              </p>
              <h3 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
                {s.value}
              </h3>
            </div>
            <div
              style={{
                width: '44px',
                height: '44px',
                borderRadius: '10px',
                background: s.bg,
                border: `1px solid ${s.border}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Icon size={22} className={s.color} />
            </div>
          </div>
        );
      })}
    </div>
  );
};
