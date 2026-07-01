#!/usr/bin/env python3
"""Real-CVE head-to-head — ACR-QA vs Bandit vs Semgrep on the CVE recall battery.

The battery (`TESTS/evaluation/cve_recall/*.yml`) pins real CVEs in real, popular Python packages
(Django, GitPython, PyJWT, Pillow, ...) with the affected file + lines + CWE at the vulnerable
version. This fetches each affected file at its vulnerable tag from GitHub raw (no full clone) and
checks whether each tool flags the CVE's CWE within ±15 lines of the affected location.

A tool "detects" a CVE if it reports the labelled CWE near the affected line. The ACR-QA HYBRID is
the union of its AST engine + Bandit + Semgrep — what the product actually runs.

Requires network (GitHub raw). Run: python scripts/cve_recall_bench.py
"""

from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from ast_security_scanner import scan_python  # noqa: E402

BANDIT = str(ROOT / ".venv/bin/bandit")
BATTERY = ROOT / "TESTS/evaluation/cve_recall"


def raw_url(repo_url: str, tag: str, path: str) -> str | None:
    m = re.search(r"github\.com/([^/]+)/([^/.]+)", repo_url or "")
    if not m or not path:
        return None
    tag = tag.split("==")[-1] if "==" in tag else tag  # e.g. "pkg==0.3.8" -> "0.3.8"
    return f"https://raw.githubusercontent.com/{m.group(1)}/{m.group(2)}/{tag}/{path}"


def fetch(url: str) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "acrqa-bench"})
        return urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
    except Exception:
        return None


def _hit(pairs: list[tuple[int, str]], cwe: str, lines: list[int], tol: int = 15) -> bool:
    anchors = lines or [0]
    if any(c == cwe and any(abs(ln - a) <= tol for a in anchors) for ln, c in pairs):
        return True
    return not lines and cwe in {c for _, c in pairs}


def _tmp(code: str) -> Path:
    f = Path(tempfile.mktemp(suffix=".py"))
    f.write_text(code)
    return f


def scan_ours(code: str) -> list[tuple[int, str]]:
    f = _tmp(code)
    try:
        return [(x["line"], x["cwe"]) for x in scan_python(f)]
    except Exception:
        return []
    finally:
        os.unlink(f)


def scan_bandit(code: str) -> list[tuple[int, str]]:
    f = _tmp(code)
    try:
        r = subprocess.run([BANDIT, "-f", "json", "-q", str(f)], capture_output=True, text=True, timeout=30)
        d = json.loads(r.stdout or "{}")
        return [
            (res.get("line_number", 0), f"CWE-{c}")
            for res in d.get("results", [])
            if (c := (res.get("issue_cwe") or {}).get("id"))
        ]
    except Exception:
        return []
    finally:
        os.unlink(f)


def scan_semgrep(code: str) -> list[tuple[int, str]]:
    f = _tmp(code)
    try:
        r = subprocess.run(
            ["semgrep", "--config", "p/python", str(f), "--json", "--quiet", "--no-autofix"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        d = json.loads(r.stdout or "{}")
        out = []
        for res in d.get("results", []):
            cf = (res.get("extra", {}).get("metadata", {}) or {}).get("cwe") or []
            for cc in [cf] if isinstance(cf, str) else cf:
                if m := re.search(r"CWE-0*(\d+)", str(cc)):
                    out.append((res.get("start", {}).get("line", 0), f"CWE-{int(m.group(1))}"))
        return out
    except Exception:
        return []
    finally:
        os.unlink(f)


def main() -> None:
    cves = [yaml.safe_load(Path(f).read_text()) for f in sorted(glob.glob(str(BATTERY / "*.yml")))]
    tallies = {"AST": 0, "Bandit": 0, "Semgrep": 0, "HYBRID": 0}
    total = 0
    print(f"CVE recall battery — {len(cves)} real CVEs in real packages (exact-CWE within +/-15 lines)\n")
    print(f"{'CVE':<18}{'project':<14}{'CWE':<10}{'AST':>5}{'Bandit':>7}{'Semgrep':>8}{'HYBRID':>8}")
    print("-" * 72)
    for c in cves:
        cwe = c.get("cwe")
        code = fetch(
            raw_url(c.get("repo_url", ""), str(c.get("vuln_version_tag", "")), c.get("affected_file", "")) or ""
        )
        if not code:
            print(f"{c['cve_id']:<18}{str(c.get('project'))[:13]:<14}{str(cwe):<10}{'  fetch-fail':>20}")
            continue
        total += 1
        lines = c.get("affected_lines") or []
        res = {
            "AST": _hit(scan_ours(code), cwe, lines),
            "Bandit": _hit(scan_bandit(code), cwe, lines),
            "Semgrep": _hit(scan_semgrep(code), cwe, lines),
        }
        res["HYBRID"] = any(res.values())
        for k, v in res.items():
            tallies[k] += v
        cells = "".join(
            f"{'Y' if res[k] else '-':>{w}}" for k, w in (("AST", 5), ("Bandit", 7), ("Semgrep", 8), ("HYBRID", 8))
        )
        print(f"{c['cve_id']:<18}{str(c.get('project'))[:13]:<14}{str(cwe):<10}{cells}")
    print("-" * 72)
    if total:
        cells = "".join(
            f"{f'{tallies[k]}/{total}':>{w}}" for k, w in (("AST", 5), ("Bandit", 7), ("Semgrep", 8), ("HYBRID", 8))
        )
        print(f"{'RECALL (of ' + str(total) + ' fetched)':<42}{cells}")
        print(
            f"\nACR-QA HYBRID {tallies['HYBRID'] / total:.0%}  vs  Bandit {tallies['Bandit'] / total:.0%}  vs  Semgrep {tallies['Semgrep'] / total:.0%}"
        )


if __name__ == "__main__":
    main()
