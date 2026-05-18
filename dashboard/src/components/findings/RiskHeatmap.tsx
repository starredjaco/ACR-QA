/**
 * Risk Heatmap of File Tree (v5.0.0 Phase A.1 — MVP).
 *
 * Renders a collapsible folder tree colored by HIGH-density risk score.
 * Click a file/folder → bubble onPathSelect(path) so a parent can filter findings.
 */

import { useEffect, useMemo, useState } from "react";
import { authHeader } from "@/lib/auth";

interface HeatmapFile {
  file_path: string;
  high: number;
  medium: number;
  low: number;
  total: number;
  risk_score: number;
  top_rules: Array<{ rule_id: string; count: number }>;
}

interface HeatmapResponse {
  run_id: number;
  files: HeatmapFile[];
  max_high: number;
  max_total: number;
}

interface TreeNode {
  name: string;
  path: string;
  isFile: boolean;
  children: TreeNode[];
  file?: HeatmapFile;
  /** Aggregated risk for folders */
  risk: number;
  high: number;
  total: number;
}

interface Props {
  runId: number;
  onPathSelect?: (path: string) => void;
  className?: string;
}

function buildTree(files: HeatmapFile[]): TreeNode {
  const root: TreeNode = { name: "/", path: "", isFile: false, children: [], risk: 0, high: 0, total: 0 };

  for (const f of files) {
    const parts = f.file_path.split("/").filter(Boolean);
    let cur = root;
    for (let i = 0; i < parts.length; i++) {
      const name = parts[i];
      const isLeaf = i === parts.length - 1;
      const path = parts.slice(0, i + 1).join("/");
      let child = cur.children.find((c) => c.name === name);
      if (!child) {
        child = {
          name,
          path,
          isFile: isLeaf,
          children: [],
          file: isLeaf ? f : undefined,
          risk: isLeaf ? f.risk_score : 0,
          high: isLeaf ? f.high : 0,
          total: isLeaf ? f.total : 0,
        };
        cur.children.push(child);
      }
      cur = child;
    }
  }

  // Aggregate folder risk/high/total from descendants
  function aggregate(n: TreeNode): { risk: number; high: number; total: number } {
    if (n.isFile) return { risk: n.risk, high: n.high, total: n.total };
    let high = 0;
    let total = 0;
    let risk = 0;
    for (const c of n.children) {
      const a = aggregate(c);
      high += a.high;
      total += a.total;
      risk = Math.max(risk, a.risk);
    }
    n.high = high;
    n.total = total;
    n.risk = risk;
    return { risk, high, total };
  }
  aggregate(root);

  // Sort: folders first, then by risk desc
  function sortRec(n: TreeNode) {
    n.children.sort((a, b) => {
      if (a.isFile !== b.isFile) return a.isFile ? 1 : -1;
      if (a.risk !== b.risk) return b.risk - a.risk;
      return a.name.localeCompare(b.name);
    });
    for (const c of n.children) sortRec(c);
  }
  sortRec(root);

  return root;
}

function riskColor(score: number): string {
  // 0 → green-50, 100 → red-700 — linear interpolate in HSL
  // Empty band stays neutral.
  if (score <= 0) return "rgba(100,116,139,0.06)";
  const hue = 140 - (score / 100) * 140; // 140 (green) → 0 (red)
  const lightness = 92 - (score / 100) * 50; // 92 → 42
  return `hsl(${hue} 70% ${lightness}%)`;
}

interface RowProps {
  node: TreeNode;
  depth: number;
  onPathSelect?: (path: string) => void;
  expanded: Set<string>;
  toggle: (path: string) => void;
}

function Row({ node, depth, onPathSelect, expanded, toggle }: RowProps) {
  const isOpen = expanded.has(node.path);
  const indent = depth * 14;
  const tooltipParts = node.file
    ? [`${node.high}H · ${node.file.medium}M · ${node.file.low}L`, ...node.file.top_rules.map((r) => `${r.rule_id} ×${r.count}`)]
    : [`${node.high} HIGH · ${node.total} total`];

  return (
    <>
      <div
        data-testid={`heatmap-row-${node.path || "root"}`}
        data-risk={node.risk}
        data-isfile={node.isFile ? "1" : "0"}
        role="treeitem"
        aria-expanded={!node.isFile ? isOpen : undefined}
        tabIndex={0}
        title={tooltipParts.join(" · ")}
        style={{ paddingLeft: 6 + indent, backgroundColor: riskColor(node.risk) }}
        className="group flex cursor-pointer items-center gap-2 border-b border-border/40 py-1 pr-2 text-xs hover:bg-accent/30"
        onClick={() => {
          if (!node.isFile) toggle(node.path);
          if (onPathSelect) onPathSelect(node.path);
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            if (!node.isFile) toggle(node.path);
            onPathSelect?.(node.path);
          }
        }}
      >
        {!node.isFile && (
          <span aria-hidden className="inline-block w-3 text-muted-foreground">
            {isOpen ? "▾" : "▸"}
          </span>
        )}
        {node.isFile && <span aria-hidden className="inline-block w-3" />}
        <span className="truncate font-mono">{node.name}</span>
        <span className="ml-auto inline-flex items-center gap-1 text-[10px] text-muted-foreground">
          {node.high > 0 && (
            <span data-testid="row-high" className="rounded bg-red-500/15 px-1 text-red-700">
              {node.high}H
            </span>
          )}
          <span data-testid="row-total" className="rounded bg-muted px-1">
            {node.total}
          </span>
        </span>
      </div>
      {!node.isFile && isOpen && node.children.map((c) => (
        <Row key={c.path} node={c} depth={depth + 1} onPathSelect={onPathSelect} expanded={expanded} toggle={toggle} />
      ))}
    </>
  );
}

export function RiskHeatmap({ runId, onPathSelect, className }: Props) {
  const [data, setData] = useState<HeatmapResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set([""]));

  useEffect(() => {
    let alive = true;
    setLoading(true);
    fetch(`/v1/runs/${runId}/heatmap`, { headers: authHeader() })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d: HeatmapResponse) => {
        if (!alive) return;
        setData(d);
        // auto-expand top-level folders that contain HIGH findings
        const tree = buildTree(d.files);
        const top = new Set<string>([""]);
        for (const c of tree.children) {
          if (!c.isFile && c.high > 0) top.add(c.path);
        }
        setExpanded(top);
      })
      .catch((e) => alive && setError(e instanceof Error ? e.message : "fetch failed"))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [runId]);

  const tree = useMemo(() => (data ? buildTree(data.files) : null), [data]);

  const toggle = (path: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });

  if (loading) {
    return (
      <div data-testid="heatmap-loading" className={`text-xs text-muted-foreground ${className ?? ""}`}>
        Building heatmap…
      </div>
    );
  }
  if (error) {
    return (
      <div data-testid="heatmap-error" role="alert" className={`text-xs text-destructive ${className ?? ""}`}>
        {error}
      </div>
    );
  }
  if (!tree || tree.children.length === 0) {
    return (
      <div data-testid="heatmap-empty" className={`text-xs text-muted-foreground ${className ?? ""}`}>
        No findings to display.
      </div>
    );
  }

  return (
    <nav
      data-testid="heatmap"
      role="tree"
      aria-label="Risk Heatmap"
      className={`overflow-y-auto rounded-md border bg-card ${className ?? ""}`}
    >
      {tree.children.map((c) => (
        <Row key={c.path} node={c} depth={0} onPathSelect={onPathSelect} expanded={expanded} toggle={toggle} />
      ))}
    </nav>
  );
}
