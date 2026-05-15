import { type Dependency } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { riskColor } from "@/lib/utils";
import { ShieldAlert, GitBranch, Package } from "lucide-react";

interface Props { deps: Dependency[]; }

export function DependencyTree({ deps }: Props) {
  if (!deps.length) return <div className="text-sm text-muted-foreground">No dependencies found</div>;

  return (
    <div className="rounded-lg border overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-muted/50">
          <tr>
            <th className="px-4 py-2 text-left font-medium">Package</th>
            <th className="px-4 py-2 text-left font-medium">Version</th>
            <th className="px-4 py-2 text-left font-medium hidden md:table-cell">Ecosystem</th>
            <th className="px-4 py-2 text-left font-medium">Risk</th>
            <th className="px-4 py-2 text-left font-medium">CVEs</th>
            <th className="px-4 py-2 text-left font-medium hidden lg:table-cell">Stars</th>
            <th className="px-4 py-2 text-left font-medium hidden lg:table-cell">Last commit</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {deps.map((d) => (
            <tr key={d.id} className="hover:bg-muted/20">
              <td className="px-4 py-2 font-mono font-medium flex items-center gap-2">
                <Package className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                {d.name}
                {d.archived && <Badge variant="destructive" className="text-[10px] px-1 py-0">ARCHIVED</Badge>}
              </td>
              <td className="px-4 py-2 font-mono text-xs text-muted-foreground">{d.version ?? "—"}</td>
              <td className="px-4 py-2 hidden md:table-cell text-xs text-muted-foreground">{d.ecosystem}</td>
              <td className="px-4 py-2">
                <span className={`inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-medium ${riskColor(d.risk_level)}`}>
                  {d.risk_level === "high" && <ShieldAlert className="h-3 w-3" />}
                  {d.risk_level} ({d.risk_score})
                </span>
              </td>
              <td className="px-4 py-2">
                {d.cve_count > 0
                  ? <span className="text-red-600 font-medium">{d.cve_count}</span>
                  : <span className="text-muted-foreground">0</span>}
              </td>
              <td className="px-4 py-2 hidden lg:table-cell text-xs text-muted-foreground">
                {d.stars !== null
                  ? <span className="flex items-center gap-1"><GitBranch className="h-3 w-3" />{d.stars.toLocaleString()}</span>
                  : "—"}
              </td>
              <td className="px-4 py-2 hidden lg:table-cell text-xs text-muted-foreground">
                {d.last_commit_days !== null ? `${d.last_commit_days}d ago` : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
