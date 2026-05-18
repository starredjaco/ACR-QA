/**
 * Visual Call Graph for a finding (v5.0.0 Phase A.1).
 *
 * Pure-SVG layered layout (no external graph library).
 * Layout: entry-points → intermediates → target → callees of target.
 * Colors: green=reachable, gray=dead, amber=entry-point, red=target.
 */

import { useEffect, useMemo, useState } from "react";
import { authHeader } from "@/lib/auth";

interface CGNode {
  id: string;
  name: string;
  reachable: boolean;
  is_target: boolean;
  is_entry: boolean;
}

interface CGEdge {
  source: string;
  target: string;
}

interface CallGraphResponse {
  file_path: string;
  target: string | null;
  entry_points?: string[];
  nodes: CGNode[];
  edges: CGEdge[];
  unsupported_language?: boolean;
  file_missing?: boolean;
}

interface Props {
  findingId: number;
  onNodeClick?: (functionName: string) => void;
  className?: string;
}

const NODE_W = 140;
const NODE_H = 32;
const COL_GAP = 60;
const ROW_GAP = 18;
const PAD = 24;

interface LaidOutNode extends CGNode {
  x: number;
  y: number;
  column: number;
}

function layout(nodes: CGNode[], edges: CGEdge[]): LaidOutNode[] {
  // Column 0: entry points
  // Column 1: nodes called by entry points (but not entry / target)
  // Column 2: target
  // Column 3: nodes called by target
  // Column "other": everything else (placed in column 1 as orphans)
  const calledBy = new Map<string, Set<string>>();
  const callers = new Map<string, Set<string>>();
  for (const e of edges) {
    if (!calledBy.has(e.source)) calledBy.set(e.source, new Set());
    calledBy.get(e.source)!.add(e.target);
    if (!callers.has(e.target)) callers.set(e.target, new Set());
    callers.get(e.target)!.add(e.source);
  }

  const target = nodes.find((n) => n.is_target);
  const targetName = target?.id;
  const cols: Record<number, CGNode[]> = { 0: [], 1: [], 2: [], 3: [] };

  for (const n of nodes) {
    if (n.is_entry) {
      cols[0].push(n);
    } else if (n.is_target) {
      cols[2].push(n);
    } else if (targetName && calledBy.get(targetName)?.has(n.id)) {
      cols[3].push(n);
    } else {
      cols[1].push(n);
    }
  }

  const out: LaidOutNode[] = [];
  for (const col of [0, 1, 2, 3]) {
    cols[col].forEach((n, i) => {
      out.push({
        ...n,
        column: col,
        x: PAD + col * (NODE_W + COL_GAP),
        y: PAD + i * (NODE_H + ROW_GAP),
      });
    });
  }
  return out;
}

function nodeFill(n: CGNode): string {
  if (n.is_target) return "rgb(239 68 68 / 0.18)"; // red-500 @ 18%
  if (n.is_entry) return "rgb(245 158 11 / 0.18)"; // amber-500
  if (n.reachable) return "rgb(34 197 94 / 0.18)"; // green-500
  return "rgb(100 116 139 / 0.18)"; // slate
}

function nodeStroke(n: CGNode): string {
  if (n.is_target) return "rgb(239 68 68)";
  if (n.is_entry) return "rgb(245 158 11)";
  if (n.reachable) return "rgb(34 197 94)";
  return "rgb(100 116 139)";
}

