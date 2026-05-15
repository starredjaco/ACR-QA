import { useState } from "react";
import { type Finding } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { truncate, cn } from "@/lib/utils";
import { Search, ChevronUp, ChevronDown } from "lucide-react";

interface Props {
  findings: Finding[];
  onSelect: (f: Finding) => void;
}

type SortKey = "severity" | "confidence" | "rule_id";

const SEV_ORDER: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };

export function FindingsTable({ findings, onSelect }: Props) {
  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [sortKey, setSortKey] = useState<SortKey>("severity");
  const [sortAsc, setSortAsc] = useState(true);

  const filtered = findings
    .filter((f) => {
      if (severityFilter !== "all" && f.severity !== severityFilter) return false;
      if (search) {
        const q = search.toLowerCase();
        return (
          f.rule_id?.toLowerCase().includes(q) ||
          f.message?.toLowerCase().includes(q) ||
          f.file_path?.toLowerCase().includes(q)
        );
      }
      return true;
    })
    .sort((a, b) => {
      let cmp = 0;
      if (sortKey === "severity") cmp = (SEV_ORDER[a.severity] ?? 9) - (SEV_ORDER[b.severity] ?? 9);
      else if (sortKey === "confidence") cmp = (b.confidence ?? 0) - (a.confidence ?? 0);
      else if (sortKey === "rule_id") cmp = (a.rule_id ?? "").localeCompare(b.rule_id ?? "");
      return sortAsc ? cmp : -cmp;
    });

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(true); }
  }

  const SortIcon = ({ k }: { k: SortKey }) => sortKey === k
    ? (sortAsc ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />)
    : null;

  const severities = ["all", "high", "medium", "low"];

  return (
    <div className="space-y-3">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search rule, file, message…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8"
          />
        </div>
        <div className="flex gap-1">
          {severities.map((s) => (
            <button
              key={s}
              onClick={() => setSeverityFilter(s)}
              className={cn(
                "rounded px-2 py-1 text-xs font-medium transition-colors",
                severityFilter === s ? "bg-primary text-primary-foreground" : "bg-muted hover:bg-muted/80"
              )}
            >
              {s.toUpperCase()}
            </button>
          ))}
        </div>
        <span className="text-xs text-muted-foreground">{filtered.length} / {findings.length}</span>
      </div>

      <div className="rounded-lg border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-2 text-left font-medium cursor-pointer select-none" onClick={() => toggleSort("severity")}>
                  <span className="flex items-center gap-1">Sev <SortIcon k="severity" /></span>
                </th>
                <th className="px-4 py-2 text-left font-medium cursor-pointer select-none" onClick={() => toggleSort("rule_id")}>
                  <span className="flex items-center gap-1">Rule <SortIcon k="rule_id" /></span>
                </th>
                <th className="px-4 py-2 text-left font-medium hidden md:table-cell">File</th>
                <th className="px-4 py-2 text-left font-medium">Message</th>
                <th className="px-4 py-2 text-left font-medium cursor-pointer select-none hidden lg:table-cell" onClick={() => toggleSort("confidence")}>
                  <span className="flex items-center gap-1">Conf <SortIcon k="confidence" /></span>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filtered.map((f) => (
                <tr
                  key={f.id}
                  onClick={() => onSelect(f)}
                  className="cursor-pointer hover:bg-muted/30 transition-colors"
                >
                  <td className="px-4 py-2">
                    <Badge variant={f.severity as "high" | "medium" | "low" | "default"}>{f.severity}</Badge>
                  </td>
                  <td className="px-4 py-2 font-mono text-xs">{f.rule_id}</td>
                  <td className="px-4 py-2 text-xs text-muted-foreground hidden md:table-cell font-mono">
                    {truncate(f.file_path ?? "", 40)}
                    {f.line_number && <span className="text-xs opacity-60">:{f.line_number}</span>}
                  </td>
                  <td className="px-4 py-2 text-xs">{truncate(f.message ?? "", 70)}</td>
                  <td className="px-4 py-2 text-xs hidden lg:table-cell">
                    <div className="flex items-center gap-1">
                      <div className="w-12 h-1.5 rounded-full bg-muted overflow-hidden">
                        <div className="h-full bg-primary rounded-full" style={{ width: `${Math.round((f.confidence ?? 0) * 100)}%` }} />
                      </div>
                      <span className="text-muted-foreground">{Math.round((f.confidence ?? 0) * 100)}%</span>
                    </div>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">No findings match your filters</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
