#!/usr/bin/env python3
"""SecurityEval head-to-head — independent generalization check (not RealVuln).

SecurityEval (arXiv:2108.09293, `TESTS/evaluation/securityeval/dataset.jsonl`) is 121 CWE-labeled
vulnerable Python samples spanning 69 CWE categories. The AST engine was built for RealVuln and never
tuned on this, so it is a genuine out-of-distribution test. Every sample is vulnerable, so we report:

  * detect-any — the tool flagged some security issue on the sample (did it notice it's vulnerable?)
  * exact-CWE  — the tool flagged the sample's labelled CWE

for ACR-QA's AST engine, Bandit, Semgrep, and the ACR-QA hybrid (the union — what the product runs).

    python scripts/securityeval_bench.py            # AST + Bandit (fast)
    python scripts/securityeval_bench.py --semgrep  # + Semgrep + hybrid union (slower)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from ast_security_scanner import scan_python  # noqa: E402

DATASET = ROOT / "TESTS/evaluation/securityeval/dataset.jsonl"
BANDIT = str(ROOT / ".venv/bin/bandit")


def _norm(cwe: str) -> str | None:
    m = re.search(r"CWE-0*(\d+)", str(cwe))
    return f"CWE-{int(m.group(1))}" if m else None


def _tmp(code: str) -> Path:
    f = Path(tempfile.mktemp(suffix=".py"))
    f.write_text(code)
    return f


def scan_ours(code: str) -> set[str]:
    f = _tmp(code)
    try:
        return {x["cwe"] for x in scan_python(f)}
    except Exception:
        return set()
    finally:
        os.unlink(f)


def scan_bandit(code: str) -> set[str]:
    f = _tmp(code)
    try:
        r = subprocess.run([BANDIT, "-f", "json", "-q", str(f)], capture_output=True, text=True, timeout=30)
        d = json.loads(r.stdout or "{}")
        return {c for res in d.get("results", []) if (c := _norm(f"CWE-{(res.get('issue_cwe') or {}).get('id')}"))}
    except Exception:
        return set()
    finally:
        os.unlink(f)


def scan_semgrep(code: str) -> set[str]:
    f = _tmp(code)
    try:
        r = subprocess.run(
            ["semgrep", "--config", "p/python", str(f), "--json", "--quiet", "--no-autofix"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        d = json.loads(r.stdout or "{}")
        out: set[str] = set()
        for res in d.get("results", []):
            cf = (res.get("extra", {}).get("metadata", {}) or {}).get("cwe") or []
            for c in [cf] if isinstance(cf, str) else cf:
                if n := _norm(c):
                    out.add(n)
        return out
    except Exception:
        return set()
    finally:
        os.unlink(f)


def main() -> None:
    use_semgrep = "--semgrep" in sys.argv
    samples = [json.loads(line) for line in DATASET.read_text().splitlines() if line.strip()]
    tools = [("ACR-QA (AST)", scan_ours), ("Bandit", scan_bandit)]
    if use_semgrep:
        tools.append(("Semgrep", scan_semgrep))
    names = [t for t, _ in tools] + (["ACR-QA hybrid"] if use_semgrep else [])
    stats = {t: {"det": 0, "cwe": 0} for t in names}

    for s in samples:
        expected = _norm(s["ID"])
        union: set[str] = set()
        for t, fn in tools:
            res = fn(s["Insecure_code"])
            union |= res
            stats[t]["det"] += 1 if res else 0
            stats[t]["cwe"] += 1 if expected in res else 0
        if use_semgrep:
            stats["ACR-QA hybrid"]["det"] += 1 if union else 0
            stats["ACR-QA hybrid"]["cwe"] += 1 if expected in union else 0

    n = len(samples)
    print(f"SecurityEval — {n} vulnerable Python samples (independent of RealVuln, never tuned on)\n")
    print(f"{'tool':<16}{'detect-any':>12}{'exact-CWE':>12}")
    print("-" * 42)
    for t in names:
        print(f"{t:<16}{stats[t]['det'] / n:>11.1%}{stats[t]['cwe'] / n:>12.1%}")


if __name__ == "__main__":
    main()
