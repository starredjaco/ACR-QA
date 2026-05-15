import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/lib/auth";
import { Wifi, WifiOff, Server, User, Shield, CheckCircle, XCircle, Loader2 } from "lucide-react";
import { toast } from "@/components/ui/toast";

type HealthStatus = "checking" | "ok" | "error";

function useHealthCheck(url: string) {
  const [status, setStatus] = useState<HealthStatus>("checking");

  useEffect(() => {
    const check = async () => {
      setStatus("checking");
      try {
        const res = await fetch(url, { signal: AbortSignal.timeout(3000) });
        setStatus(res.ok ? "ok" : "error");
      } catch {
        setStatus("error");
      }
    };
    check();
    const interval = setInterval(check, 30_000);
    return () => clearInterval(interval);
  }, [url]);

  return status;
}

function StatusDot({ status }: { status: HealthStatus }) {
  if (status === "checking") return <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />;
  if (status === "ok") return <CheckCircle className="h-4 w-4 text-green-600" />;
  return <XCircle className="h-4 w-4 text-red-500" />;
}

export function SettingsPage() {
  const { user, logout } = useAuth();
  const mode = import.meta.env.VITE_ACRQA_MODE ?? "online";
  const isOffline = mode === "offline";

  const apiStatus = useHealthCheck("/v1/health");
  const celeryStatus = useHealthCheck("/v1/celery/health");

  function handleLogout() {
    logout();
    window.location.href = "/login";
  }

  function handleCopyToken() {
    const raw = localStorage.getItem("acrqa_auth");
    if (!raw) return;
    try {
      const { state } = JSON.parse(raw);
      navigator.clipboard.writeText(state.token ?? "").then(() => toast("Token copied", "success"));
    } catch {
      toast("Failed to copy token", "error");
    }
  }

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-sm text-muted-foreground mt-1">System status and account configuration</p>
      </div>

      {/* Mode card */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            {isOffline ? <WifiOff className="h-4 w-4" /> : <Wifi className="h-4 w-4" />}
            Operation Mode
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm">Current mode</span>
            <Badge variant={isOffline ? "destructive" : "default"} className="uppercase text-xs">
              {mode}
            </Badge>
          </div>
          {isOffline && (
            <p className="text-xs text-muted-foreground bg-muted/50 rounded p-2">
              Offline mode: LLM calls routed to local Ollama endpoint. External OSV and GitHub API
              calls disabled. Set <code className="font-mono">ACRQA_LLM_PROVIDER=ollama</code> and{" "}
              <code className="font-mono">ACRQA_MODE=offline</code> in the backend environment.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Live status */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            <Server className="h-4 w-4" /> Live Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              { label: "FastAPI backend", status: apiStatus },
              { label: "Celery worker", status: celeryStatus },
            ].map(({ label, status }) => (
              <div key={label} className="flex items-center justify-between py-1 border-b last:border-0">
                <span className="text-sm">{label}</span>
                <div className="flex items-center gap-2">
                  <StatusDot status={status} />
                  <span className="text-xs text-muted-foreground">
                    {status === "checking" ? "checking" : status === "ok" ? "healthy" : "unreachable"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Account */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            <User className="h-4 w-4" /> Account
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {user && (
            <>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Email</span>
                <span className="text-sm font-medium">{user.email}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Role</span>
                <Badge variant="outline" className="text-xs">
                  <Shield className="h-3 w-3 mr-1" />
                  {user.role ?? "analyst"}
                </Badge>
              </div>
            </>
          )}
          <div className="flex gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={handleCopyToken}>
              Copy API token
            </Button>
            <Button variant="destructive" size="sm" onClick={handleLogout}>
              Sign out
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Version */}
      <div className="text-xs text-muted-foreground text-center pt-2">
        ACR-QA v3.8.0 — Dashboard PRO · Phase 6
      </div>
    </div>
  );
}
