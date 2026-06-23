#!/usr/bin/env python3
"""Slot 6 — optional cheap-LLM precision filter (the only path to top-F2).

The deterministic engine finds candidates at high recall but ~47% precision. This filter sends each
NON-certain finding (the ones dragging precision) to a cheap Groq model with its code context and
asks: is this a real, exploitable vulnerability? Confirmed → kept; rejected → dropped. The
high-precision Confirmed tier (≥2-engine agreement) is always kept unchanged.

This trades the deterministic-$0 wedge for a higher-precision/F2 *mode*, so it is STRICTLY OPT-IN
(`--llm-filter`); the default pipeline stays deterministic. Groq at temperature=0 is near-determinate
(not bit-identical) and costs ~$0.005/finding — orders of magnitude below the agentic LLM scanners
($35–62/benchmark).

Reuses the 4-key round-robin Groq client from llm_security_scanner.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

from groq import Groq, RateLimitError

_GROQ_KEYS = [os.getenv(f"GROQ_API_KEY_{i}") for i in range(1, 5)]
_GROQ_KEYS = [k for k in _GROQ_KEYS if k] or ([os.getenv("GROQ_API_KEY")] if os.getenv("GROQ_API_KEY") else [])
_MODEL = os.getenv("ACRQA_FILTER_MODEL", "llama-3.1-8b-instant")
_call_count = 0

_FILTER_SYSTEM = (
    "You are a precise application-security triager. For each candidate finding you are given the "
    "CWE, a short description, and the exact code with a few lines of context. Decide if it is a "
    "REAL, exploitable vulnerability in THIS code (KEEP) or a false positive / non-exploitable / "
    "test-or-demo-noise (DROP). Be strict: KEEP only when the code genuinely exhibits the "
    "vulnerability. Reply ONLY with a JSON array of objects like "
    '[{"i": 0, "v": "KEEP"}, {"i": 1, "v": "DROP"}] - one per finding index, no prose.'
)


def _call_groq(user_msg: str) -> str:
    global _call_count
    if not _GROQ_KEYS:
        return "[]"
    n = len(_GROQ_KEYS)
    start = _call_count % n
    _call_count += 1
    for attempt in range(n * 3):
        key = _GROQ_KEYS[(start + attempt) % n]
        try:
            resp = Groq(api_key=key).chat.completions.create(
                model=_MODEL,
                messages=[{"role": "system", "content": _FILTER_SYSTEM}, {"role": "user", "content": user_msg}],
                max_tokens=2048,
                temperature=0,
            )
            return resp.choices[0].message.content or "[]"
        except RateLimitError:
            time.sleep(12 * (attempt // n + 1))
        except Exception:
            time.sleep(2)
    return "[]"


def _context(repo: Path, rel_file: str, line: int, radius: int = 4) -> str:
    p = repo / rel_file
    try:
        lines = p.read_text(errors="replace").splitlines()
    except Exception:
        return ""
    lo, hi = max(0, line - radius - 1), min(len(lines), line + radius)
    out = []
    for i in range(lo, hi):
        marker = ">>" if (i + 1) == line else "  "
        out.append(f"{marker}{i + 1}: {lines[i]}")
    return "\n".join(out)


def _parse_verdicts(text: str, n: int) -> dict[int, bool]:
    text = re.sub(r"^```[a-z]*\n?|\n?```$", "", text.strip(), flags=re.MULTILINE)
    keep: dict[int, bool] = {}
    try:
        for obj in json.loads(text):
            keep[int(obj["i"])] = str(obj.get("v", "KEEP")).upper().startswith("K")
    except Exception:
        # Fallback: line-by-line "<idx> KEEP/DROP"
        for m in re.finditer(r"(\d+)\D+(KEEP|DROP)", text, re.IGNORECASE):
            keep[int(m.group(1))] = m.group(2).upper() == "KEEP"
    # Default unseen indices to KEEP (don't silently drop on parse gaps).
    return {i: keep.get(i, True) for i in range(n)}


def filter_findings(findings: list[dict], repo_path: str, batch: int = 20) -> list[dict]:
    """Return findings minus the non-certain ones the LLM judges false. 'certain' tier kept as-is."""
    repo = Path(repo_path)
    # Keep certain (agreement) + firm (syntactically clear) as-is — the LLM only loses recall on
    # those. Judge ONLY the tentative tier (authorization heuristics), which is the real FP source.
    always = [f for f in findings if f.get("confidence") in ("certain", "firm")]
    judge = [f for f in findings if f.get("confidence") == "tentative"]
    kept: list[dict] = list(always)

    for start in range(0, len(judge), batch):
        chunk = judge[start : start + batch]
        prompt_parts = []
        for i, f in enumerate(chunk):
            ctx = _context(repo, f["file"], f.get("line", 0))
            prompt_parts.append(f"[{i}] {f['cwe']} — {f.get('description', '')[:80]}\n{ctx}")
        user_msg = "Candidate findings:\n\n" + "\n\n---\n\n".join(prompt_parts)
        verdicts = _parse_verdicts(_call_groq(user_msg), len(chunk))
        for i, f in enumerate(chunk):
            if verdicts.get(i, True):
                kept.append(f)
    return kept
