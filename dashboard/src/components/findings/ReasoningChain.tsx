import { useState } from "react";
import { ChevronDown, ChevronRight, CheckCircle, XCircle, HelpCircle } from "lucide-react";
import { type Finding } from "@/lib/api";
import { cn } from "@/lib/utils";

interface Props { finding: Finding; }

export function ReasoningChain({ finding }: Props) {
  const [open, setOpen] = useState(false);

  if (!finding.triage_verdict) {
    return <div className="text-sm text-muted-foreground italic">No triage data for this finding</div>;
  }

  const icons: Record<string, React.ReactNode> = {
    true_positive: <CheckCircle className="h-4 w-4 text-red-500" />,
    false_positive: <XCircle className="h-4 w-4 text-green-500" />,
    needs_review: <HelpCircle className="h-4 w-4 text-yellow-500" />,
  };
  const labels: Record<string, string> = {
    true_positive: "True Positive",
    false_positive: "False Positive",
    needs_review: "Needs Review",
  };
  const colors: Record<string, string> = {
    true_positive: "border-red-200 bg-red-50",
    false_positive: "border-green-200 bg-green-50",
    needs_review: "border-yellow-200 bg-yellow-50",
  };

  const verdict = finding.triage_verdict;

  return (
    <div className="space-y-3">
      <div className={cn("rounded-lg border p-3 flex items-center gap-3", colors[verdict] ?? "border bg-muted")}>
        {icons[verdict]}
        <div>
          <div className="font-semibold text-sm">{labels[verdict] ?? verdict}</div>
          {finding.triage_confidence_delta !== null && (
            <div className="text-xs text-muted-foreground">
              Confidence delta: {finding.triage_confidence_delta > 0 ? "+" : ""}
              {Math.round((finding.triage_confidence_delta ?? 0) * 100)}%
            </div>
          )}
        </div>
      </div>

      {finding.triage_reasoning && (
        <div>
          <button
            onClick={() => setOpen(!open)}
            className="flex items-center gap-1 text-sm font-medium hover:text-primary transition-colors"
          >
            {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            Reasoning
          </button>
          {open && (
            <div className="mt-2 rounded-lg border bg-muted/30 p-3 text-sm text-muted-foreground whitespace-pre-wrap">
              {finding.triage_reasoning}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
