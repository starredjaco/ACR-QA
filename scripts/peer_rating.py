#!/usr/bin/env python3
"""Peer-rating harness for the 5-rater inter-rater agreement study (v5.0.0 A4).

Three sub-commands:

    sample   — pull a stratified sample of N findings from a run, anonymize them
               (strip ACR-QA's own verdict + confidence), and emit a Markdown
               packet plus a CSV ballot for raters to fill in.

    score    — given one or more rater-submitted ballots (CSV with columns
               finding_id,verdict), compute:
                 - pairwise Cohen's κ matrix
                 - Fleiss' κ across all raters
                 - per-finding agreement count
               and write `docs/evaluation/PEER_VALIDATION_v5.md`.

    blank    — emit a blank ballot CSV that raters can save-as.

Verdict labels: TP / FP / NEEDS_REVIEW.

Pure stdlib + PyYAML (already a project dep). No scipy / sklearn — Cohen's and
Fleiss' κ are short enough to implement inline (and the implementation lives
in this file so reviewers can audit it).
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

VALID_VERDICTS = ("TP", "FP", "NEEDS_REVIEW")


# ── κ computations ───────────────────────────────────────────────────────────


def cohens_kappa(rater_a: list[str], rater_b: list[str]) -> float:
    """Cohen's κ between two raters on the same items.

    κ = (p_o - p_e) / (1 - p_e), where p_o is observed agreement and p_e is
    chance agreement under the assumption that each rater's marginal frequency
    is independent.
    """
    assert len(rater_a) == len(rater_b), "raters must label the same items"
    n = len(rater_a)
    if n == 0:
        return 0.0
    categories = set(rater_a) | set(rater_b)
    p_o = sum(1 for a, b in zip(rater_a, rater_b, strict=False) if a == b) / n
    p_e = 0.0
    for c in categories:
        pa = rater_a.count(c) / n
        pb = rater_b.count(c) / n
        p_e += pa * pb
    if abs(1 - p_e) < 1e-12:
        return 1.0 if p_o == 1.0 else 0.0
    return (p_o - p_e) / (1 - p_e)


def fleiss_kappa(ballots: list[list[str]], categories: list[str]) -> float:
    """Fleiss' κ across an arbitrary number of raters on the same items.

    `ballots` is shape (R, N): R raters × N items. We build the N×K count
    matrix and apply Fleiss' formula.
    """
    if not ballots or not ballots[0]:
        return 0.0
    n_items = len(ballots[0])
    r = len(ballots)
    k = len(categories)
    if r < 2:
        return 0.0
    # n_ij — number of raters who gave item i category j
    n_ij = [[0] * k for _ in range(n_items)]
    for ballot in ballots:
        for i, verdict in enumerate(ballot):
            if verdict in categories:
                n_ij[i][categories.index(verdict)] += 1
    # P_i — agreement on item i
    P_i = []
    for i in range(n_items):
        s = sum(n_ij[i][j] * (n_ij[i][j] - 1) for j in range(k))
        P_i.append(s / (r * (r - 1)) if r > 1 else 0.0)
    P_bar = sum(P_i) / n_items if n_items else 0.0
    # P_e — chance agreement
    p_j = [sum(n_ij[i][j] for i in range(n_items)) / (n_items * r) for j in range(k)]
    P_e = sum(p * p for p in p_j)
    if abs(1 - P_e) < 1e-12:
        return 1.0 if P_bar == 1.0 else 0.0
    return (P_bar - P_e) / (1 - P_e)


def landis_koch(kappa: float) -> str:
    """Landis & Koch (1977) verbal scale for κ."""
    if kappa < 0:
        return "worse than chance"
    if kappa < 0.20:
        return "slight"
    if kappa < 0.40:
        return "fair"
    if kappa < 0.60:
        return "moderate"
    if kappa < 0.80:
        return "substantial"
    return "almost perfect"


# ── Sampling ──────────────────────────────────────────────────────────────────


@dataclass
class SampledFinding:
    finding_id: int
    canonical_rule_id: str
    severity: str
    file_path: str
    line_number: int
    message: str

    def as_packet_row(self, idx: int) -> str:
        return (
            f"### #{idx} — {self.canonical_rule_id} ({self.severity})\n"
            f"`{self.file_path}:{self.line_number}`\n\n"
            f"{self.message}\n\n"
            f"_Your verdict (TP / FP / NEEDS_REVIEW):_ ______________\n"
        )


def stratified_sample(findings: list[dict], n: int, seed: int = 42) -> list[SampledFinding]:
    """Pick *n* findings split evenly across high/medium/low (best effort)."""
    rng = random.Random(seed)
    buckets: dict[str, list[dict]] = {"high": [], "medium": [], "low": []}
    for f in findings:
        sev = (f.get("canonical_severity") or f.get("severity") or "low").lower()
        if sev not in buckets:
            sev = "low"
        buckets[sev].append(f)
    target_per_bucket = max(1, n // 3)
    picked: list[dict] = []
    for sev in ("high", "medium", "low"):
        pool = buckets[sev]
        rng.shuffle(pool)
        picked.extend(pool[:target_per_bucket])
    rng.shuffle(picked)
    if len(picked) > n:
        picked = picked[:n]
    elif len(picked) < n:
        # top up from any bucket if a stratum was small
        leftover = [f for sev in buckets for f in buckets[sev] if f not in picked]
        rng.shuffle(leftover)
        picked.extend(leftover[: n - len(picked)])
    return [
        SampledFinding(
            finding_id=int(f.get("id") or 0),
            canonical_rule_id=str(f.get("canonical_rule_id") or f.get("rule_id") or "UNKNOWN"),
            severity=str(f.get("canonical_severity") or f.get("severity") or "low"),
            file_path=str(f.get("file_path") or "unknown"),
            line_number=int(f.get("line_number") or 0),
            message=str(f.get("message") or "")[:400],
        )
        for f in picked[:n]
    ]


def write_packet(samples: list[SampledFinding], dest: Path) -> None:
    lines: list[str] = ["# ACR-QA Peer Validation Packet\n"]
    lines.append(
        "Rate each finding as **TP** (true positive — real issue), **FP** (false positive — "
        "spurious / out of scope), or **NEEDS_REVIEW** (cannot decide without more context).\n",
    )
    lines.append("Return your CSV ballot to the maintainer when done.\n\n---\n")
    for i, s in enumerate(samples, start=1):
        lines.append(s.as_packet_row(i))
    dest.write_text("\n".join(lines), encoding="utf-8")


def write_ballot(samples: list[SampledFinding], dest: Path) -> None:
    with dest.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["finding_id", "rule_id", "verdict"])
        for s in samples:
            w.writerow([s.finding_id, s.canonical_rule_id, ""])


# ── Sub-commands ─────────────────────────────────────────────────────────────


def cmd_sample(args: argparse.Namespace) -> int:
    src = Path(args.input)
    if not src.is_file():
        print(f"[error] findings JSON not found: {src}", file=sys.stderr)
        return 2
    data = json.loads(src.read_text(encoding="utf-8"))
    findings = data if isinstance(data, list) else data.get("findings", [])
    if not findings:
        print("[error] no findings to sample from")
        return 2
    samples = stratified_sample(findings, args.n, seed=args.seed)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_packet(samples, out_dir / "PACKET.md")
    write_ballot(samples, out_dir / "ballot.csv")
    print(f"Wrote packet + ballot to {out_dir} ({len(samples)} items)")
    return 0


def cmd_blank(args: argparse.Namespace) -> int:
    src = Path(args.ballot)
    if not src.is_file():
        print(f"[error] reference ballot not found: {src}", file=sys.stderr)
        return 2
    rows = list(csv.DictReader(src.open()))
    out = Path(args.out)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["finding_id", "rule_id", "verdict"])
        for r in rows:
            w.writerow([r["finding_id"], r["rule_id"], ""])
    print(f"Wrote blank ballot to {out}")
    return 0


def _load_ballot(path: Path) -> tuple[list[int], list[str]]:
    fids: list[int] = []
    verdicts: list[str] = []
    with path.open() as f:
        for row in csv.DictReader(f):
            try:
                fid = int(row["finding_id"])
            except (KeyError, ValueError):
                continue
            v = (row.get("verdict") or "").strip().upper()
            if v not in VALID_VERDICTS:
                continue
            fids.append(fid)
            verdicts.append(v)
    return fids, verdicts


def cmd_score(args: argparse.Namespace) -> int:
    ballots: list[tuple[str, list[int], list[str]]] = []
    for p in args.ballots:
        path = Path(p)
        fids, verdicts = _load_ballot(path)
        if not fids:
            print(f"[warn] {path}: no valid rows", file=sys.stderr)
            continue
        ballots.append((path.stem, fids, verdicts))

    if len(ballots) < 2:
        print("[error] need at least 2 valid ballots", file=sys.stderr)
        return 2

    # Align ballots on shared finding_ids (intersection).
    shared = set.intersection(*[set(b[1]) for b in ballots])
    if not shared:
        print("[error] no overlapping finding_ids across ballots", file=sys.stderr)
        return 2

    aligned: list[tuple[str, list[str]]] = []
    fid_order = sorted(shared)
    for name, fids, verdicts in ballots:
        fid_to_v = dict(zip(fids, verdicts, strict=False))
        aligned.append((name, [fid_to_v[fid] for fid in fid_order]))

    # Pairwise Cohen's
    print(f"\n# Peer agreement on {len(fid_order)} shared findings\n")
    print(f"Raters: {[a[0] for a in aligned]}\n")
    print("## Pairwise Cohen's κ")
    pairwise: list[tuple[str, str, float]] = []
    for i in range(len(aligned)):
        for j in range(i + 1, len(aligned)):
            k = cohens_kappa(aligned[i][1], aligned[j][1])
            pairwise.append((aligned[i][0], aligned[j][0], k))
            print(f"  {aligned[i][0]} ↔ {aligned[j][0]}: κ = {k:.3f}  ({landis_koch(k)})")

    # Fleiss'
    fk = fleiss_kappa([a[1] for a in aligned], list(VALID_VERDICTS))
    print(f"\n## Fleiss' κ across all {len(aligned)} raters: {fk:.3f}  ({landis_koch(fk)})")

    if args.write_md:
        out = ROOT / "docs" / "evaluation" / "PEER_VALIDATION_v5.md"
        lines = [
            "# Peer Validation v5.0.0 (Eval Wave 2)\n",
            f"_Shared findings: {len(fid_order)} · Raters: {len(aligned)}_\n",
            "## Pairwise Cohen's κ\n",
            "| Rater A | Rater B | κ | Interpretation |",
            "|---|---|---:|---|",
        ]
        for a, b, k in pairwise:
            lines.append(f"| {a} | {b} | {k:.3f} | {landis_koch(k)} |")
        lines.append("\n## Fleiss' κ across all raters\n")
        lines.append(f"**κ = {fk:.3f}** ({landis_koch(fk)})\n")
        lines.append("\n_Generated by `scripts/peer_rating.py`._\n")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(lines), encoding="utf-8")
        print(f"\nWrote {out.relative_to(ROOT)}")

    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="ACR-QA peer-rating harness")
    sp = p.add_subparsers(dest="cmd", required=True)

    s = sp.add_parser("sample", help="emit packet + blank ballot from a findings JSON")
    s.add_argument("--input", required=True, help="findings JSON (list, or {'findings': [...]})")
    s.add_argument("--n", type=int, default=30, help="sample size (default 30)")
    s.add_argument("--seed", type=int, default=42)
    s.add_argument("--out-dir", default="peer_study_out")
    s.set_defaults(func=cmd_sample)

    b = sp.add_parser("blank", help="emit a blank ballot from a reference ballot")
    b.add_argument("--ballot", required=True)
    b.add_argument("--out", default="ballot_blank.csv")
    b.set_defaults(func=cmd_blank)

    sc = sp.add_parser("score", help="compute Cohen's + Fleiss' κ from rater ballots")
    sc.add_argument("ballots", nargs="+", help="CSV ballots (one per rater)")
    sc.add_argument("--write-md", action="store_true")
    sc.set_defaults(func=cmd_score)

    args = p.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
