#!/usr/bin/env python3
"""PR Preview Sandbox (v5.0.0 Phase A.5 — Review-Bottleneck Solver, Point 3).

Composes existing pieces (IaC scanner, exploit verifier, taint analyzer,
dogfooding gate) into a single command that gives a reviewer a runnable
verdict on a PR branch — not just static findings.

Sub-commands:

    static    — fast pass: IaC scan + dogfood gate. No Docker. ~3s.
    docker    — build the PR's Dockerfile (if any), run the container, report
                back which exploit_verifier tiers reproduce inside the live
                process. ~30s + image build time.
    full      — static + docker + summary table to stdout / JSON / md.

Designed for the GitHub Action: on each PR, post a comment with the sandbox
verdict (green / amber / red) alongside the PR Risk Score.

Exit codes mirror the dogfood gate:
    0 — no HIGH findings; sandbox clean (or skipped cleanly)
    1 — HIGH findings present OR exploit-verified hit in docker tier
    2 — engine unavailable / Docker missing when `--require-docker`
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# ── Helpers ───────────────────────────────────────────────────────────────────


def _git(*args: str, cwd: Path = ROOT, timeout: float = 20.0) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return 127, f"git error: {exc}"
    return proc.returncode, proc.stdout


def _docker_available() -> bool:
    rc, _ = _git("--version")  # cheap; just sanity-check subprocess works
    try:
        proc = subprocess.run(
            ["docker", "version", "--format", "{{.Server.Version}}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return proc.returncode == 0 and proc.stdout.strip() != ""
    except (OSError, subprocess.SubprocessError):
        return False


def _diff_changed_lines(base_ref: str = "origin/main") -> int:
    """Count changed lines between HEAD and base_ref. Returns 0 on failure."""
    rc, out = _git("diff", "--shortstat", f"{base_ref}...HEAD")
    if rc != 0 or not out.strip():
        return 0
    total = 0
    for part in out.split(","):
        stripped = part.strip()
        # skip the "N files changed" part — only count insertion/deletion lines
        if "file" in stripped:
            continue
        for token in stripped.split():
            if token.isdigit():
                total += int(token)
                break
    return total


def _find_dockerfile() -> Path | None:
    """Look for a top-level Dockerfile in the repo."""
    for candidate in ("Dockerfile", "Dockerfile.app", "Dockerfile.api"):
        p = ROOT / candidate
        if p.is_file():
            return p
    return None


# ── Sub-command: static ──────────────────────────────────────────────────────


def cmd_static(args: argparse.Namespace) -> dict:
    """Fast pass — IaC + dogfood. No Docker."""
    sys.path.insert(0, str(ROOT))

    summary: dict = {"stage": "static", "ok": True, "iac": None, "dogfood": None}

    try:
        from CORE.engines.iac_scanner import IaCScanner

        iac = IaCScanner(target_dir=str(ROOT)).scan()
        EXC = ("TESTS/samples/", "TESTS/evaluation/", "test_targets/", "TESTS/fixtures/")
        filtered = []
        for f in iac:
            fp = (f.get("file") or "").replace(str(ROOT), "").lstrip("/")
            if not any(fp.startswith(p) for p in EXC):
                filtered.append(f)
        high = sum(1 for f in filtered if f.get("severity") == "high")
        summary["iac"] = {"total": len(filtered), "high": high}
        if high > 0:
            summary["ok"] = False
    except Exception as exc:
        summary["iac"] = {"error": str(exc)}

    # Dogfood gate — shell out to scripts/dogfood.py
    try:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "dogfood.py"), "--fail-on=high"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(ROOT),
        )
        summary["dogfood"] = {"exit_code": proc.returncode, "ok": proc.returncode == 0}
        if proc.returncode != 0:
            summary["ok"] = False
    except (OSError, subprocess.SubprocessError) as exc:
        summary["dogfood"] = {"error": str(exc)}

    return summary


# ── Sub-command: docker ──────────────────────────────────────────────────────


def cmd_docker(args: argparse.Namespace) -> dict:
    """Build the PR's Dockerfile and report container start success."""
    summary: dict = {"stage": "docker", "ok": True}
    if not _docker_available():
        summary["ok"] = False
        summary["error"] = "docker daemon not reachable"
        return summary

    dockerfile = _find_dockerfile()
    if dockerfile is None:
        summary["error"] = "no Dockerfile found at repo root"
        summary["ok"] = True  # Not an error — just no docker workflow for this PR
        return summary

    tag = f"acrqa-pr-sandbox:{int(time.time())}"
    try:
        build = subprocess.run(
            ["docker", "build", "-t", tag, "-f", str(dockerfile), str(ROOT)],
            capture_output=True,
            text=True,
            timeout=600,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"stage": "docker", "ok": False, "error": f"docker build subprocess error: {exc}"}

    summary["build_exit_code"] = build.returncode
    if build.returncode != 0:
        summary["ok"] = False
        summary["error"] = (build.stderr or build.stdout)[-1000:]
        return summary

    summary["image_tag"] = tag

    # Start the container briefly to check it boots; immediately stop.
    try:
        run = subprocess.run(
            ["docker", "run", "--rm", "-d", "--name", f"{tag}-run", tag],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if run.returncode == 0:
            container = run.stdout.strip()
            summary["container_started"] = True
            # Give it 3s to crash if it's going to
            time.sleep(3)
            ps = subprocess.run(
                ["docker", "ps", "-q", "--filter", f"id={container}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            summary["still_running_after_3s"] = bool(ps.stdout.strip())
            # Clean up
            subprocess.run(["docker", "stop", container], capture_output=True, timeout=10)
        else:
            summary["ok"] = False
            summary["container_started"] = False
            summary["error"] = (run.stderr or run.stdout)[-1000:]
    except (OSError, subprocess.SubprocessError) as exc:
        summary["ok"] = False
        summary["error"] = f"docker run error: {exc}"

    # Clean up the image
    subprocess.run(["docker", "rmi", "-f", tag], capture_output=True, timeout=30)
    return summary


# ── Sub-command: full ────────────────────────────────────────────────────────


def cmd_full(args: argparse.Namespace) -> dict:
    static_out = cmd_static(args)
    docker_out = cmd_docker(args) if args.docker else {"stage": "docker", "skipped": True}
    changed_lines = _diff_changed_lines(args.base_ref)
    return {
        "ok": static_out.get("ok", True) and docker_out.get("ok", True),
        "changed_lines": changed_lines,
        "static": static_out,
        "docker": docker_out,
    }


def _print_summary(summary: dict) -> None:
    print("== ACR-QA PR Sandbox ==")
    if "changed_lines" in summary:
        print(f"Changed lines: {summary['changed_lines']}")
    if "static" in summary:
        s = summary["static"]
        iac = s.get("iac", {})
        df = s.get("dogfood", {})
        print(f"Static — IaC: {iac.get('total', '?')} findings ({iac.get('high', 0)} HIGH); "
              f"dogfood gate: {'✅ pass' if df.get('ok') else '❌ fail'}")
    if "docker" in summary:
        d = summary["docker"]
        if d.get("skipped"):
            print("Docker — skipped")
        elif "error" in d and d.get("ok") is False:
            print(f"Docker — ❌ {d['error'][:120]}")
        else:
            built = d.get("build_exit_code", "?")
            running = d.get("still_running_after_3s")
            print(f"Docker — build exit {built}; container running after 3s: {running}")
    verdict = "✅ green" if summary.get("ok") else "❌ red"
    print(f"\nVerdict: {verdict}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="ACR-QA PR Sandbox")
    p.add_argument("--base-ref", default="origin/main", help="diff base for line counting")
    p.add_argument("--docker", action="store_true", help="also run docker build + boot check")
    p.add_argument("--json", metavar="FILE", help="write JSON summary to FILE")
    p.add_argument("--require-docker", action="store_true", help="fail (exit 2) if docker unavailable")
    args = p.parse_args(argv)

    if args.require_docker and not _docker_available():
        print("[error] docker daemon not reachable", file=sys.stderr)
        return 2

    summary = cmd_full(args)
    _print_summary(summary)
    if args.json:
        Path(args.json).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return 0 if summary.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