export function CallGraph({ findingId, onNodeClick, className }: Props) {
  const [data, setData] = useState<CallGraphResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    fetch(`/v1/findings/${findingId}/call-graph`, { headers: authHeader() })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d: CallGraphResponse) => {
        if (alive) setData(d);
      })
      .catch((e) => {
        if (alive) setError(e instanceof Error ? e.message : "fetch failed");
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [findingId]);

  const laidOut = useMemo(() => (data ? layout(data.nodes, data.edges) : []), [data]);
  const byId = useMemo(() => new Map(laidOut.map((n) => [n.id, n])), [laidOut]);

  const width = useMemo(() => {
    if (laidOut.length === 0) return 600;
    const maxCol = Math.max(...laidOut.map((n) => n.column));
    return PAD * 2 + (maxCol + 1) * NODE_W + maxCol * COL_GAP;
  }, [laidOut]);

  const height = useMemo(() => {
    if (laidOut.length === 0) return 200;
    const perCol: Record<number, number> = {};
    for (const n of laidOut) perCol[n.column] = (perCol[n.column] ?? 0) + 1;
    const rows = Math.max(...Object.values(perCol));
    return PAD * 2 + rows * NODE_H + (rows - 1) * ROW_GAP;
  }, [laidOut]);

  if (loading) {
    return (
      <div data-testid="callgraph-loading" className={`text-xs text-muted-foreground ${className ?? ""}`}>
        Loading call graph…
      </div>
    );
  }
  if (error) {
    return (
      <div data-testid="callgraph-error" role="alert" className={`text-xs text-destructive ${className ?? ""}`}>
        {error}
      </div>
    );
  }
  if (!data) return null;
  if (data.unsupported_language) {
    return (
      <div data-testid="callgraph-unsupported" className={`text-xs text-muted-foreground ${className ?? ""}`}>
        Call graph is currently Python-only. ({data.file_path})
      </div>
    );
  }
  if (data.file_missing || data.nodes.length === 0) {
    return (
      <div data-testid="callgraph-empty" className={`text-xs text-muted-foreground ${className ?? ""}`}>
        No call graph available for this finding.
      </div>
    );
  }

  return (
    <div data-testid="callgraph" className={`overflow-auto rounded-md border bg-card p-2 ${className ?? ""}`}>
      <svg
        role="img"
        aria-label={`Call graph for ${data.file_path}`}
        width={width}
        height={height}
        style={{ display: "block" }}
      >
        <defs>
          <marker
            id="arrow"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="rgb(100 116 139)" />
          </marker>
        </defs>
        {data.edges.map((e, i) => {
          const s = byId.get(e.source);
          const t = byId.get(e.target);
          if (!s || !t) return null;
          const x1 = s.x + NODE_W;
          const y1 = s.y + NODE_H / 2;
          const x2 = t.x;
          const y2 = t.y + NODE_H / 2;
          return (
            <line
              key={i}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke="rgb(100 116 139)"
              strokeWidth={1}
              markerEnd="url(#arrow)"
              data-testid={`edge-${e.source}-${e.target}`}
            />
          );
        })}
        {laidOut.map((n) => (
          <g
            key={n.id}
            transform={`translate(${n.x}, ${n.y})`}
            data-testid={`node-${n.id}`}
            data-target={n.is_target ? "1" : "0"}
            data-entry={n.is_entry ? "1" : "0"}
            data-reachable={n.reachable ? "1" : "0"}
            style={{ cursor: onNodeClick ? "pointer" : "default" }}
            onClick={() => onNodeClick?.(n.id)}
            tabIndex={onNodeClick ? 0 : -1}
            onKeyDown={(e) => {
              if (onNodeClick && (e.key === "Enter" || e.key === " ")) onNodeClick(n.id);
            }}
          >
            <rect
              width={NODE_W}
              height={NODE_H}
              rx={6}
              fill={nodeFill(n)}
              stroke={nodeStroke(n)}
              strokeWidth={n.is_target ? 2 : 1}
            />
            <text
              x={NODE_W / 2}
              y={NODE_H / 2 + 4}
              textAnchor="middle"
              fontSize={12}
              fontFamily="monospace"
              fill="currentColor"
            >
              {n.name.length > 18 ? n.name.slice(0, 17) + "…" : n.name}
            </text>
          </g>
        ))}
      </svg>
      <p className="mt-2 text-[10px] text-muted-foreground">
        <span className="mr-3">
          <span
            className="inline-block h-2 w-2 rounded-sm align-middle"
            style={{ backgroundColor: "rgb(239 68 68)" }}
          />{" "}
          target
        </span>
        <span className="mr-3">
          <span
            className="inline-block h-2 w-2 rounded-sm align-middle"
            style={{ backgroundColor: "rgb(245 158 11)" }}
          />{" "}
          entry
        </span>
        <span className="mr-3">
          <span
            className="inline-block h-2 w-2 rounded-sm align-middle"
            style={{ backgroundColor: "rgb(34 197 94)" }}
          />{" "}
          reachable
        </span>
        <span>
          <span
            className="inline-block h-2 w-2 rounded-sm align-middle"
            style={{ backgroundColor: "rgb(100 116 139)" }}
          />{" "}
          dead
        </span>
      </p>
    </div>
  );
}
