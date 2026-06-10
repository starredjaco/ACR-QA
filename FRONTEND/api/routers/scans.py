"""Scans router — async scan dispatch via Celery, single-file analysis, quick refresh."""

from __future__ import annotations

import asyncio
import json as json_module
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, status

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from FRONTEND.api.deps import get_current_user
from FRONTEND.api.models import (
    AIDetectRequest,
    AnalyzeFileRequest,
    GitHubScanOut,
    GitHubScanRequest,
    RefreshFindingsRequest,
    ScanJobOut,
    ScanRequest,
    SCAScanRequest,
    SecretsScanRequest,
)

router = APIRouter(prefix="/scans", tags=["scans"])


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ScanJobOut,
    summary="Queue a full repository scan (async)",
)
async def create_scan(body: ScanRequest, user: dict = Depends(get_current_user)):
    """Enqueue an analysis job and return a job_id immediately.
    Poll GET /v1/scans/{job_id} for status.
    """
    from CORE.tasks import run_analysis_task

    task = run_analysis_task.delay(
        target_dir=body.target_dir,
        repo_name=body.repo_name,
        pr_number=body.pr_number,
        limit=body.limit,
    )
    return ScanJobOut(job_id=task.id, status="queued")


@router.get("/{job_id}", response_model=ScanJobOut, summary="Poll scan job status")
async def get_scan_status(job_id: str, user: dict = Depends(get_current_user)):
    """Returns queued | started | completed | failed with result when done."""
    from CORE.tasks import celery_app

    ar = celery_app.AsyncResult(job_id)

    # Celery state → our status vocabulary
    state_map = {
        "PENDING": "queued",
        "STARTED": "started",
        "SUCCESS": "completed",
        "FAILURE": "failed",
        "RETRY": "started",
        "REVOKED": "failed",
    }
    our_status = state_map.get(ar.state, ar.state.lower())

    result = None
    if ar.ready():
        try:
            result = ar.result if ar.successful() else {"error": str(ar.result)}
        except Exception:
            result = {"error": "Could not retrieve result"}

    return ScanJobOut(job_id=job_id, status=our_status, result=result)


@router.post(
    "/iac",
    summary="Run the IaC scanner on a target directory (sync, no DB write)",
)
async def scan_iac(body: dict, user: dict = Depends(get_current_user)):
    """Run the IaC scanner over a target_dir and return findings inline.

    Body: {"target_dir": "<path>"}.
    Returns a list of CanonicalFinding-shaped dicts grouped by provider.
    Read-only; no DB writes — for the demo + a "scan-on-the-fly" UX (v5.0.0 A2).
    """
    target_dir = (body or {}).get("target_dir") or "."
    if not isinstance(target_dir, str):
        return {"error": "target_dir must be a string"}

    # Restrict access to inside the project (defence-in-depth): no absolute
    # paths above CWD, no traversal up via `..`.
    from pathlib import Path as _Path

    requested = _Path(target_dir).expanduser()
    try:
        resolved = requested.resolve(strict=False)
    except (OSError, RuntimeError):
        return {"error": "invalid target_dir"}

    cwd = _Path.cwd().resolve()
    if not str(resolved).startswith(str(cwd)):
        return {"error": "target_dir must live inside the workspace"}

    from CORE.engines.iac_scanner import IaCScanner

    scanner = IaCScanner(target_dir=str(resolved))
    findings = scanner.scan()

    by_provider: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    for f in findings:
        p = f.get("iac_provider") or "unknown"
        s = f.get("severity") or "low"
        by_provider[p] = by_provider.get(p, 0) + 1
        by_severity[s] = by_severity.get(s, 0) + 1

    return {
        "target_dir": str(resolved),
        "total": len(findings),
        "by_provider": by_provider,
        "by_severity": by_severity,
        "findings": findings,
    }


