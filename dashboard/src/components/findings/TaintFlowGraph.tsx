import { ArrowRight } from "lucide-react";
import { type Finding } from "@/lib/api";

interface Props { finding: Finding; }

export function TaintFlowGraph({ finding }: Props) {
  if (!finding.taint_source && !finding.taint_path) {
    return <div className="text-sm text-muted-foreground italic">No taint data for this finding</div>;
  }

  const pathSteps: string[] = finding.taint_path
    ? JSON.parse(finding.taint_path)
    : [];

  return (
    <div className="space-y-3">
      <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Data Flow</div>
      <div className="flex flex-wrap items-center gap-2">
        {/* Source node */}
        <div className="rounded-lg border-2 border-red-300 bg-red-50 px-3 py-2 text-sm">
          <div className="text-xs text-red-600 font-medium">SOURCE</div>
          <div className="font-mono text-red-800">{finding.taint_source ?? "unknown"}</div>
        </div>

        {/* Path hops */}
        {pathSteps.map((step, i) => (
          <div key={i} className="flex items-center gap-2">
            <ArrowRight className="h-4 w-4 text-muted-foreground" />
            <div className="rounded-lg border border-yellow-300 bg-yellow-50 px-3 py-2 text-sm">
              <div className="text-xs text-yellow-700 font-medium">HOP {i + 1}</div>
              <div className="font-mono text-yellow-800">{step}</div>
            </div>
          </div>
        ))}

        {/* Sink node (rule is the sink context) */}
        <ArrowRight className="h-4 w-4 text-muted-foreground" />
        <div className="rounded-lg border-2 border-orange-400 bg-orange-50 px-3 py-2 text-sm">
          <div className="text-xs text-orange-700 font-medium">SINK</div>
          <div className="font-mono text-orange-900">{finding.rule_id}</div>
          <div className="text-xs text-orange-600 mt-0.5">line {finding.line_number}</div>
        </div>
      </div>

      {finding.taint_confidence !== null && (
        <div className="text-xs text-muted-foreground">
          Taint confidence: <strong>{Math.round((finding.taint_confidence ?? 0) * 100)}%</strong>
        </div>
      )}
    </div>
  );
}
