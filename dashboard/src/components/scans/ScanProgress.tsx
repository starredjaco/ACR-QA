import { useScanProgress } from "@/lib/sse";
import { CheckCircle, XCircle, Loader2 } from "lucide-react";

interface Props { jobId: string; onComplete?: (runId?: number) => void; }

export function ScanProgress({ jobId, onComplete }: Props) {
  const { events, done } = useScanProgress(jobId);

  const lastComplete = [...events].reverse().find((e) => e.type === "complete");
  if (done && lastComplete && onComplete) onComplete(lastComplete.run_id);

  return (
    <div className="space-y-2 text-sm">
      {events.map((e, i) => (
        <div key={i} className="flex items-center gap-2">
          {e.type === "complete" && <CheckCircle className="h-4 w-4 text-green-500" />}
          {e.type === "error" && <XCircle className="h-4 w-4 text-red-500" />}
          {e.type === "progress" && <Loader2 className="h-4 w-4 animate-spin text-blue-500" />}
          <span className={e.type === "error" ? "text-red-600" : "text-muted-foreground"}>{e.message}</span>
          {e.percent !== undefined && (
            <div className="ml-auto w-24 h-1.5 rounded-full bg-muted overflow-hidden">
              <div className="h-full bg-primary rounded-full" style={{ width: `${e.percent}%` }} />
            </div>
          )}
        </div>
      ))}
      {!done && events.length === 0 && (
        <div className="flex items-center gap-2 text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" /> Waiting for scan to start…
        </div>
      )}
    </div>
  );
}
