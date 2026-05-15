import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { type Run } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { GitBranch, Clock, AlertTriangle } from "lucide-react";

interface Props { run: Run; }

export function ScanCard({ run }: Props) {
  const statusColor: Record<string, string> = {
    completed: "bg-green-100 text-green-800",
    running: "bg-blue-100 text-blue-800",
    failed: "bg-red-100 text-red-800",
    pending: "bg-gray-100 text-gray-700",
  };

  return (
    <Link to={`/runs/${run.id}`}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <GitBranch className="h-4 w-4 text-muted-foreground" />
              {run.repo_name}
              {run.pr_number && <span className="text-muted-foreground font-normal">#{run.pr_number}</span>}
            </CardTitle>
            <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusColor[run.status] ?? statusColor.pending}`}>
              {run.status}
            </span>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 text-sm text-muted-foreground mb-3">
            <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> {formatDate(run.started_at)}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1 text-sm"><AlertTriangle className="h-3 w-3" /> {run.total_findings} findings</span>
            {run.high_count > 0 && <Badge variant="high">{run.high_count} HIGH</Badge>}
            {run.medium_count > 0 && <Badge variant="medium">{run.medium_count} MED</Badge>}
            {run.low_count > 0 && <Badge variant="low">{run.low_count} LOW</Badge>}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
