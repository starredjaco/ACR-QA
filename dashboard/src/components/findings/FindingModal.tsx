import { useState } from "react";
import { Dialog, TabsList, TabsTrigger } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { type Finding, postSecondOpinion, type SecondOpinion } from "@/lib/api";
import { TaintFlowGraph } from "./TaintFlowGraph";
import { ReasoningChain } from "./ReasoningChain";
import { AutofixDiff } from "./AutofixDiff";
import { ExploitProofPanel } from "./ExploitProofPanel";
import { ChatSidebar } from "./ChatSidebar";
import { CallGraph } from "./CallGraph";
import { FindingHistory } from "./FindingHistory";
import { Loader2, CheckCircle, XCircle, AlertCircle } from "lucide-react";

interface Props {
  finding: Finding | null;
  runId: number;
  onClose: () => void;
}

const TABS = ["Overview", "Chat", "Call Graph", "History", "Taint", "Reasoning", "Autofix", "Exploit", "2nd Opinion"];

export function FindingModal({ finding, runId, onClose }: Props) {
  const [tab, setTab] = useState("Overview");
  const [opinion, setOpinion] = useState<SecondOpinion | null>(null);
  const [opinionLoading, setOpinionLoading] = useState(false);

  async function fetchOpinion() {
    if (!finding) return;
    setOpinionLoading(true);
    try {
      const result = await postSecondOpinion(finding.id);
      setOpinion(result);
    } finally {
      setOpinionLoading(false);
    }
  }

  if (!finding) return null;

  return (
    <Dialog open={!!finding} onClose={onClose} title={finding.rule_id} className="max-w-4xl">
      <div className="space-y-4">
        <div className="flex flex-wrap gap-2 items-center">
          <Badge variant={finding.severity as "high" | "medium" | "low" | "default"}>{finding.severity.toUpperCase()}</Badge>
          {finding.category && <Badge variant="secondary">{finding.category}</Badge>}
          {finding.tool && <span className="text-xs text-muted-foreground">via {finding.tool}</span>}
          <span className="ml-auto text-xs text-muted-foreground">
            Confidence: {Math.round((finding.confidence ?? 0) * 100)}%
          </span>
        </div>

        <div className="rounded bg-muted px-3 py-2 font-mono text-xs">
          {finding.file_path}{finding.line_number ? `:${finding.line_number}` : ""}
        </div>

        <TabsList>
          {TABS.map((t) => (
            <TabsTrigger
              key={t}
              value={t}
              label={t}
              active={tab === t}
              onClick={() => setTab(t)}
            />
          ))}
        </TabsList>

        {tab === "Overview" && (
          <div className="space-y-3">
            <div>
              <div className="text-xs font-medium text-muted-foreground mb-1">Message</div>
              <p className="text-sm">{finding.message}</p>
            </div>
            {finding.explanation_text && (
              <div>
                <div className="text-xs font-medium text-muted-foreground mb-1">AI Explanation</div>
                <div className="rounded-lg border bg-muted/20 p-3 text-sm whitespace-pre-wrap">
                  {finding.explanation_text}
                </div>
              </div>
            )}
            {finding.model_name && (
              <div className="text-xs text-muted-foreground">
                Model: {finding.model_name}
              </div>
            )}
          </div>
        )}

        {tab === "Chat" && <ChatSidebar findingId={finding.id} />}
        {tab === "Call Graph" && <CallGraph findingId={finding.id} />}
        {tab === "History" && <FindingHistory findingId={finding.id} />}
        {tab === "Taint" && <TaintFlowGraph finding={finding} />}
        {tab === "Reasoning" && <ReasoningChain finding={finding} />}
        {tab === "Autofix" && <AutofixDiff runId={runId} findingId={finding.id} />}
        {tab === "Exploit" && <ExploitProofPanel finding={finding} />}

        {tab === "2nd Opinion" && (
          <div className="space-y-4">
            {!opinion && !opinionLoading && (
              <div className="text-center py-8">
                <p className="text-sm text-muted-foreground mb-4">Get a second AI verdict from a different provider to cross-check this finding.</p>
                <Button onClick={fetchOpinion}>Request Second Opinion</Button>
              </div>
            )}
            {opinionLoading && (
              <div className="flex items-center justify-center py-12 gap-2 text-muted-foreground">
                <Loader2 className="h-5 w-5 animate-spin" /> Consulting second model…
              </div>
            )}
            {opinion && (
              <div className="space-y-3">
                <div className={`rounded-lg p-3 text-sm font-medium flex items-center gap-2 ${opinion.agreement ? "bg-green-50 text-green-800 dark:bg-green-900/20 dark:text-green-300" : "bg-yellow-50 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300"}`}>
                  {opinion.agreement ? <CheckCircle className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
                  {opinion.agreement ? "Models agree" : "Models disagree — manual review recommended"}
                </div>
                {[
                  { provider: opinion.primary_provider, verdict: opinion.primary_verdict, reason: opinion.primary_reason },
                  { provider: opinion.secondary_provider, verdict: opinion.secondary_verdict, reason: opinion.secondary_reason },
                ].map(({ provider, verdict, reason }) => (
                  <div key={provider} className="rounded-lg border p-3 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono bg-muted px-2 py-0.5 rounded">{provider}</span>
                      <Badge variant={verdict === "TP" ? "destructive" : verdict === "FP" ? "secondary" : "outline"} className="text-xs">{verdict}</Badge>
                    </div>
                    {reason && <p className="text-sm text-muted-foreground">{reason}</p>}
                  </div>
                ))}
                {opinion.skipped_reason && (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <XCircle className="h-3.5 w-3.5" />
                    Secondary skipped: {opinion.skipped_reason}
                  </div>
                )}
                <div className="flex justify-between items-center text-xs text-muted-foreground pt-1">
                  <span>Latency: {opinion.latency_ms}ms</span>
                  <Button variant="ghost" size="sm" onClick={fetchOpinion} disabled={opinionLoading}>Re-run</Button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </Dialog>
  );
}
