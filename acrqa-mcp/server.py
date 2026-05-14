"""
ACR-QA MCP Server (v3.4.0) — Feature 11.

Exposes ACR-QA as an MCP server so Claude Code, Cursor, and Continue
can trigger security scans pre-PR, directly from the AI coding context.

3 tools:
  acrqa_scan(target_dir)      → queues a Celery scan, polls until done, returns summary
  acrqa_explain(finding_id)   → returns AI explanation for a stored finding
  acrqa_fix(finding_id)       → returns autofix suggestion for a stored finding

Config (env vars or ~/.config/acrqa/config.json):
  ACRQA_URL    — base URL of the running ACR-QA FastAPI server (default: http://localhost:8000)
  ACRQA_TOKEN  — Bearer token (obtain via POST /v1/auth/login)
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_CONFIG_PATH = Path.home() / ".config" / "acrqa" / "config.json"


def _load_config() -> dict:
    cfg: dict = {}
    if _CONFIG_PATH.exists():
        try:
            cfg = json.loads(_CONFIG_PATH.read_text())
        except Exception:
            pass
    return cfg


def _get_base_url() -> str:
    return os.environ.get("ACRQA_URL") or _load_config().get("url", "http://localhost:8000")


def _get_token() -> str:
    return os.environ.get("ACRQA_TOKEN") or _load_config().get("token", "")


def _headers() -> dict[str, str]:
    token = _get_token()
    h: dict[str, str] = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _post(path: str, body: dict) -> dict:
    url = f"{_get_base_url().rstrip('/')}{path}"
    with httpx.Client(timeout=30) as client:
        r = client.post(url, json=body, headers=_headers())
        r.raise_for_status()
        return r.json()


def _get(path: str) -> dict:
    url = f"{_get_base_url().rstrip('/')}{path}"
    with httpx.Client(timeout=30) as client:
        r = client.get(url, headers=_headers())
        r.raise_for_status()
        return r.json()


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _tool_scan(target_dir: str, repo_name: str = "mcp-scan", poll_timeout: int = 120) -> dict[str, Any]:
    """
    Queue a full ACR-QA scan on target_dir, poll until complete, return summary.

    Returns a dict with: job_id, status, findings_count, high_count, medium_count,
    low_count, top_findings (up to 5 most severe), duration_seconds.
    """
    # Submit
    try:
        job = _post("/v1/scans", {"target_dir": target_dir, "repo_name": repo_name})
    except httpx.HTTPError as e:
        return {"error": f"Failed to submit scan: {e}", "target_dir": target_dir}

    job_id = job.get("job_id", "")

    # Poll
    deadline = time.time() + poll_timeout
    status = "queued"
    result: dict = {}
    while time.time() < deadline:
        try:
            poll = _get(f"/v1/scans/{job_id}")
            status = poll.get("status", "queued")
            if status in ("completed", "failed"):
                result = poll.get("result") or {}
                break
        except httpx.HTTPError:
            pass
        time.sleep(3)

    if status != "completed":
        return {"job_id": job_id, "status": status, "error": "Scan did not complete within timeout"}

    # Build terse summary for the AI
    run_id = result.get("run_id")
    all_findings: list[dict] = result.get("findings", [])
    findings_count = len(all_findings)
    high_count = sum(1 for f in all_findings if f.get("severity") == "high")
    medium_count = sum(1 for f in all_findings if f.get("severity") == "medium")
    low_count = sum(1 for f in all_findings if f.get("severity") == "low")

    # Top 5 most severe
    severity_order = {"high": 0, "medium": 1, "low": 2}
    top = sorted(all_findings, key=lambda f: severity_order.get(f.get("severity", "low"), 3))[:5]
    top_findings = [
        {
            "id": f.get("id"),
            "rule_id": f.get("canonical_rule_id", f.get("rule_id", "")),
            "severity": f.get("severity", ""),
            "file": f.get("file", f.get("file_path", "")),
            "line": f.get("line", f.get("line_number", "")),
            "message": f.get("message", f.get("description", "")),
        }
        for f in top
    ]

    return {
        "job_id": job_id,
        "run_id": run_id,
        "status": "completed",
        "target_dir": target_dir,
        "findings_count": findings_count,
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count,
        "top_findings": top_findings,
        "summary": (
            f"Scan complete: {findings_count} findings "
            f"({high_count} HIGH, {medium_count} MEDIUM, {low_count} LOW)"
        ),
    }


def _tool_explain(finding_id: int) -> dict[str, Any]:
    """
    Return the AI explanation for a stored finding.

    The ACR-QA pipeline generates an LLM explanation for each finding during analysis.
    This tool retrieves the pre-generated explanation from the database.
    """
    try:
        data = _get(f"/v1/runs/findings/{finding_id}/explanation")
        return {
            "finding_id": finding_id,
            "explanation": data.get("explanation", data.get("text", "")),
            "rule_id": data.get("canonical_rule_id", ""),
            "severity": data.get("severity", ""),
            "model": data.get("model", ""),
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {
                "finding_id": finding_id,
                "error": "No explanation found for this finding. Run a full scan to generate explanations.",
            }
        return {"finding_id": finding_id, "error": f"HTTP {e.response.status_code}: {e}"}
    except httpx.HTTPError as e:
        return {"finding_id": finding_id, "error": str(e)}


def _tool_fix(finding_id: int) -> dict[str, Any]:
    """
    Return an autofix suggestion (unified diff) for a stored finding.

    Returns the fix suggestion, confidence score, and whether it can be auto-applied.
    """
    try:
        data = _get(f"/v1/runs/findings/{finding_id}/fix")
        return {
            "finding_id": finding_id,
            "can_fix": data.get("can_fix", False),
            "confidence": data.get("confidence", 0),
            "fix_description": data.get("fix_description", ""),
            "diff": data.get("diff", data.get("fix_code", "")),
            "rule_id": data.get("canonical_rule_id", ""),
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {
                "finding_id": finding_id,
                "can_fix": False,
                "error": "No fix available for this finding.",
            }
        return {"finding_id": finding_id, "can_fix": False, "error": f"HTTP {e.response.status_code}: {e}"}
    except httpx.HTTPError as e:
        return {"finding_id": finding_id, "can_fix": False, "error": str(e)}


# ---------------------------------------------------------------------------
# MCP server definition
# ---------------------------------------------------------------------------

def create_server():
    """Create and return the FastMCP server instance."""
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP(
        "acrqa",
        instructions=(
            "ACR-QA is a multi-tool security analysis platform. "
            "Use acrqa_scan to scan a directory for security issues, "
            "acrqa_explain to get an AI explanation of a specific finding, "
            "and acrqa_fix to get an autofix suggestion."
        ),
    )

    @mcp.tool()
    def acrqa_scan(target_dir: str, repo_name: str = "mcp-scan") -> str:
        """
        Run a full ACR-QA security scan on a local directory.

        Triggers an async Celery scan on the ACR-QA server, polls for completion,
        and returns a summary of findings. Use this before opening a PR to catch
        security issues, code quality problems, and vulnerabilities.

        Args:
            target_dir: Absolute path to the directory to scan.
            repo_name: Optional label for this scan (default: mcp-scan).

        Returns:
            JSON string with findings_count, severity breakdown, and top 5 findings.
        """
        result = _tool_scan(target_dir, repo_name=repo_name)
        return json.dumps(result, indent=2)

    @mcp.tool()
    def acrqa_explain(finding_id: int) -> str:
        """
        Get an AI-generated explanation for a specific finding.

        Returns the LLM explanation generated during the last scan, including
        a description of the vulnerability, its impact, and a code fix example.

        Args:
            finding_id: The numeric ID returned in the scan result's top_findings list.

        Returns:
            JSON string with the explanation text, rule_id, and severity.
        """
        result = _tool_explain(finding_id)
        return json.dumps(result, indent=2)

    @mcp.tool()
    def acrqa_fix(finding_id: int) -> str:
        """
        Get an autofix suggestion (unified diff) for a specific finding.

        Returns a code fix with confidence score. High-confidence fixes (≥80%)
        can be applied automatically; lower-confidence fixes require human review.

        Args:
            finding_id: The numeric ID returned in the scan result's top_findings list.

        Returns:
            JSON string with can_fix, confidence (0-100), diff, and fix_description.
        """
        result = _tool_fix(finding_id)
        return json.dumps(result, indent=2)

    return mcp


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """Run the MCP server via stdio (standard MCP transport)."""
    mcp = create_server()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