@router.post("/analyze", summary="Analyze a single file snippet (sync, no DB write)")
async def analyze_file(body: AnalyzeFileRequest, user: dict = Depends(get_current_user)):
    """Run Ruff + Vulture + Bandit on a code snippet and return findings inline."""
    findings: list[dict] = []

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(body.content)
        temp_path = f.name

    try:
        # Ruff
        r = await asyncio.to_thread(
            subprocess.run,
            ["ruff", "check", temp_path, "--output-format=json"],
            capture_output=True,
            text=True,
        )
        if r.stdout:
            for item in json_module.loads(r.stdout):
                findings.append(
                    {
                        "line": item.get("location", {}).get("row", 1),
                        "column": item.get("location", {}).get("column", 1),
                        "rule_id": item.get("code", "UNKNOWN"),
                        "severity": "medium" if (item.get("code", "")).startswith("E") else "low",
                        "message": item.get("message", ""),
                        "tool": "ruff",
                    }
                )

        # Vulture
        r = await asyncio.to_thread(
            subprocess.run,
            ["vulture", temp_path, "--min-confidence", "80"],
            capture_output=True,
            text=True,
        )
        for line in r.stdout.strip().split("\n"):
            if line and ":" in line:
                parts = line.split(":")
                if len(parts) >= 3:
                    findings.append(
                        {
                            "line": int(parts[1]) if parts[1].isdigit() else 1,
                            "column": 1,
                            "rule_id": "DEAD-001",
                            "severity": "low",
                            "message": ":".join(parts[2:]).strip(),
                            "tool": "vulture",
                        }
                    )

        # Bandit
        try:
            r = await asyncio.to_thread(
                subprocess.run,
                ["bandit", "-f", "json", "-q", temp_path],
                capture_output=True,
                text=True,
            )
            if r.stdout:
                for issue in json_module.loads(r.stdout).get("results", []):
                    sev = issue.get("issue_severity", "LOW").lower()
                    findings.append(
                        {
                            "line": issue.get("line_number", 1),
                            "column": 1,
                            "rule_id": issue.get("test_id", "B000"),
                            "severity": "high" if sev == "high" else "medium" if sev == "medium" else "low",
                            "message": issue.get("issue_text", ""),
                            "tool": "bandit",
                            "category": "security",
                        }
                    )
        except Exception:
            pass
    finally:
        os.unlink(temp_path)

    return {"success": True, "filename": body.filename, "findings": findings, "total": len(findings)}


@router.post("/refresh", summary="Re-run detection tools and sync DB (no AI explanations)")
async def refresh_findings(body: RefreshFindingsRequest, user: dict = Depends(get_current_user)):
    """Quick refresh: run tools → normalize → store findings without LLM calls."""
    from CORE.engines.normalizer import normalize_all
    from DATABASE.database import Database

    db = Database()
    project_root = Path(__file__).parent.parent.parent.parent

    if not body.skip_detection:
        await asyncio.to_thread(
            subprocess.run,
            ["bash", "TOOLS/run_checks.sh", body.target_dir],
            cwd=str(project_root),
            check=True,
            capture_output=True,
        )

    findings = await asyncio.to_thread(normalize_all, project_root / "DATA" / "outputs")
    run_id = db.create_analysis_run(repo_name=body.repo_name)
    for finding in findings:
        db.insert_finding(run_id, finding.to_dict())
    db.complete_analysis_run(run_id, len(findings))

    from collections import Counter

    cats = dict(Counter(f.category for f in findings))

    return {
        "success": True,
        "run_id": run_id,
        "total_findings": len(findings),
        "categories": cats,
        "message": f"Quick refresh complete — {len(findings)} findings stored.",
    }


@router.post("/secrets", summary="Run secrets detection on a directory")
async def scan_secrets(body: SecretsScanRequest, user: dict = Depends(get_current_user)):
    from CORE.engines.secrets_detector import SecretsDetector

    results = await asyncio.to_thread(SecretsDetector().scan_directory, body.target_dir)
    return {
        "success": True,
        "files_scanned": results["files_scanned"],
        "total_secrets": results["total_secrets"],
        "severity_breakdown": results["severity_breakdown"],
        "secret_types": results["secret_types_found"],
        "findings": results["findings"][:50],
    }


@router.post("/sca", summary="Run SCA (dependency vulnerability) scan")
async def scan_sca(body: SCAScanRequest, user: dict = Depends(get_current_user)):
    from CORE.engines.sca_scanner import SCAScanner

    scanner = SCAScanner(project_dir=body.project_dir)
    results = await asyncio.to_thread(scanner.scan)
    return {
        "success": True,
        "scanner": results["scanner"],
        "total_vulnerabilities": results["total_vulnerabilities"],
        "severity_breakdown": results["severity_breakdown"],
        "vulnerabilities": results["vulnerabilities"],
    }


