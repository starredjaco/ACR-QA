"""TruffleHog verified secrets detector adapter.

Wraps `trufflehog filesystem --json` to produce canonical findings.
Gracefully degrades when TruffleHog is not installed — falls back to the
existing regex-based SecretsDetector.

TruffleHog advantage over regex-only: it actively validates detected
credentials (e.g., probes the GitHub API to verify a token is live),
dramatically reducing false positives from revoked/test keys.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TruffleHogAdapter:
    """Run TruffleHog filesystem scan and normalise results."""

    def __init__(self, timeout: int = 120, verified_only: bool = False) -> None:
        self._timeout = timeout
        self._verified_only = verified_only
        self._available = shutil.which("trufflehog") is not None

    @property
    def available(self) -> bool:
        return self._available

    def scan_directory(self, target_dir: str | Path) -> list[dict[str, Any]]:
        """Run TruffleHog on *target_dir* and return canonical findings."""
        if not self._available:
            logger.info("TruffleHog not installed — falling back to regex secrets detector")
            return []

        target_dir = Path(target_dir)
        cmd = [
            "trufflehog",
            "filesystem",
            "--json",
            "--no-update",
            str(target_dir),
        ]
        if self._verified_only:
            cmd.append("--only-verified")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
            return self._parse(result.stdout, target_dir)
        except subprocess.TimeoutExpired:
            logger.warning(f"TruffleHog timed out after {self._timeout}s")
            return []
        except Exception as e:
            logger.warning(f"TruffleHog scan failed: {e}")
            return []

    def _parse(self, stdout: str, target_dir: Path) -> list[dict[str, Any]]:
        """Parse TruffleHog NDJSON output (one JSON object per line)."""
        findings: list[dict[str, Any]] = []
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            finding = self._item_to_finding(item, target_dir)
            if finding:
                findings.append(finding)
        logger.info(f"TruffleHog: {len(findings)} secret(s) in {target_dir}")
        return findings

    def _item_to_finding(self, item: dict, target_dir: Path) -> dict[str, Any] | None:
        detector = item.get("DetectorName", "unknown")
        verified = item.get("Verified", False)
        raw = item.get("Raw", "") or ""
        source_meta = item.get("SourceMetadata", {}) or {}
        data = source_meta.get("Data", {}) or {}
        filesystem = data.get("Filesystem", {}) or {}

        file_path = filesystem.get("file", "unknown")
        line = filesystem.get("line", 0)

        # Severity escalation: verified = high, unverified = medium
        severity = "high" if verified else "medium"
        verified_str = "VERIFIED LIVE" if verified else "unverified"

        # Mask the raw secret (only show first 6 chars)
        masked = raw[:6] + "***" if len(raw) > 6 else "***"

        return {
            "tool": "trufflehog",
            "canonical_rule_id": "HARDCODE-001",
            "cwe": "CWE-798",
            "severity": severity,
            "category": "security",
            "file": file_path,
            "line": line,
            "message": (f"{verified_str} secret detected — type: {detector}. " f"Credential starts with: {masked}"),
            "rule_id": f"trufflehog-{detector.lower()}",
            "detector": detector,
            "verified": verified,
        }
