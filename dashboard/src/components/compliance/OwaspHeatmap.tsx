import { useCompliance } from "@/lib/queries";

const OWASP_LABELS: Record<string, string> = {
  A01: "Broken Access Control",
  A02: "Cryptographic Failures",
  A03: "Injection",
  A04: "Insecure Design",
  A05: "Security Misconfiguration",
  A06: "Vulnerable Components",
  A07: "Auth Failures",
  A08: "Data Integrity",
  A09: "Logging Failures",
  A10: "SSRF",
};

interface Props { runId: number; }

export function OwaspHeatmap({ runId }: Props) {
  const { data, isLoading } = useCompliance(runId);
  if (isLoading) return <div className="text-sm text-muted-foreground">Loading compliance data…</div>;
  if (!data) return null;

  const owasp = data.owasp ?? {};
  const entries = Object.keys(OWASP_LABELS).map((key) => ({
    key,
    label: OWASP_LABELS[key],
    count: owasp[key]?.count ?? 0,
    severity: owasp[key]?.severity ?? "none",
  }));

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-sm">OWASP Top 10 Coverage</h3>
        <span className="text-xs text-muted-foreground">Score: {data.overall_score ?? "—"}%</span>
      </div>
      <div className="grid grid-cols-2 gap-2 md:grid-cols-5">
        {entries.map(({ key, label, count, severity }) => {
          const bg =
            count === 0 ? "bg-green-50 border-green-200" :
            severity === "high" ? "bg-red-50 border-red-200" :
            severity === "medium" ? "bg-yellow-50 border-yellow-200" :
            "bg-blue-50 border-blue-200";
          return (
            <div key={key} className={`rounded-lg border p-2 text-center ${bg}`}>
              <div className="text-xs font-bold text-muted-foreground">{key}</div>
              <div className="text-xs truncate mt-0.5" title={label}>{label}</div>
              <div className="text-lg font-bold mt-1">{count}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
