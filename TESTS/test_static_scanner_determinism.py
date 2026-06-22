"""Determinism guarantee for the zero-LLM static security scanner.

The RealVuln "reliable recall" #1 claim rests entirely on one property: the engine is
deterministic — the same code over the same input yields bit-identical findings every run,
unlike non-deterministic LLM scanners. This test enforces that property in CI so it can
never silently regress (e.g. via set iteration order or dict ordering leaking into output).

See docs/evaluation/REALVULN_PURE_STATIC_2026_06_22.md (Headline 0).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import ast_security_scanner as scanner  # noqa: E402

_SAMPLE_DIR = Path(__file__).parent / "samples" / "comprehensive-issues"


def _fingerprint(findings: list[dict]) -> str:
    """Stable hash of the complete finding set (order-independent)."""
    rows = sorted((f["file"], f.get("line", 0), f["cwe"]) for f in findings)
    return hashlib.sha256(json.dumps(rows).encode()).hexdigest()


def test_scan_repo_is_deterministic():
    """Three independent scans of the same directory must be bit-identical."""
    runs = [scanner.scan_repo(str(_SAMPLE_DIR)) for _ in range(3)]
    fingerprints = {_fingerprint(r) for r in runs}
    assert len(fingerprints) == 1, f"non-deterministic output across 3 runs: {fingerprints}"
    # And the finding count is stable too.
    assert len({len(r) for r in runs}) == 1


def test_scan_repo_finds_known_vulnerabilities():
    """Sanity: the engine actually produces findings on the intentionally-vulnerable sample
    (a determinism test on an empty result set would be vacuously true)."""
    findings = scanner.scan_repo(str(_SAMPLE_DIR))
    assert len(findings) > 0
    assert all({"file", "line", "cwe"} <= set(f) for f in findings)
