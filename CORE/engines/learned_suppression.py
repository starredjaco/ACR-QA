"""
Learned Suppression Engine — Feature 10 (v3.4.0).

Uses sentence-transformer embeddings to suppress findings semantically
similar to ones previously dismissed as false positives.

Workflow:
  1. User marks finding N as FP → `store_dismissed(N, db)` embeds it
  2. On next scan → `suppress(findings, db)` checks cosine similarity
  3. If similarity > THRESHOLD: confidence set to 0, annotated with reason

Model: all-MiniLM-L6-v2 (~80MB, runs locally, no API keys needed).
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.92
MODEL_NAME = "all-MiniLM-L6-v2"

if TYPE_CHECKING:
    pass

# Lazy-loaded to avoid import-time cost if sentence-transformers not installed.
_model = None


def _get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer(MODEL_NAME)
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is required for learned suppression. "
                "Install with: pip install sentence-transformers"
            ) from exc
    return _model


def _finding_to_text(finding: dict) -> str:
    """Canonical text representation of a finding for embedding."""
    parts = [
        finding.get("canonical_rule_id") or finding.get("rule_id", ""),
        finding.get("message", finding.get("description", "")),
        finding.get("file", finding.get("file_path", "")),
        str(finding.get("line", finding.get("line_number", ""))),
    ]
    return " | ".join(p for p in parts if p)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two float vectors (pure Python, no numpy required)."""
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class LearnedSuppressionEngine:
    """Semantic FP suppression via sentence-transformer embeddings."""

    def __init__(self, threshold: float = SIMILARITY_THRESHOLD):
        self.threshold = threshold

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed_text(self, text: str) -> list[float]:
        """Embed a string and return a float list (JSON-serialisable)."""
        model = _get_model()
        vec = model.encode(text, convert_to_numpy=True)
        return vec.tolist()

    def store_dismissed(self, finding_id: int, db) -> bool:
        """
        Load finding from DB, embed it, and store in finding_embeddings.

        Returns True on success, False if finding not found or embedding fails.
        """
        try:
            rows = db.execute(
                "SELECT canonical_rule_id, file_path, message FROM findings WHERE id = %s",
                (finding_id,),
                fetch=True,
            )
            if not rows:
                logger.warning("store_dismissed: finding %s not found", finding_id)
                return False

            row = rows[0]
            finding_dict = {
                "canonical_rule_id": row.get("canonical_rule_id") or "",
                "message": row.get("message", ""),
                "file": row.get("file_path", ""),
            }
            text = _finding_to_text(finding_dict)
            vec = self.embed_text(text)
            embedding_json = json.dumps(vec)

            db.insert_finding_embedding(
                rule_id=finding_dict["canonical_rule_id"] or "UNKNOWN",
                embedding_json=embedding_json,
                code_context=text,
                finding_id=finding_id,
            )
            logger.info("LearnedSuppression: embedded finding %s (%s)", finding_id, finding_dict["canonical_rule_id"])
            return True
        except Exception:
            logger.exception("store_dismissed failed for finding %s", finding_id)
            return False

    def suppress(self, findings: list[dict], db) -> tuple[list[dict], int]:
        """
        Filter findings by cosine similarity to previously dismissed embeddings.

        Returns (kept_findings, suppressed_count).
        Gracefully degrades if sentence-transformers is not installed or DB is unavailable.
        """
        try:
            stored = db.get_all_finding_embeddings()
            if not stored:
                return findings, 0

            # Parse all stored vectors once
            stored_vecs: list[tuple[str, list[float]]] = []
            for row in stored:
                try:
                    vec = json.loads(row["embedding_json"])
                    stored_vecs.append((row["rule_id"], vec))
                except Exception:
                    continue

            if not stored_vecs:
                return findings, 0

            kept: list[dict] = []
            suppressed = 0

            for finding in findings:
                rule_id = finding.get("canonical_rule_id") or finding.get("rule_id", "")
                text = _finding_to_text(finding)
                try:
                    query_vec = self.embed_text(text)
                except ImportError:
                    # sentence-transformers not installed — skip silently
                    return findings, 0

                for stored_rule, stored_vec in stored_vecs:
                    # Only compare same-rule embeddings for efficiency
                    if stored_rule != rule_id:
                        continue
                    sim = _cosine_similarity(query_vec, stored_vec)
                    if sim >= self.threshold:
                        finding = dict(finding)
                        finding["confidence_score"] = 0
                        finding["suppressed_by_embedding"] = True
                        finding["embedding_similarity"] = round(sim, 4)
                        finding["suppression_reason"] = f"Similar to previously-dismissed finding (cosine={sim:.3f})"
                        suppressed += 1
                        break

                kept.append(finding)  # kept but confidence=0, not removed

            return kept, suppressed

        except Exception:
            logger.exception("LearnedSuppression.suppress failed — returning all findings")
            return findings, 0

    def is_available(self) -> bool:
        """Return True if sentence-transformers is importable."""
        try:
            from sentence_transformers import SentenceTransformer  # noqa: F401

            return True
        except ImportError:
            return False
