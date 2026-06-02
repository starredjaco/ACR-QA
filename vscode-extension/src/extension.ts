/**
 * ACR-QA VS Code Extension — entry point
 *
 * Provides two modes:
 *   server    — talks to a running ACR-QA FastAPI instance (GET /v1/scans, etc.)
 *   standalone — spawns `python3 CORE/main.py` in the workspace and parses JSON output
 */

import * as vscode from "vscode";
import * as path from "path";
import * as cp from "child_process";
import axios from "axios";

// ── Diagnostics collection ────────────────────────────────────────────────────

const DIAG = vscode.languages.createDiagnosticCollection("acrqa");

// ── Severity helpers ──────────────────────────────────────────────────────────

function toVSCodeSeverity(sev: string): vscode.DiagnosticSeverity {
  switch (sev.toLowerCase()) {
    case "critical":
    case "high":
      return vscode.DiagnosticSeverity.Error;
    case "medium":
      return vscode.DiagnosticSeverity.Warning;
    default:
      return vscode.DiagnosticSeverity.Information;
  }
}

// ── Config helper ─────────────────────────────────────────────────────────────

function cfg<T>(key: string): T {
  return vscode.workspace.getConfiguration("acrqa").get<T>(key) as T;
}

// ── Server mode: call ACR-QA REST API ─────────────────────────────────────────

async function scanViaServer(targetDir: string): Promise<Finding[]> {
  const base = cfg<string>("serverUrl").replace(/\/$/, "");
  const apiKey = cfg<string>("apiKey");
  const headers: Record<string, string> = apiKey
    ? { "X-API-Key": apiKey }
    : {};

  // Trigger scan
  const triggerRes = await axios.post(
    `${base}/v1/scans`,
    { target_dir: targetDir, repo_name: path.basename(targetDir), no_ai: false },
    { headers, timeout: 10_000 }
  );
  const runId: number = triggerRes.data?.run_id ?? triggerRes.data?.id;
  if (!runId) {
    throw new Error("ACR-QA server did not return a run_id");
  }

  // Poll until complete (max 3 min)
  for (let i = 0; i < 36; i++) {
    await sleep(5_000);
    const statusRes = await axios.get(`${base}/v1/runs/${runId}`, { headers });
    const status: string = statusRes.data?.status ?? "";
    if (status === "complete" || status === "completed") {
      break;
    }
    if (status === "failed") {
      throw new Error(`Scan ${runId} failed`);
    }
  }

  const findingsRes = await axios.get(`${base}/v1/runs/${runId}/findings`, { headers });
  return (findingsRes.data?.findings ?? []) as Finding[];
}

// ── Standalone mode: run CLI, parse JSON stdout ───────────────────────────────

async function scanStandalone(targetDir: string): Promise<Finding[]> {
  const wsRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? targetDir;
  const groqKey = cfg<string>("groqApiKey");
  const env = { ...process.env, ...(groqKey ? { GROQ_API_KEY_1: groqKey } : {}) };

  return new Promise((resolve, reject) => {
    const child = cp.spawn(
      "python3",
      ["CORE/main.py", "--target-dir", targetDir, "--json", "--no-ai"],
      { cwd: wsRoot, env }
    );
    let out = "";
    child.stdout.on("data", (d) => (out += d));
    child.on("close", (code) => {
      try {
        const parsed = JSON.parse(out);
        resolve((parsed.findings ?? []) as Finding[]);
      } catch {
        if (code !== 0 && !out.trim()) {
          reject(new Error("ACR-QA CLI failed. Make sure CORE/main.py is in the workspace root."));
        } else {
          resolve([]);
        }
      }
    });
    child.on("error", reject);
  });
}

// ── Apply findings as VS Code diagnostics ────────────────────────────────────

