import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { useFindings } from "@/lib/queries";
import { type Finding } from "@/lib/api";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, ArrowRight, Loader2 } from "lucide-react";
import { severityColor } from "@/lib/utils";

export function RunComparePage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const runIdA = Number(id);
  const [runIdBInput, setRunIdBInput] = useState(searchParams.get("compare") ?? "");
  const [runIdB, setRunIdB] = useState<number | null>(
    searchParams.get("compare") ? Number(searchParams.get("compare")) : null
  );

  const { data: dataA, isLoading: loadingA } = useFindings(runIdA);
  const { data: dataB, isLoading: loadingB } = useFindings(runIdB ?? 0, { enabled: !!runIdB });

  const findingsA = dataA?.findings ?? [];
  const findingsB = dataB?.findings ?? [];

  const ruleSetA = new Set(findingsA.map((f) => `${f.rule_id}::${f.file_path}::${f.line_start}`));
  const ruleSetB = new Set(findingsB.map((f) => `${f.rule_id}::${f.file_path}::${f.line_start}`));

  const added = findingsB.filter((f) => !ruleSetA.has(`${f.rule_id}::${f.file_path}::${f.line_start}`));
  const fixed = findingsA.filter((f) => !ruleSetB.has(`${f.rule_id}::${f.file_path}::${f.line_start}`));
  const unchanged = findingsA.filter((f) => ruleSetB.has(`${f.rule_id}::${f.file_path}::${f.line_start}`));

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate(`/runs/${runIdA}`)}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">Compare Runs</h1>
          <p className="text-sm text-muted-foreground mt-0.5">Run #{runIdA} vs selected baseline</p>
        </div>
      </div>

      {/* Selector */}
      <Card>
        <CardContent className="pt-4">
          <form
            onSubmit={(e) => { e.preventDefault(); setRunIdB(Number(runIdBInput)); }}
            className="flex gap-2 items-end"
          >
            <div className="flex-1">
              <label className="text-sm font-medium">Baseline run ID</label>
              <Input
                className="mt-1"
                value={runIdBInput}
                onChange={(e) => setRunIdBInput(e.target.value)}
                placeholder="e.g. 42"
                type="number"
                min={1}
              />
            </div>
            <Button type="submit">Compare</Button>
          </form>
        </CardContent>
      </Card>

      {(loadingA || loadingB) && (
        <div className="flex justify-center py-8 text-muted-foreground gap-2">
          <Loader2 className="h-5 w-5 animate-spin" /> Loading…
        </div>
      )}

      {runIdB && !loadingA && !loadingB && (
        <>
          {/* Summary */}
          <div className="grid grid-cols-3 gap-4">
            <Card>
              <CardContent className="pt-4 text-center">
                <div className="text-3xl font-bold text-green-600">−{fixed.length}</div>
                <div className="text-xs text-muted-foreground mt-1">Fixed</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 text-center">
                <div className="text-3xl font-bold text-muted-foreground">{unchanged.length}</div>
                <div className="text-xs text-muted-foreground mt-1">Unchanged</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 text-center">
                <div className="text-3xl font-bold text-red-600">+{added.length}</div>
                <div className="text-xs text-muted-foreground mt-1">Introduced</div>
              </CardContent>
            </Card>
          </div>

          {/* Side-by-side table */}
          <div className="grid md:grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  Run #{runIdA}
                  <span className="text-xs text-muted-foreground font-normal">({findingsA.length} findings)</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <FindingList findings={findingsA} highlight={fixed} highlightClass="bg-green-50 dark:bg-green-950/20" />
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  Run #{runIdB}
                  <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground font-normal">({findingsB.length} findings)</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <FindingList findings={findingsB} highlight={added} highlightClass="bg-red-50 dark:bg-red-950/20" />
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

function FindingList({
  findings,
  highlight,
  highlightClass,
}: {
  findings: Finding[];
  highlight: Finding[];
  highlightClass: string;
}) {
  const highlightKeys = new Set(highlight.map((f) => `${f.rule_id}::${f.file_path}::${f.line_start}`));
  return (
    <div className="divide-y max-h-96 overflow-y-auto">
      {findings.map((f) => {
        const key = `${f.rule_id}::${f.file_path}::${f.line_start}`;
        return (
          <div key={f.id} className={`px-4 py-2 text-xs ${highlightKeys.has(key) ? highlightClass : ""}`}>
            <div className="flex items-center gap-2">
              <Badge className={`${severityColor(f.severity)} text-[10px] px-1 py-0`}>{f.severity}</Badge>
              <span className="font-mono font-medium">{f.rule_id}</span>
            </div>
            <div className="text-muted-foreground mt-0.5 truncate">{f.file_path}:{f.line_start}</div>
          </div>
        );
      })}
    </div>
  );
}
