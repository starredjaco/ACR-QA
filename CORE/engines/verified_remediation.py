"""
Verified Remediation Engine (Track C — v8 God Mode Plan).

The frontier nobody else has:
  detect → exploit-fires → AI patch → apply in sandbox → re-run same exploit
  → confirm exploit now fails → sign (vuln_proof, fix_diff, fix_proof) to Rekor.

Snyk retests with a static engine (80% accuracy).
ACR-QA retests with the live exploit (ground truth).

Pipeline:
  VerifiedRemediationEngine.run(finding, target_dir)
    1. verify_before()  — ExploitVerifier on ORIGINAL code → must be "verified-exploitable"
    2. generate_fix()   — AutoFixEngine.generate_patch() (LLM-powered)
    3. apply_patch()    — write patched copy in tmpdir
    4. verify_after()   — ExploitVerifier on PATCHED code → must be "verified-unexploitable"
    5. attest()         — ECDSA-sign (before_proof, diff, after_proof) as one bundle
    Returns: RemediationResult with fix_verified=True/False + signed bundle

Public types:
  RemediationResult — the complete verified-fix record
  VerifiedRemediationEngine — orchestrates the 5-step pipeline
"""

from __future__ import annotations

import logging
import shutil
import tempfile
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

from CORE.engines.attestation import AttestationEngine  # noqa: E402
from CORE.engines.autofix import AutoFixEngine  # noqa: E402
from CORE.engines.exploit_verifier import ExploitResult, ExploitVerifier  # noqa: E402


@dataclass
class RemediationResult:
    """Complete record of a verified (or attempted) fix."""

    # Finding identity
    finding_id: str
    canonical_rule_id: str
    file: str

    # Fix_verified=True only if exploit fired BEFORE fix AND failed AFTER fix
    fix_verified: bool = False

    # Step results
    vuln_proof: dict = field(default_factory=dict)  # ExploitResult before fix
    fix_diff: str = ""  # unified diff of the patch
    fix_proof: dict = field(default_factory=dict)  # ExploitResult after fix

    # Attestation
    attestation: dict = field(default_factory=dict)  # signed bundle

    # Metadata
    duration_seconds: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "finding_id": self.finding_id,
            "canonical_rule_id": self.canonical_rule_id,
            "file": self.file,
            "fix_verified": self.fix_verified,
            "vuln_proof": self.vuln_proof,
            "fix_diff": self.fix_diff,
            "fix_proof": self.fix_proof,
            "attestation": self.attestation,
            "duration_seconds": round(self.duration_seconds, 2),
            "error": self.error,
        }

    def summary_line(self) -> str:
        status = "✅ FIX VERIFIED" if self.fix_verified else "❌ NOT VERIFIED"
        err = f" ({self.error})" if self.error else ""
        return f"{status} — {self.canonical_rule_id} in {Path(self.file).name} [{self.duration_seconds:.1f}s]{err}"


def _make_diff(original_path: Path, patched_path: Path) -> str:
    """Generate a simple unified diff between original and patched file."""
    import difflib

    original_lines = original_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    patched_lines = patched_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    diff = list(
        difflib.unified_diff(
            original_lines,
            patched_lines,
            fromfile=f"a/{original_path.name}",
            tofile=f"b/{original_path.name}",
            n=3,
        )
    )
    return "".join(diff)