function applyFindings(findings: Finding[], wsRoot: string): void {
  DIAG.clear();
  const allowedSeverities = new Set(
    cfg<string[]>("severity").map((s) => s.toLowerCase())
  );
  const confirmedOnly = cfg<boolean>("confirmedTierOnly");

  const byFile = new Map<string, vscode.Diagnostic[]>();

  for (const f of findings) {
    const sev = (f.severity ?? "low").toLowerCase();
    if (!allowedSeverities.has(sev)) {
      continue;
    }
    if (confirmedOnly && !f.confirmed_tier) {
      continue;
    }

    const filePath = path.isAbsolute(f.file ?? "")
      ? f.file
      : path.join(wsRoot, f.file ?? "");
    const line = Math.max(0, (f.line ?? 1) - 1);
    const range = new vscode.Range(line, 0, line, 999);

    const message = `[ACR-QA ${f.canonical_rule_id ?? f.rule_id ?? ""}] ${f.message ?? ""}`;
    const diag = new vscode.Diagnostic(range, message, toVSCodeSeverity(sev));
    diag.source = "ACR-QA";
    diag.code = {
      value: f.canonical_rule_id ?? f.rule_id ?? "",
      target: vscode.Uri.parse(`https://github.com/ahmed-145/ACR-QA/blob/main/docs/DEFENSE_QA.md`),
    };

    const key = filePath ?? "";
    if (!byFile.has(key)) {
      byFile.set(key, []);
    }
    byFile.get(key)!.push(diag);
  }

  for (const [file, diags] of byFile) {
    DIAG.set(vscode.Uri.file(file), diags);
  }
}

// ── Main scan function ────────────────────────────────────────────────────────

async function runScan(targetDir: string): Promise<void> {
  const mode = cfg<string>("mode");
  const wsRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? targetDir;

  await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: "ACR-QA",
      cancellable: false,
    },
    async (progress) => {
      progress.report({ message: `Scanning ${path.basename(targetDir)}…` });
      try {
        const findings =
          mode === "server"
            ? await scanViaServer(targetDir)
            : await scanStandalone(targetDir);
        applyFindings(findings, wsRoot);
        const count = findings.length;
        vscode.window.showInformationMessage(
          `ACR-QA: ${count} finding${count !== 1 ? "s" : ""} in ${path.basename(targetDir)}`
        );
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        vscode.window.showErrorMessage(`ACR-QA scan failed: ${msg}`);
      }
    }
  );
}

// ── Extension activate / deactivate ──────────────────────────────────────────

export function activate(ctx: vscode.ExtensionContext): void {
  // Scan workspace
  ctx.subscriptions.push(
    vscode.commands.registerCommand("acrqa.scanWorkspace", async () => {
      const wsRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
      if (!wsRoot) {
        vscode.window.showWarningMessage("ACR-QA: open a workspace folder first");
        return;
      }
      await runScan(wsRoot);
    })
  );

  // Scan current file's directory
  ctx.subscriptions.push(
    vscode.commands.registerCommand("acrqa.scanFile", async () => {
      const file = vscode.window.activeTextEditor?.document.uri.fsPath;
      if (!file) {
        vscode.window.showWarningMessage("ACR-QA: no active file");
        return;
      }
      await runScan(path.dirname(file));
    })
  );

  // Show findings panel
  ctx.subscriptions.push(
    vscode.commands.registerCommand("acrqa.showFindings", () => {
      vscode.commands.executeCommand("workbench.view.extension.acrqa-panel");
    })
  );

  // Clear diagnostics
  ctx.subscriptions.push(
    vscode.commands.registerCommand("acrqa.clearDiagnostics", () => {
      DIAG.clear();
    })
  );

  // Auto-scan on save (optional)
  ctx.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument(async (doc) => {
      if (!cfg<boolean>("autoScanOnSave")) {
        return;
      }
      const lang = doc.languageId;
      if (!["python", "javascript", "typescript", "go"].includes(lang)) {
        return;
      }
      await runScan(path.dirname(doc.uri.fsPath));
    })
  );

  ctx.subscriptions.push(DIAG);
}

export function deactivate(): void {
  DIAG.dispose();
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

interface Finding {
  id?: number;
  file?: string;
  line?: number;
  severity?: string;
  message?: string;
  canonical_rule_id?: string;
  rule_id?: string;
  confirmed_tier?: boolean;
}
