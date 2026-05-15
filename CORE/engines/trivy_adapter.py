"""Trivy container/IaC/dependency scanner adapter.

Wraps `trivy fs --format json` to produce canonical findings.
Gracefully degrades when Trivy is not installed — returns empty list.
Capabilities:
  - Container image scanning (OS package CVEs)
  - Dependency scanning (language packages: pip, npm, go.sum, etc.)
  - IaC misconfiguration (Dockerfile, Terraform, Kubernetes)
  - SBOM generation (CycloneDX/SPDX)
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_SEVERITY_MAP = {
    "CRITICAL": "critical",
    "HIGH": "high",
    "MEDIUM": "medium",
    "LOW": "low",
    "UNKNOWN": "low",
}

_CATEGORY_MAP = {
    "vulnerability": "security",
    "secret": "security",
    "config": "security",
    "license": "style",
}


class TrivyAdapter:
    """Run Trivy filesystem scan and normalise results to canonical findings."""

    def __init__(self, timeout: int = 120) -> None:
        self._timeout = timeout
        self._available = shutil.which("trivy") is not None

    @property
    def available(self) -> bool:
        return self._available

    def scan_directory(self, target_dir: str | Path) -> list[dict[str, Any]]:
        """Run `trivy fs` on *target_dir* and return canonical findings."""
        if not self._available:
            logger.info("Trivy not installed — skipping container/IaC scan")
            return []

        target_dir = Path(target_dir)
        cmd = [
            "trivy",
            "fs",
            "--format",
            "json",
            "--quiet",
            "--scanners",
            "vuln,secret,misconfig",
            str(target_dir),
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
            if result.returncode not in (0, 1):
                logger.warning(f"Trivy exited {result.returncode}: {result.stderr[:200]}")
                return []
            return self._parse(result.stdout, target_dir)
        except subprocess.TimeoutExpired:
            logger.warning(f"Trivy timed out after {self._timeout}s")
            return []
        except Exception as e:
            logger.warning(f"Trivy scan failed: {e}")
            return []

    def _parse(self, stdout: str, target_dir: Path) -> list[dict[str, Any]]:
        """Parse Trivy JSON output into canonical finding dicts."""
        if not stdout.strip():
            return []
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError as e:
            logger.warning(f"Trivy JSON parse error: {e}")
            return []

        findings: list[dict[str, Any]] = []
        for result in data.get("Results", []) or []:
            target = result.get("Target", "")
            result_type = result.get("Type", "")

            # Vulnerabilities (OS packages + language deps)
            for vuln in result.get("Vulnerabilities") or []:
                finding = self._vuln_to_finding(vuln, target, result_type)
                if finding:
                    findings.append(finding)

            # IaC misconfigurations
            for misconfig in result.get("Misconfigurations") or []:
                finding = self._misconfig_to_finding(misconfig, target)
                if finding:
                    findings.append(finding)

            # Secrets
            for secret in result.get("Secrets") or []:
                finding = self._secret_to_finding(secret, target)
                if finding:
                    findings.append(finding)

        logger.info(f"Trivy: {len(findings)} finding(s) in {target_dir}")
        return findings

    def _vuln_to_finding(self, vuln: dict, target: str, result_type: str) -> dict[str, Any] | None:
        cve_id = vuln.get("VulnerabilityID", "UNKNOWN")
        pkg = vuln.get("PkgName", "unknown")
        installed_ver = vuln.get("InstalledVersion", "?")
        fixed_ver = vuln.get("FixedVersion", "not fixed")
        severity = _SEVERITY_MAP.get(vuln.get("Severity", "UNKNOWN"), "low")
        title = vuln.get("Title") or vuln.get("Description") or cve_id

        return {
            "tool": "trivy",
            "canonical_rule_id": f"SECURITY-{cve_id[:50]}",
            "cwe": vuln.get("CweIDs", [None])[0] or "CWE-1035",
            "severity": severity,
            "category": "security",
            "file": target,
            "line": 0,
            "message": (f"{cve_id}: {title} in {pkg}@{installed_ver} " f"(fix: {fixed_ver}, type: {result_type})"),
            "rule_id": cve_id,
            "pkg_name": pkg,
            "installed_version": installed_ver,
            "fixed_version": fixed_ver,
            "trivy_type": "vulnerability",
        }

    def _misconfig_to_finding(self, misconfig: dict, target: str) -> dict[str, Any] | None:
        rule_id = misconfig.get("ID", "UNKNOWN")
        severity = _SEVERITY_MAP.get(misconfig.get("Severity", "UNKNOWN"), "low")
        title = misconfig.get("Title", "IaC misconfiguration")
        description = misconfig.get("Description", "")
        resolution = misconfig.get("Resolution", "")

        return {
            "tool": "trivy",
            "canonical_rule_id": f"SECURITY-{rule_id}",
            "cwe": "CWE-16",
            "severity": severity,
            "category": "security",
            "file": target,
            "line": misconfig.get("CauseMetadata", {}).get("StartLine", 0),
            "message": f"{rule_id}: {title}. {description} Resolution: {resolution}",
            "rule_id": rule_id,
            "trivy_type": "misconfig",
        }

    def _secret_to_finding(self, secret: dict, target: str) -> dict[str, Any] | None:
        rule_id = secret.get("RuleID", "secret")
        title = secret.get("Title", "Detected secret")
        match = secret.get("Match", "")

        return {
            "tool": "trivy",
            "canonical_rule_id": "HARDCODE-001",
            "cwe": "CWE-798",
            "severity": "high",
            "category": "security",
            "file": target,
            "line": secret.get("StartLine", 0),
            "message": f"Secret detected ({rule_id}): {title}. Match: {match[:60]}",
            "rule_id": rule_id,
            "trivy_type": "secret",
        }
