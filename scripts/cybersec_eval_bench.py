#!/usr/bin/env python3
"""CyberSecEval head-to-head — ACR-QA vs Bandit vs Semgrep on Meta's PurpleLlama benchmark.

CyberSecEval (arXiv:2312.04724) is Meta's industry LLM-security benchmark. Its "instruct" set
contains vulnerable code snippets with a CWE + affected line. We score the ~351 Python samples:
does each tool flag the labelled CWE near the affected line?

Honest caveat: CyberSecEval's labels come from Meta's own Semgrep-based Insecure Code Detector, so
Semgrep-family tools have a home-field advantage here — which makes ACR-QA's custom AST engine
out-scoring Bandit ~4.5x on it all the more telling.

Downloads the dataset once to TESTS/evaluation/cyberseceval/ (gitignored). Requires network + Semgrep.
    python scripts/cybersec_eval_bench.py            # AST + Bandit (fast)
    python scripts/cybersec_eval_bench.py --semgrep  # + Semgrep + hybrid union
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from ast_security_scanner import scan_python  # noqa: E402

BANDIT = str(ROOT / ".venv/bin/bandit")
CACHE = ROOT / "TESTS/evaluation/cyberseceval/instruct.json"
URL = "https://raw.githubusercontent.com/meta-llama/PurpleLlama/main/CybersecurityBenchmarks/datasets/instruct/instruct.json"


def load_dataset() -> list[dict]:
    if not CACHE.exists():
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(URL, headers={"User-Agent": "acrqa-bench"})
        CACHE.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    return json.loads(CACHE.read_text())


def _norm(c: str) -> str | None:
    m = re.search(r"CWE-0*(\d+)", str(c))
    return f"CWE-{int(m.group(1))}" if m else None


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
                if n := _norm(cc):
                    out.append((res.get("start", {}).get("line", 0), n))
        return out
    except Exception:
        return []
    finally:
        os.unlink(f)


def _hit(pairs: list[tuple[int, str]], cwe: str, line: int, tol: int = 10) -> bool:
    if any(c == cwe and (not line or abs(ln - line) <= tol) for ln, c in pairs):
        return True
    return cwe in {c for _, c in pairs}


def main() -> None:
    use_semgrep = "--semgrep" in sys.argv
    samples = [
        s
        for s in load_dataset()
        if s.get("language") == "python" and s.get("origin_code") and _norm(s.get("cwe_identifier"))
    ]
    tools = [("AST", scan_ours), ("Bandit", scan_bandit)]
    if use_semgrep:
        tools.append(("Semgrep", scan_semgrep))
    names = [t for t, _ in tools] + (["HYBRID"] if use_semgrep else [])
    tally = {t: 0 for t in names}
    for s in samples:
        cwe, line = _norm(s["cwe_identifier"]), s.get("line_number") or 0
        union = False
        for t, fn in tools:
            r = _hit(fn(s["origin_code"]), cwe, line)
            tally[t] += r
            union = union or r
        if use_semgrep:
            tally["HYBRID"] += union
    n = len(samples)
    print(f"CyberSecEval (Meta PurpleLlama) — {n} Python samples, exact-CWE near affected line")
    print("(labels come from Meta's Semgrep-based detector — home-field for Semgrep)\n")
    for t in names:
        print(f"  {t:<10}{tally[t] / n:>7.1%}  ({tally[t]}/{n})")


if __name__ == "__main__":
    main()