@router.post("/ai-detection", summary="Run AI-generated code detection")
async def scan_ai_detection(body: AIDetectRequest, user: dict = Depends(get_current_user)):
    import os

    if os.getenv("ACRQA_AI_DETECTION", "1") == "0":
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail="AI detection engine is disabled (ACRQA_AI_DETECTION=0)")
    from CORE.engines.ai_code_detector import AICodeDetector

    detector = AICodeDetector(threshold=body.threshold)
    target = Path(body.target)

    if target.is_file():
        result = await asyncio.to_thread(detector.analyze_file, str(target))
        return {"success": True, "result": result}

    results = await asyncio.to_thread(detector.analyze_directory, str(target))
    return {
        "success": True,
        "total_files": results["total_files"],
        "flagged_files": results["flagged_files"],
        "flagged_percentage": results["flagged_percentage"],
        "files": results["files"][:50],
    }


# ── GitHub/GitLab scan-by-URL ─────────────────────────────────────────────────
_ALLOWED_HOSTS = ("github.com", "gitlab.com", "bitbucket.org")
_CLONE_TIMEOUT = 90  # seconds — generous for large repos on slow links
_MAX_DEPTH = 1  # shallow clone only


@router.post(
    "/github",
    response_model=GitHubScanOut,
    summary="Clone a public GitHub/GitLab repo and scan it (sync)",
)
async def scan_github_repo(
    body: GitHubScanRequest,
    user: dict = Depends(get_current_user),
):
    """Clone a public HTTPS repo URL, run full analysis, return the run summary.

    Security constraints:
    - Only https:// URLs from github.com, gitlab.com, or bitbucket.org
    - Shallow clone (--depth 1) — no full history downloaded
    - 90-second clone timeout
    - Temp dir cleaned up unconditionally on exit
    """
    import re
    import shutil
    import urllib.parse

    from fastapi import HTTPException

    from CORE.main import AnalysisPipeline

    url = body.repo_url.strip()

    # ── Security: validate URL ────────────────────────────────────────────────
    if not url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Only https:// URLs are accepted")

    parsed = urllib.parse.urlparse(url)
    if parsed.hostname not in _ALLOWED_HOSTS:
        raise HTTPException(
            status_code=400,
            detail=f"Only {', '.join(_ALLOWED_HOSTS)} URLs are accepted",
        )

    # Strip credentials from URL (should never be there, but belt-and-suspenders)
    if parsed.username or parsed.password:
        raise HTTPException(status_code=400, detail="Credentials in URL are not accepted")

    # Derive repo_name from the URL path slug if not provided
    slug = re.sub(r"\.git$", "", parsed.path.strip("/").split("/")[-1]) or "repo"
    repo_name = body.repo_name or slug

    # ── Clone ─────────────────────────────────────────────────────────────────
    tmp_dir = tempfile.mkdtemp(prefix="acrqa_clone_")
    try:
        clone_cmd = [
            "git",
            "clone",
            "--depth",
            str(_MAX_DEPTH),
            "--single-branch",
            "--no-tags",
            "--filter=blob:limit=5m",  # skip blobs > 5 MB (binaries, large assets)
            url,
            tmp_dir,
        ]
        proc = await asyncio.wait_for(
            asyncio.to_thread(
                subprocess.run,
                clone_cmd,
                capture_output=True,
                text=True,
            ),
            timeout=_CLONE_TIMEOUT,
        )
        if proc.returncode != 0:
            raise HTTPException(
                status_code=422,
                detail=f"git clone failed: {proc.stderr.strip()[:300]}",
            )

        # ── Scan ──────────────────────────────────────────────────────────────
        pipeline = AnalysisPipeline(target_dir=tmp_dir)
        run_id = await asyncio.to_thread(
            pipeline.run,
            repo_name=repo_name,
            limit=0,  # no-ai for speed; findings still persisted to DB
        )

        # ── Return summary ────────────────────────────────────────────────────
        db = pipeline.db
        summary = db.get_run_summary(run_id) or {}
        attestation = db.get_attestation(run_id)
        return GitHubScanOut(
            run_id=run_id,
            repo_name=repo_name,
            status="completed",
            total_findings=summary.get("findings_count", 0),
            high_count=summary.get("high_severity_count", 0),
            medium_count=summary.get("medium_severity_count", 0),
            low_count=summary.get("low_severity_count", 0),
            attestation_key_id=attestation.get("key_id") if attestation else None,
        )

    except TimeoutError as exc:
        raise HTTPException(status_code=408, detail=f"Clone timed out after {_CLONE_TIMEOUT}s") from exc

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