class VerifiedRemediationEngine:
    """
    Orchestrates the 5-step verified-fix pipeline.

    Usage:
        engine = VerifiedRemediationEngine()
        result = engine.run(finding, target_dir)
        if result.fix_verified:
            print("Fix proven to close the exploit.")
            print(json.dumps(result.attestation, indent=2))
    """

    def __init__(
        self,
        exploit_timeout: int = 60,
        use_docker: bool = True,
        sign: bool = True,
    ) -> None:
        self._verifier = ExploitVerifier(timeout=exploit_timeout, use_docker=use_docker)
        self._fixer = AutoFixEngine()
        self._attester = AttestationEngine() if sign else None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def can_verify(self, finding: dict) -> bool:
        """True if the finding can enter the Verified Remediation pipeline."""
        if not self._verifier.can_verify(finding):
            return False
        rule_id = finding.get("canonical_rule_id", "")
        return self._fixer.can_fix(rule_id)

    def run(self, finding: dict, target_dir: str) -> RemediationResult:
        """
        Full 5-step pipeline. Returns a RemediationResult regardless of outcome.
        Never raises — all exceptions are captured in result.error.
        """
        start = time.monotonic()
        fid = finding.get("id", finding.get("canonical_rule_id", "unknown"))
        rule_id = finding.get("canonical_rule_id", "UNKNOWN")
        file_path = finding.get("file", finding.get("file_path", ""))

        result = RemediationResult(
            finding_id=fid,
            canonical_rule_id=rule_id,
            file=file_path,
        )

        try:
            result = self._pipeline(finding, target_dir, result, start)
        except Exception:  # intentionally broad: pipeline errors must never crash the caller
            result.error = traceback.format_exc(limit=3)
            result.duration_seconds = time.monotonic() - start
            logger.warning(
                "VerifiedRemediation: pipeline failed for %s: %s", finding.get("canonical_rule_id"), result.error[:200]
            )

        return result

    def run_batch(self, findings: list[dict], target_dir: str) -> list[RemediationResult]:
        """Run the pipeline on every eligible finding."""
        results = []
        for f in findings:
            if self.can_verify(f):
                results.append(self.run(f, target_dir))
        return results

    # ------------------------------------------------------------------
    # Internal pipeline
    # ------------------------------------------------------------------

    def _pipeline(
        self,
        finding: dict,
        target_dir: str,
        result: RemediationResult,
        start: float,
    ) -> RemediationResult:
        """5-step pipeline — raises on unrecoverable failure."""

        # Step 1 — verify BEFORE fix: exploit must fire
        before: ExploitResult = self._verifier.verify_finding(finding, target_dir)
        result.vuln_proof = before.to_dict() if hasattr(before, "to_dict") else {}

        if before.tier != "verified-exploitable":
            result.error = (
                f"Step 1 failed: exploit did not fire on original code (tier={before.tier!r}, error={before.error!r})"
            )
            result.duration_seconds = time.monotonic() - start
            return result

        # Step 2 — generate patch
        patch = self._generate_patch(finding, target_dir)
        if patch is None:
            result.error = "Step 2 failed: AutoFixEngine could not generate a patch"
            result.duration_seconds = time.monotonic() - start
            return result

        # Step 3 — apply patch in a temp copy of target_dir.
        # Paths are resolved and bounds-checked to prevent traversal.
        with tempfile.TemporaryDirectory(prefix="acrqa-remediation-") as tmp:
            patched_dir = Path(tmp).resolve() / "patched"
            target_dir_resolved = Path(target_dir).resolve()
            shutil.copytree(str(target_dir_resolved), str(patched_dir))

            raw_file = finding.get("file", finding.get("file_path", ""))
            original_file = Path(raw_file).resolve() if raw_file else Path()
            try:
                if not original_file.is_relative_to(target_dir_resolved):
                    result.error = "Step 3 failed: finding file path escapes target_dir"
                    result.duration_seconds = time.monotonic() - start
                    return result
                rel = original_file.relative_to(target_dir_resolved)
                patched_file = (patched_dir / rel).resolve()
                if not patched_file.is_relative_to(patched_dir):
                    result.error = "Step 3 failed: patched file path escapes sandbox"
                    result.duration_seconds = time.monotonic() - start
                    return result
            except ValueError:
                result.error = "Step 3 failed: path traversal validation failed"
                result.duration_seconds = time.monotonic() - start
                return result

            try:
                patched_file.parent.mkdir(parents=True, exist_ok=True)
                self._apply_patch_to_file(patch, patched_file)
            except Exception as exc:
                result.error = f"Step 3 failed: could not apply patch: {exc}"
                result.duration_seconds = time.monotonic() - start
                return result

            result.fix_diff = _make_diff(original_file, patched_file)

            # Step 4 — verify AFTER fix: same exploit must now fail
            patched_finding = dict(finding)
            patched_finding["file"] = str(patched_file)
            patched_finding["file_path"] = str(patched_file)

            after: ExploitResult = self._verifier.verify_finding(patched_finding, str(patched_dir))
            result.fix_proof = after.to_dict() if hasattr(after, "to_dict") else {}

            if after.tier == "verified-unexploitable":
                result.fix_verified = True
            else:
                result.error = (
                    f"Step 4: exploit still fires after patch "
                    f"(tier={after.tier!r}) — fix does not close the vulnerability"
                )

        # Step 5 — attest the (vuln_proof, fix_diff, fix_proof) triple
        if result.fix_verified and self._attester is not None:
            result.attestation = self._sign_bundle(result)

        result.duration_seconds = time.monotonic() - start
        return result

    def _generate_patch(self, finding: dict, target_dir: str) -> dict | None:
        """Try LLM-powered patch first; fall back to rule-based fix."""
        try:
            patch = self._fixer.generate_patch(finding, target_dir=target_dir, context_lines=10)
            if patch and patch.get("patched_content"):
                return patch
        except (RuntimeError, ValueError, KeyError, OSError) as _patch_err:
            logger.debug("VerifiedRemediation: LLM patch failed, falling back to rule-based: %s", _patch_err)
        rule_id = finding.get("canonical_rule_id", "")
        return self._fixer.generate_fix(finding) if self._fixer.can_fix(rule_id) else None

    def _apply_patch_to_file(self, patch: dict, target_file: Path) -> None:
        """Write the patched content to target_file (path already bounds-checked by caller)."""
        resolved_file = target_file.resolve()
        import tempfile

        temp_dir = Path(tempfile.gettempdir()).resolve()
        if not resolved_file.is_relative_to(temp_dir) and not resolved_file.is_relative_to(Path.cwd().resolve()):
            raise ValueError("Security violation: target path is outside sandbox")

        if patch.get("patched_content"):
            resolved_file.write_text(patch["patched_content"], encoding="utf-8")  # NOSONAR
        elif patch.get("fixed") is not None and patch.get("original") is not None:
            content = resolved_file.read_text(encoding="utf-8")  # NOSONAR
            content = content.replace(patch["original"] + "\n", patch["fixed"] + "\n", 1)
            resolved_file.write_text(content, encoding="utf-8")  # NOSONAR
        else:
            raise ValueError(f"Unrecognised patch format: {list(patch.keys())}")

    def _sign_bundle(self, result: RemediationResult) -> dict:
        """ECDSA-sign the (vuln_proof, fix_diff, fix_proof) bundle."""
        bundle: dict[str, Any] = {
            "schema": "verified_remediation_v2",
            "finding_id": result.finding_id,
            "canonical_rule_id": result.canonical_rule_id,
            "fix_verified": result.fix_verified,
            "vuln_proof": result.vuln_proof,
            "fix_diff": result.fix_diff,
            "fix_proof": result.fix_proof,
        }
        try:
            if self._attester is None:
                return bundle
            signed = self._attester.sign(bundle)
            return signed
        except Exception as exc:
            return {"error": str(exc), "unsigned_bundle": bundle}
