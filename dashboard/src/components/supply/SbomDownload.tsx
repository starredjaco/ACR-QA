import { useState } from "react";
import { Button } from "@/components/ui/button";
import { getSbom } from "@/lib/api";
import { Download, Loader2 } from "lucide-react";
import { toast } from "@/components/ui/toast";

interface Props { runId: number; }

export function SbomDownload({ runId }: Props) {
  const [loading, setLoading] = useState(false);

  async function download() {
    setLoading(true);
    try {
      const { sbom } = await getSbom(runId);
      const blob = new Blob([JSON.stringify(sbom, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `sbom-run-${runId}.json`;
      a.click();
      URL.revokeObjectURL(url);
      toast("SBOM downloaded", "success");
    } catch {
      toast("Failed to download SBOM", "error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Button variant="outline" size="sm" onClick={download} disabled={loading}>
      {loading ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Download className="h-4 w-4 mr-1" />}
      Download SBOM (CycloneDX)
    </Button>
  );
}
