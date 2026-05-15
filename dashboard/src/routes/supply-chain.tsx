import { useState } from "react";
import { useRuns, useSupplyChain } from "@/lib/queries";
import { DependencyTree } from "@/components/supply/DependencyTree";
import { SbomDownload } from "@/components/supply/SbomDownload";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, Package, ShieldAlert, Archive } from "lucide-react";
import { riskColor } from "@/lib/utils";

export function SupplyChainPage() {
  const { data: runsData, isLoading: runsLoading } = useRuns(10);
  const runs = runsData?.runs ?? [];
  const latestRun = runs.find((r) => r.status === "completed");
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);

  const runId = selectedRunId ?? latestRun?.id ?? null;
  const { data: scData, isLoading: scLoading } = useSupplyChain(runId ?? 0, { enabled: !!runId });

  const deps = scData?.dependencies ?? [];
  const highRisk = deps.filter((d) => d.risk_level === "high");
  const withCves = deps.filter((d) => d.cve_count > 0);
  const archived = deps.filter((d) => d.archived);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Supply Chain</h1>
          <p className="text-sm text-muted-foreground mt-1">Dependency risk analysis and SBOM</p>
        </div>
        {runId && <SbomDownload runId={runId} />}
      </div>

      {/* Run selector */}
      {!runsLoading && runs.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {runs.filter((r) => r.status === "completed").slice(0, 8).map((r) => (
            <Button
              key={r.id}
              variant={runId === r.id ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedRunId(r.id)}
            >
              Run #{r.id}
            </Button>
          ))}
        </div>
      )}

      {scLoading || runsLoading ? (
        <div className="flex items-center justify-center py-16 text-muted-foreground gap-2">
          <Loader2 className="h-5 w-5 animate-spin" /> Loading supply chain data…
        </div>
      ) : !runId ? (
        <div className="text-center py-16 text-muted-foreground">
          <Package className="h-10 w-10 mx-auto mb-3 opacity-40" />
          <p>No completed scans found. Run a scan first.</p>
        </div>
      ) : (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-4">
                <div className="text-2xl font-bold">{deps.length}</div>
                <div className="text-xs text-muted-foreground mt-1">Total dependencies</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <div className={`text-2xl font-bold ${highRisk.length > 0 ? "text-red-600" : ""}`}>
                  {highRisk.length}
                </div>
                <div className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                  <ShieldAlert className="h-3 w-3" /> High risk
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <div className={`text-2xl font-bold ${withCves.length > 0 ? "text-orange-600" : ""}`}>
                  {withCves.length}
                </div>
                <div className="text-xs text-muted-foreground mt-1">With CVEs</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <div className={`text-2xl font-bold ${archived.length > 0 ? "text-yellow-600" : ""}`}>
                  {archived.length}
                </div>
                <div className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                  <Archive className="h-3 w-3" /> Archived
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Risk breakdown */}
          {deps.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Risk distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex gap-3 flex-wrap">
                  {(["high", "medium", "low"] as const).map((level) => {
                    const count = deps.filter((d) => d.risk_level === level).length;
                    return count > 0 ? (
                      <span
                        key={level}
                        className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium ${riskColor(level)}`}
                      >
                        {count} {level}
                      </span>
                    ) : null;
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Alerts */}
          {highRisk.length > 0 && (
            <Card className="border-red-200 dark:border-red-900">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-red-600 flex items-center gap-2">
                  <ShieldAlert className="h-4 w-4" /> High-risk packages
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex gap-2 flex-wrap">
                  {highRisk.map((d) => (
                    <Badge key={d.id} variant="destructive" className="font-mono text-xs">
                      {d.name} {d.version}
                      {d.cve_count > 0 && ` (${d.cve_count} CVE)`}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Full dependency tree */}
          <div>
            <h2 className="text-lg font-semibold mb-3">All dependencies</h2>
            <DependencyTree deps={deps} />
          </div>
        </>
      )}
    </div>
  );
}
