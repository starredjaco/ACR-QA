"""
ACR-QA Second Opinion engine (v5.0.0 Phase A.5 — Review-Bottleneck Solver, Point 2).

Two *different* LLM providers independently classify each finding as TP / FP /
NEEDS_REVIEW. When they agree the verdict is high-confidence; when they
disagree the finding is flagged for human review with both opinions surfaced.

Default pairing (the "free way"):
    Provider A: Groq Llama 3.3-70B-versatile   (already in use)
    Provider B: Ollama (local; default qwen2.5-coder:1.5b)

Ollama runs locally, so the second opinion is free at zero recurring cost.
If Ollama isn't reachable, we **don't** fail the finding — we mark
`second_opinion_skipped` with a reason and return the primary verdict.

Why two *different* models?
    Same-model self-review has correlated failure modes — the same training
    distribution yields the same blind spots. Asking a structurally
    different model the same question lowers the chance of correlated
    error on a per-finding basis. This is the same principle behind
    inter-rater agreement studies in empirical SE (Cohen's κ).
"""

from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import asdict, dataclass

import httpx

logger = logging.getLogger(__name__)


VALID_VERDICTS = ("TP", "FP", "NEEDS_REVIEW")

_VERDICT_PROMPT_TEMPLATE = """You are reviewing a static-analysis finding from a security tool.

## Finding
- rule: {rule_id} ({severity})
- location: {file_path}:{line_number}
- message: {message}

## Code snippet
```
{snippet}
```

Classify this finding as exactly ONE of:
- TP (true positive — this is a real issue that should be fixed)
- FP (false positive — this is spurious or out of scope)
- NEEDS_REVIEW (cannot decide without more context)

Respond with the single token TP, FP, or NEEDS_REVIEW on its own line.
Then add one short reason (≤ 20 words). Do not invent CVE numbers."""


# ── Result type ───────────────────────────────────────────────────────────────


@dataclass
class SecondOpinionResult:
    finding_id: int
    primary_provider: str
    primary_verdict: str
    primary_reason: str
    secondary_provider: str
    secondary_verdict: str
    secondary_reason: str
    agreement: bool
    confidence_delta: int  # +X when agree, 0 when skipped, -X when disagree
    skipped_reason: str | None = None
    latency_ms: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


# ── Parsing ───────────────────────────────────────────────────────────────────


_VERDICT_RE = re.compile(r"\b(TP|FP|NEEDS_REVIEW)\b", re.IGNORECASE)


def parse_verdict(text: str) -> tuple[str, str]:
    """Extract (verdict, reason) from raw LLM output.

    Returns (verdict, reason). Verdict is upper-case; falls back to NEEDS_REVIEW
    if no recognisable token is present. Reason is the first non-empty line that
    isn't the verdict itself, trimmed to 200 chars.
    """
    if not isinstance(text, str):
        return "NEEDS_REVIEW", ""
    m = _VERDICT_RE.search(text)
    verdict = m.group(1).upper() if m else "NEEDS_REVIEW"
    if verdict == "NEEDS_REVIEW":
        # Catch the spaced form too: "needs review"
        if re.search(r"\bneeds[\s_-]?review\b", text, re.IGNORECASE):
            verdict = "NEEDS_REVIEW"
    reason_lines = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln or _VERDICT_RE.fullmatch(ln) or ln.upper() in VALID_VERDICTS:
            continue
        reason_lines.append(ln)
    reason = " ".join(reason_lines)[:200].strip()
    return verdict, reason


def _build_prompt(finding: dict) -> str:
    return _VERDICT_PROMPT_TEMPLATE.format(
        rule_id=finding.get("canonical_rule_id") or finding.get("rule_id") or "UNKNOWN",
        severity=finding.get("canonical_severity") or finding.get("severity") or "unknown",
        file_path=finding.get("file_path") or "<unknown>",
        line_number=finding.get("line_number") or "?",
        message=(finding.get("message") or "")[:400],
        snippet=((finding.get("code_snippet") or finding.get("evidence", {}).get("snippet") or "")[:1200] or ""),
    )


# ── Provider calls ────────────────────────────────────────────────────────────


class _OllamaUnavailableError(RuntimeError):
    pass


class _GeminiUnavailableError(RuntimeError):
    pass


def _call_gemini(prompt: str, timeout: float = 10.0) -> str:
    """One-shot Gemini API call (free tier: gemini-1.5-flash).

    Requires GEMINI_API_KEY env var (Google AI Studio — free, no card).
    Falls back to _GeminiUnavailableError so the engine degrades gracefully.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
    if not api_key:
        raise _GeminiUnavailableError("GEMINI_API_KEY not set")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/" f"gemini-1.5-flash:generateContent?key={api_key}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 80,
        },
    }
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=body)
    except httpx.HTTPError as exc:
        raise _GeminiUnavailableError(f"http error: {exc}") from exc
    if resp.status_code != 200:
        raise _GeminiUnavailableError(f"status {resp.status_code}: {resp.text[:200]}")
    try:
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, ValueError) as exc:
        raise _GeminiUnavailableError(f"malformed response: {exc}") from exc


def _call_ollama(prompt: str, model: str | None = None, timeout: float = 6.0) -> str:
    """One-shot Ollama call. Raises _OllamaUnavailableError on connection failure."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    url = f"{base_url}/v1/chat/completions"
    body = {
        "model": model or os.getenv("ACRQA_OLLAMA_MODEL", "qwen2.5-coder:1.5b"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 80,
        "stream": False,
    }
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=body)
    except httpx.HTTPError as exc:
        raise _OllamaUnavailableError(f"http error: {exc}") from exc
    if resp.status_code != 200:
        raise _OllamaUnavailableError(f"status {resp.status_code}")
    try:
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except (KeyError, ValueError, IndexError) as exc:
        raise _OllamaUnavailableError(f"malformed response: {exc}") from exc


