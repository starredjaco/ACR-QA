"""
Verification data loop router — exposes the exploit-verification log (Moat #1).

GET /v1/verification/stats   — aggregate counts by verdict
GET /v1/verification/log     — paginated verification history
"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, Depends, Query

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from DATABASE.database import Database
from FRONTEND.api.deps import get_current_user, get_db

router = APIRouter(prefix="/verification", tags=["verification"])


@router.get("/stats", summary="Verification data-loop aggregate stats")
async def verification_stats(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """
    Returns aggregate statistics over the verification_log table.

    This is the health dashboard for Moat #1 — the proprietary exploit-verification
    training corpus. As design partners use ACR-QA, every exploit verdict accumulates
    here as labeled ground truth.
    """
    stats = db.get_verification_stats()
    verified = stats["by_verdict"].get("verified-exploitable", {}).get("count", 0)
    unexploitable = stats["by_verdict"].get("verified-unexploitable", {}).get("count", 0)
    unverified = stats["by_verdict"].get("unverified", {}).get("count", 0)
    errors = stats["by_verdict"].get("error", {}).get("count", 0)
    total = stats["total"]
    exploit_rate = round(verified / total * 100, 1) if total > 0 else 0.0
    return {
        "total": total,
        "verified_exploitable": verified,
        "verified_unexploitable": unexploitable,
        "unverified": unverified,
        "errors": errors,
        "exploit_rate_pct": exploit_rate,
        "by_verdict": stats["by_verdict"],
    }


@router.get("/log", summary="Paginated verification history (Moat #1 data loop)")
async def verification_log(
    verdict: str | None = Query(
        None, description="Filter by verdict: verified-exploitable | verified-unexploitable | unverified | error"
    ),
    canonical_rule_id: str | None = Query(None, description="Filter by canonical rule ID"),
    limit: int = Query(50, ge=1, le=500),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """
    Returns the raw verification log entries, newest first.

    Each row is one exploit-verifier verdict: finding fingerprint, rule, category,
    verdict (verified-exploitable / verified-unexploitable / unverified / error),
    payload used, duration, and target repo.

    This data accumulates as ACR-QA runs on real codebases and becomes the training
    corpus for a future proprietary verifier model.
    """
    rows = db.get_verification_log(
        verdict=verdict,
        canonical_rule_id=canonical_rule_id,
        limit=limit,
    )
    return {
        "count": len(rows),
        "entries": [
            {
                "id": r["id"],
                "finding_fingerprint": r.get("finding_fingerprint"),
                "canonical_rule_id": r.get("canonical_rule_id"),
                "category": r.get("category"),
                "verdict": r.get("verdict"),
                "payload": r.get("payload"),
                "duration_seconds": r.get("duration_seconds"),
                "target_repo": r.get("target_repo"),
                "created_at": str(r.get("created_at", "")),
            }
            for r in rows
        ],
    }
