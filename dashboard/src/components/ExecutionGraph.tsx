import React, { useState, useMemo } from 'react';
import { GraphEdge, GraphNode } from '../types/graph';
import { Bot, Wrench, Sparkles, Terminal, AlertCircle, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';

interface Props {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string) => void;
}

export const ExecutionGraph: React.FC<Props> = ({
  nodes,
  edges,
  selectedNodeId,
  onSelectNode,
}) => {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Calculate hierarchical layout levels using topological tree depth
  const layoutNodes = useMemo(() => {
    if (nodes.length === 0) return [];

    const depthMap: Record<string, number> = {};
    const childrenMap: Record<string, string[]> = {};

    edges.forEach((e) => {
      if (!childrenMap[e.source]) childrenMap[e.source] = [];
      childrenMap[e.source].push(e.target);
    });

    const rootNodes = nodes.filter((n) => !edges.some((e) => e.target === n.id));
    const queue: { id: string; depth: number }[] = rootNodes.map((n) => ({ id: n.id, depth: 0 }));

    while (queue.length > 0) {
      const item = queue.shift()!;
      depthMap[item.id] = Math.max(depthMap[item.id] || 0, item.depth);

      const children = childrenMap[item.id] || [];
      children.forEach((childId) => {
        queue.push({ id: childId, depth: item.depth + 1 });
      });
    }

    // Group nodes by depth
    const levels: Record<number, GraphNode[]> = {};
    nodes.forEach((n) => {
      const d = depthMap[n.id] || 0;
      if (!levels[d]) levels[d] = [];
      levels[d].push(n);
    });

    const positioned: (GraphNode & { x: number; y: number })[] = [];
    const LEVEL_HEIGHT = 140;
    const NODE_WIDTH = 260;
    const HORIZONTAL_GAP = 40;

    Object.entries(levels).forEach(([depthStr, levelNodes]) => {
      const depth = parseInt(depthStr, 10);
      const totalWidth = levelNodes.length * NODE_WIDTH + (levelNodes.length - 1) * HORIZONTAL_GAP;
      const startX = -totalWidth / 2 + NODE_WIDTH / 2;

      levelNodes.forEach((node, idx) => {
        positioned.push({
          ...node,
          x: startX + idx * (NODE_WIDTH + HORIZONTAL_GAP),
          y: depth * LEVEL_HEIGHT + 60,
        });
      });
    });

    return positioned;
  }, [nodes, edges]);

  const getNodeIcon = (type: string, isError: boolean) => {
    if (isError) return <AlertCircle size={16} className="text-rose-400" />;
    switch (type.toLowerCase()) {
      case 'session':
        return <Bot size={16} style={{ color: '#a855f7' }} />;
      case 'agent':
        return <Bot size={16} style={{ color: '#6366f1' }} />;
      case 'llm':
        return <Sparkles size={16} style={{ color: '#f59e0b' }} />;
      case 'tool':
        return <Wrench size={16} style={{ color: '#10b981' }} />;
      default:
        return <Terminal size={16} style={{ color: '#06b6d4' }} />;
    }
  };

  const getNodeHeaderColor = (type: string, isError: boolean) => {
    if (isError) return 'linear-gradient(135deg, rgba(244,63,94,0.3) 0%, rgba(244,63,94,0.1) 100%)';
    switch (type.toLowerCase()) {
      case 'session':
        return 'linear-gradient(135deg, rgba(168,85,247,0.25) 0%, rgba(168,85,247,0.08) 100%)';
      case 'agent':
        return 'linear-gradient(135deg, rgba(99,102,241,0.25) 0%, rgba(99,102,241,0.08) 100%)';
      case 'llm':
        return 'linear-gradient(135deg, rgba(245,158,11,0.25) 0%, rgba(245,158,11,0.08) 100%)';
      case 'tool':
        return 'linear-gradient(135deg, rgba(16,185,129,0.25) 0%, rgba(16,185,129,0.08) 100%)';
      default:
        return 'linear-gradient(135deg, rgba(6,182,212,0.25) 0%, rgba(6,182,212,0.08) 100%)';
    }
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
  };

  const handleMouseUp = () => setIsDragging(false);

  return (
    <div
      className="glass-panel"
      style={{
        position: 'relative',
        height: '560px',
        overflow: 'hidden',
        cursor: isDragging ? 'grabbing' : 'grab',
        background: 'radial-gradient(ellipse at center, rgba(30, 41, 59, 0.4) 0%, rgba(9, 13, 22, 0.95) 100%)',
      }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {nodes.length === 0 && (
        <div className="graph-empty">
          <Terminal size={28} />
          <strong>No execution nodes</strong>
          <span>This session has no trace events yet.</span>
        </div>
      )}
      {/* Controls Overlay */}
      <div
        style={{
          position: 'absolute',
          top: '16px',
          right: '16px',
          zIndex: 10,
          display: 'flex',
          gap: '8px',
          background: 'rgba(15, 23, 42, 0.8)',
          backdropFilter: 'blur(8px)',
          padding: '6px',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <button
          className="btn-secondary"
          style={{ padding: '6px' }}
          onClick={() => setZoom((z) => Math.min(z + 0.15, 2))}
          title="Zoom In"
        >
          <ZoomIn size={16} />
        </button>
        <button
          className="btn-secondary"
          style={{ padding: '6px' }}
          onClick={() => setZoom((z) => Math.max(z - 0.15, 0.4))}
          title="Zoom Out"
        >
          <ZoomOut size={16} />
        </button>
        <button
          className="btn-secondary"
          style={{ padding: '6px' }}
          onClick={() => {
            setZoom(1);
            setPan({ x: 0, y: 0 });
          }}
          title="Reset View"
        >
          <Maximize2 size={16} />
        </button>
      </div>

      {/* SVG Canvas for Connectors and Positioned Nodes */}
      <div
        style={{
          position: 'absolute',
          left: '50%',
          top: '60px',
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          transformOrigin: 'top center',
          transition: isDragging ? 'none' : 'transform 0.1s ease',
        }}
      >
        {/* SVG Edges */}
        <svg
          style={{
            position: 'absolute',
            left: '-1000px',
            top: '-1000px',
            width: '2000px',
            height: '2000px',
            pointerEvents: 'none',
          }}
        >
          <defs>
            <marker
              id="arrow"
              viewBox="0 0 10 10"
              refX="6"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#6366f1" opacity="0.8" />
            </marker>
          </defs>
          {edges.map((edge) => {
            const src = layoutNodes.find((n) => n.id === edge.source);
            const tgt = layoutNodes.find((n) => n.id === edge.target);
            if (!src || !tgt) return null;

            const startX = src.x + 1000;
            const startY = src.y + 70 + 1000;
            const endX = tgt.x + 1000;
            const endY = tgt.y + 1000;

            const deltaY = endY - startY;
            const path = `M ${startX} ${startY} C ${startX} ${startY + deltaY / 2}, ${endX} ${endY - deltaY / 2}, ${endX} ${endY}`;
            const midX = (startX + endX) / 2;
            const midY = (startY + endY) / 2;

            return (
              <g key={edge.id}>
                <path
                  d={path}
                  fill="none"
                  stroke="#6366f1"
                  strokeWidth="2"
                  strokeDasharray="4 2"
                  opacity="0.6"
                  markerEnd="url(#arrow)"
                />
                {edge.label && (
                  <>
                    <rect
                      x={midX - 44}
                      y={midY - 10}
                      width={88}
                      height={18}
                      rx={4}
                      fill="rgba(15,23,42,0.85)"
                      stroke="rgba(99,102,241,0.3)"
                      strokeWidth={1}
                    />
                    <text
                      x={midX}
                      y={midY + 4}
                      textAnchor="middle"
                      fontSize={9}
                      fontWeight={600}
                      fill="#818cf8"
                      fontFamily="system-ui"
                      letterSpacing="0.04em"
                    >
                      {edge.label}
                    </text>
                  </>
                )}
              </g>
            );
          })}
        </svg>

        {/* Nodes */}
        {layoutNodes.map((node) => {
          const isSelected = node.id === selectedNodeId;
          const isError = node.status.toUpperCase() === 'ERROR';

          return (
            <div
              key={node.id}
              onClick={(e) => {
                e.stopPropagation();
                onSelectNode(node.id);
              }}
              style={{
                position: 'absolute',
                left: `${node.x - 120}px`,
                top: `${node.y}px`,
                width: '240px',
                background: 'rgba(15, 23, 42, 0.9)',
                border: isSelected
                  ? '2px solid #818cf8'
                  : isError
                  ? '1px solid #f43f5e'
                  : '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '10px',
                boxShadow: isSelected
                  ? '0 0 20px rgba(99, 102, 241, 0.4)'
                  : '0 8px 16px rgba(0,0,0,0.4)',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  padding: '8px 12px',
                  background: getNodeHeaderColor(node.type, isError),
                  borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  {getNodeIcon(node.type, isError)}
                  <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)' }}>
                    {node.type}
                  </span>
                </div>
                <span
                  style={{
                    fontSize: '10px',
                    fontWeight: 600,
                    padding: '2px 6px',
                    borderRadius: '10px',
                    background: isError ? 'rgba(244, 63, 94, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                    color: isError ? '#fb7185' : '#34d399',
                  }}
                >
                  {node.status}
                </span>
              </div>

              <div style={{ padding: '10px 12px' }}>
                <p
                  style={{
                    fontSize: '13px',
                    fontWeight: 600,
                    color: 'var(--text-primary)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    marginBottom: '4px',
                  }}
                  title={node.label}
                >
                  {node.label}
                </p>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-secondary)' }}>
                  <span>{node.duration_ms != null ? `${node.duration_ms}ms` : '—'}</span>
                  {node.model && <span style={{ color: '#f59e0b' }}>{node.model}</span>}
                  {node.cost_usd != null && <span style={{ color: '#06b6d4' }}>${node.cost_usd.toFixed(4)}</span>}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