def _call_groq(prompt: str, key_pool=None) -> str:
    """Single-shot Groq call via the existing KeyPool. Returns the content string."""
    if key_pool is None:
        from CORE.engines.explainer import KeyPool

        key_pool = KeyPool()
    if not key_pool.has_keys:
        raise RuntimeError("No Groq key configured — primary provider unavailable")
    client = key_pool.next_client()
    completion = client.chat.completions.create(
        model=os.getenv("ACRQA_CHAT_MODEL", "llama-3.3-70b-versatile"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=80,
        stream=False,
    )
    try:
        return completion.choices[0].message.content or ""
    except (AttributeError, IndexError):
        return ""


# ── Public API ────────────────────────────────────────────────────────────────


class SecondOpinionEngine:
    """Two-provider classifier.

    Default: Groq (primary) + Gemini (secondary).
    Falls back to Ollama if Gemini key is absent, then skips secondary entirely.

    Provider priority for secondary:
        1. gemini   — free tier (Google AI Studio, no card)
        2. ollama   -- local, free, requires Ollama running
    """

    def __init__(
        self,
        primary: str = "groq",
        secondary: str = "gemini",
        key_pool=None,
    ):
        self.primary = primary
        self.secondary = secondary
        self._key_pool = key_pool

    def _call_provider(self, provider: str, prompt: str) -> tuple[str, str]:
        """Return (verdict, reason)."""
        if provider == "groq":
            content = _call_groq(prompt, key_pool=self._key_pool)
        elif provider == "gemini":
            content = _call_gemini(prompt)
        elif provider == "ollama":
            content = _call_ollama(prompt)
        else:
            raise ValueError(f"unknown provider: {provider}")
        return parse_verdict(content)

    def review(self, finding: dict) -> SecondOpinionResult:
        """Get verdicts from both providers and compute agreement."""
        fid = int(finding.get("id") or 0)
        prompt = _build_prompt(finding)
        started = time.time()

        try:
            primary_verdict, primary_reason = self._call_provider(self.primary, prompt)
        except Exception as exc:
            logger.warning("primary provider %s failed: %s", self.primary, exc)
            return SecondOpinionResult(
                finding_id=fid,
                primary_provider=self.primary,
                primary_verdict="NEEDS_REVIEW",
                primary_reason="primary provider unavailable",
                secondary_provider=self.secondary,
                secondary_verdict="NEEDS_REVIEW",
                secondary_reason="not attempted (primary failed)",
                agreement=False,
                confidence_delta=0,
                skipped_reason="primary_unavailable",
                latency_ms=int((time.time() - started) * 1000),
            )

        try:
            secondary_verdict, secondary_reason = self._call_provider(self.secondary, prompt)
            skipped_reason: str | None = None
        except (_OllamaUnavailableError, _GeminiUnavailableError) as exc:
            # Gemini key absent or Ollama not running — degrade gracefully
            secondary_verdict, secondary_reason = "NEEDS_REVIEW", ""
            skipped_reason = f"{self.secondary}_unavailable: {exc}"
            # If Gemini failed, try Ollama as last resort
            if self.secondary == "gemini":
                try:
                    secondary_verdict, secondary_reason = self._call_provider("ollama", prompt)
                    skipped_reason = None
                except _OllamaUnavailableError:
                    pass  # Both cloud + local unavailable — skip secondary
        except Exception as exc:
            logger.warning("secondary provider %s failed: %s", self.secondary, exc)
            secondary_verdict, secondary_reason = "NEEDS_REVIEW", ""
            skipped_reason = f"secondary_unavailable: {exc}"

        agreement = (
            primary_verdict == secondary_verdict and primary_verdict in VALID_VERDICTS and skipped_reason is None
        )
        # Confidence delta: +15 when both agree on TP/FP, -10 when they disagree,
        # 0 when skipped or one is NEEDS_REVIEW.
        if skipped_reason:
            confidence_delta = 0
        elif agreement and primary_verdict in ("TP", "FP"):
            confidence_delta = 15
        elif primary_verdict != secondary_verdict:
            confidence_delta = -10
        else:
            confidence_delta = 0

        return SecondOpinionResult(
            finding_id=fid,
            primary_provider=self.primary,
            primary_verdict=primary_verdict,
            primary_reason=primary_reason,
            secondary_provider=self.secondary,
            secondary_verdict=secondary_verdict,
            secondary_reason=secondary_reason,
            agreement=agreement,
            confidence_delta=confidence_delta,
            skipped_reason=skipped_reason,
            latency_ms=int((time.time() - started) * 1000),
        )


def agreement_rate(results: list[SecondOpinionResult]) -> dict:
    """Aggregate metric: per-batch agreement rate (Eval Wave 2 publishable number)."""
    valid = [r for r in results if not r.skipped_reason]
    n = len(valid)
    agree = sum(1 for r in valid if r.agreement)
    return {
        "total_findings": len(results),
        "skipped": len(results) - n,
        "scored": n,
        "agreed": agree,
        "agreement_rate": (agree / n) if n else 0.0,
    }
