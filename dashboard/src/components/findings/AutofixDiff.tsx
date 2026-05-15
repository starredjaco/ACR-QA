import { useAutofix } from "@/lib/queries";
import { CheckCircle, XCircle, Loader2, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/ui/toast";

interface Props { runId: number; findingId: number; }

export function AutofixDiff({ runId, findingId }: Props) {
  const { data, isLoading, error } = useAutofix(runId, findingId, true);

  if (isLoading) return <div className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" /> Generating patch…</div>;
  if (error) return <div className="text-sm text-red-600">Failed to load autofix: {String(error)}</div>;
  if (!data?.patch) return <div className="text-sm text-muted-foreground italic">No patch available for this finding</div>;

  const lines = data.patch.split("\n");

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm">
          {data.valid
            ? <CheckCircle className="h-4 w-4 text-green-500" />
            : <XCircle className="h-4 w-4 text-yellow-500" />}
          <span className="font-medium">{data.valid ? "Validated patch" : "Unvalidated patch"}</span>
          <span className="text-muted-foreground">({Math.round(data.confidence * 100)}% confidence)</span>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            navigator.clipboard.writeText(data.patch);
            toast("Patch copied!", "success");
          }}
        >
          <Copy className="h-3 w-3 mr-1" /> Copy
        </Button>
      </div>

      {data.explanation && (
        <p className="text-sm text-muted-foreground bg-muted/30 rounded p-2">{data.explanation}</p>
      )}

      <div className="rounded-lg border overflow-hidden font-mono text-xs">
        {lines.map((line, i) => {
          const bg = line.startsWith("+") && !line.startsWith("+++")
            ? "bg-green-50 text-green-800"
            : line.startsWith("-") && !line.startsWith("---")
            ? "bg-red-50 text-red-800"
            : line.startsWith("@@")
            ? "bg-blue-50 text-blue-700"
            : "bg-background text-foreground";
          return (
            <div key={i} className={`px-4 py-0.5 ${bg}`}>
              <span className="select-none mr-3 text-muted-foreground w-6 inline-block text-right">{i + 1}</span>
              {line}
            </div>
          );
        })}
      </div>
    </div>
  );
}
