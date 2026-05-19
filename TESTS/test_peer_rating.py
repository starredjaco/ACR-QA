"""Tests for the peer-rating κ math + sampling (v5.0.0 Phase A.4)."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.peer_rating import (
    VALID_VERDICTS,
    cohens_kappa,
    fleiss_kappa,
    landis_koch,
    stratified_sample,
    write_ballot,
    write_packet,
)

# ── Cohen's κ ────────────────────────────────────────────────────────────────


class TestCohensKappa:
    def test_perfect_agreement(self):
        a = ["TP", "TP", "FP", "FP", "NEEDS_REVIEW"]
        assert cohens_kappa(a, list(a)) == pytest.approx(1.0)

    def test_zero_agreement_on_2_classes_returns_negative(self):
        a = ["TP"] * 10
        b = ["FP"] * 10
        # All-disagree on disjoint single-class outputs: chance = 0 → κ = -1 / 0,
        # but our zero-chance branch handles this gracefully (returns 0 unless p_o=1).
        assert cohens_kappa(a, b) <= 0.0

    def test_known_value(self):
        # Hand-computed example: 8 items, 6 agree (TP/TP×4, FP/FP×2), 2 disagree.
        a = ["TP", "TP", "TP", "TP", "FP", "FP", "TP", "FP"]
        b = ["TP", "TP", "TP", "TP", "FP", "FP", "FP", "TP"]
        # p_o = 6/8 = 0.75
        # marginals: a = 5 TP / 3 FP → 0.625 / 0.375
        # marginals: b = 5 TP / 3 FP → 0.625 / 0.375
        # p_e = 0.625² + 0.375² = 0.390625 + 0.140625 = 0.53125
        # κ = (0.75 - 0.53125) / (1 - 0.53125) = 0.21875 / 0.46875 ≈ 0.4667
        assert cohens_kappa(a, b) == pytest.approx(0.4667, abs=1e-3)

    def test_empty_returns_zero(self):
        assert cohens_kappa([], []) == 0.0


# ── Fleiss' κ ────────────────────────────────────────────────────────────────


class TestFleissKappa:
    def test_unanimous_returns_one(self):
        ballots = [["TP", "TP", "FP"], ["TP", "TP", "FP"], ["TP", "TP", "FP"]]
        assert fleiss_kappa(ballots, list(VALID_VERDICTS)) == pytest.approx(1.0)

    def test_random_returns_low(self):
        ballots = [
            ["TP", "FP", "NEEDS_REVIEW", "TP"],
            ["FP", "TP", "TP", "NEEDS_REVIEW"],
            ["NEEDS_REVIEW", "NEEDS_REVIEW", "FP", "FP"],
        ]
        k = fleiss_kappa(ballots, list(VALID_VERDICTS))
        assert -0.5 < k < 0.5

    def test_single_rater_returns_zero(self):
        assert fleiss_kappa([["TP", "FP"]], list(VALID_VERDICTS)) == 0.0


# ── Landis & Koch ────────────────────────────────────────────────────────────


class TestLandisKoch:
    @pytest.mark.parametrize(
        ("k", "expected"),
        [
            (-0.1, "worse than chance"),
            (0.05, "slight"),
            (0.30, "fair"),
            (0.50, "moderate"),
            (0.78, "substantial"),
            (0.95, "almost perfect"),
        ],
    )
    def test_buckets(self, k, expected):
        assert landis_koch(k) == expected


# ── Sampling + packet/ballot ─────────────────────────────────────────────────


class TestSampling:
    def test_stratified_sample_respects_strata(self):
        findings = (
            [
                {
                    "id": i,
                    "canonical_severity": "high",
                    "canonical_rule_id": "S",
                    "message": "m",
                    "file_path": "f",
                    "line_number": 1,
                }
                for i in range(10)
            ]
            + [
                {
                    "id": i + 100,
                    "canonical_severity": "medium",
                    "canonical_rule_id": "S",
                    "message": "m",
                    "file_path": "f",
                    "line_number": 1,
                }
                for i in range(10)
            ]
            + [
                {
                    "id": i + 200,
                    "canonical_severity": "low",
                    "canonical_rule_id": "S",
                    "message": "m",
                    "file_path": "f",
                    "line_number": 1,
                }
                for i in range(10)
            ]
        )
        out = stratified_sample(findings, n=9, seed=0)
        sevs = [s.severity for s in out]
        assert sevs.count("high") == 3
        assert sevs.count("medium") == 3
        assert sevs.count("low") == 3

    def test_stratified_sample_handles_short_strata(self):
        findings = [
            {
                "id": 1,
                "canonical_severity": "high",
                "canonical_rule_id": "S",
                "message": "m",
                "file_path": "f",
                "line_number": 1,
            },
            {
                "id": 2,
                "canonical_severity": "medium",
                "canonical_rule_id": "S",
                "message": "m",
                "file_path": "f",
                "line_number": 1,
            },
        ]
        out = stratified_sample(findings, n=4, seed=0)
        assert len(out) == 2  # nothing to top up with

    def test_packet_and_ballot_written(self, tmp_path: Path):
        findings = [
            {
                "id": 1,
                "canonical_rule_id": "SEC-001",
                "canonical_severity": "high",
                "file_path": "app.py",
                "line_number": 5,
                "message": "eval used",
            }
        ]
        samples = stratified_sample(findings, n=1, seed=0)
        write_packet(samples, tmp_path / "PACKET.md")
        write_ballot(samples, tmp_path / "ballot.csv")
        packet = (tmp_path / "PACKET.md").read_text()
        assert "SEC-001" in packet
        with (tmp_path / "ballot.csv").open() as f:
            rows = list(csv.reader(f))
        assert rows[0] == ["finding_id", "rule_id", "verdict"]
        assert rows[1][0] == "1"


# ── Sub-command smoke (sample → score) ───────────────────────────────────────


class TestEndToEnd:
    def test_score_two_ballots_writes_md(self, tmp_path: Path, monkeypatch):
        # Build two ballots with mostly-agreement
        b1 = tmp_path / "alice.csv"
        b2 = tmp_path / "bob.csv"
        for path, verdicts in (
            (b1, ["TP", "TP", "FP", "FP", "NEEDS_REVIEW"]),
            (b2, ["TP", "TP", "FP", "TP", "NEEDS_REVIEW"]),
        ):
            with path.open("w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["finding_id", "rule_id", "verdict"])
                for i, v in enumerate(verdicts):
                    w.writerow([i, "RID", v])

        from scripts.peer_rating import main as peer_main

        monkeypatch.chdir(tmp_path)
        rc = peer_main(["score", str(b1), str(b2)])
        assert rc == 0

    def test_score_requires_two_ballots(self, tmp_path: Path):
        from scripts.peer_rating import main as peer_main

        b1 = tmp_path / "x.csv"
        with b1.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["finding_id", "rule_id", "verdict"])
            w.writerow([1, "R", "TP"])
        assert peer_main(["score", str(b1)]) == 2
