"""Confidence-tier logic for the RealVuln hybrid runner (the deterministic Confirmed Tier).

Findings corroborated by >=2 independent engines are 'certain' (~79% precision on RealVuln);
syntactically-clear single-engine detectors are 'firm'; authorization heuristics are 'tentative'.
This gives an honest high-precision operating point alongside the high-recall one.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from run_realvuln_hybrid import _confidence_tier  # noqa: E402


def test_agreement_is_certain():
    # Two independent engines agreeing → certain, regardless of CWE.
    assert _confidence_tier("CWE-306", n_sources=2) == "certain"
    assert _confidence_tier("CWE-89", n_sources=3) == "certain"


def test_single_source_firm_vs_tentative():
    # Syntactically-clear detectors are firm; authorization heuristics are tentative.
    assert _confidence_tier("CWE-798", n_sources=1) == "firm"  # hardcoded secret
    assert _confidence_tier("CWE-89", n_sources=1) == "firm"  # SQLi
    assert _confidence_tier("CWE-306", n_sources=1) == "tentative"  # missing-auth heuristic
    assert _confidence_tier("CWE-639", n_sources=1) == "tentative"  # IDOR heuristic


def test_tier_is_deterministic():
    # Same inputs → same tier, always (the whole point).
    for _ in range(5):
        assert _confidence_tier("CWE-352", 1) == "tentative"
        assert _confidence_tier("CWE-918", 2) == "certain"
