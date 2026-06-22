# Runbook — Slots 2 & 4 (run locally; need Docker + network)

These two are the highest-differentiation moves but can't run in the CI sandbox (no Docker, no
network). Run them on your machine. Each is copy-paste turnkey. Assumes repo root with `.venv` active.

---

## Slot 4a — Instant held-out expansion (needs network only) ⏱ ~5 min

**4 RealVuln repos have ground truth but no local checkout — the engine has *never seen them*.**
Cloning + scoring them is the cleanest held-out test we can get without leaving RealVuln (existing
GT, zero tuning). This directly strengthens the "generalises" claim.

```bash
cd TESTS/evaluation/realvuln

# 1. Clone the 4 unseen repos at their pinned commits (reads URL + SHA from ground truth)
python3 clone_repos.py --repo \
  realvuln-pygoat realvuln-owasp-web-playground \
  realvuln-python-app realvuln-vulnerable-api

# 2. Score the FROZEN engine on them (back to repo root)
cd ../../..
.venv/bin/python scripts/run_realvuln_hybrid.py --static-only \
  --repos realvuln-pygoat realvuln-owasp-web-playground realvuln-python-app realvuln-vulnerable-api

# 3. Official scorer per repo (source of truth)
cd TESTS/evaluation/realvuln
for r in realvuln-pygoat realvuln-python-app realvuln-vulnerable-api; do
  ../../../.venv/bin/python score.py --repo $r --scanner acr-qa-hybrid-v1
done
```

**What to record:** the recall/precision on these 4 — that becomes part of the held-out number, on
repos the engine demonstrably never touched. If it holds ~45–50%, the generalisation story is
ironclad. (Note: some `kolega-ai/...` mirror URLs may be private/404 — clone what resolves; pygoat
and the dolevf/Contrast upstreams are public.)

## Slot 4b — Gold-standard external corpus (needs network) ⏱ ~1–2 hrs

Truly *outside* RealVuln — the unfakeable proof. Clone fresh intentionally-vulnerable Python repos
NOT in the benchmark, score the frozen engine, sanity-check findings against their READMEs/known CVEs.

```bash
mkdir -p /tmp/external-heldout && cd /tmp/external-heldout
git clone https://github.com/adeyosemanputra/pygoat          # OWASP PyGoat (Django)
git clone https://github.com/anxolerd/dvpwa                   # async Flask
git clone https://github.com/we45/Vulnerable-Flask-App
git clone https://github.com/payatu/Tplmap-test || true
# Score each with the standalone engine (no GT needed — manual triage of the finding list):
for d in */; do
  echo "=== $d ==="
  cd "$REPO_ROOT" && .venv/bin/python scripts/ast_security_scanner.py "/tmp/external-heldout/$d" | tail -3
done
```

**What to record:** eyeball the findings vs each repo's documented vulns. This is the number a
committee/HN cannot attack ("you only ran on the author's repos" → "here's a repo they never made").

---

## Slot 2 — Exploit-proven tier (needs Docker) ⏱ ~10–30 min

`CORE/engines/exploit_verifier.py` spins each runnable repo in a Docker sandbox (`--network none`),
fires the exploit payload, and marks confirmed findings `exploit_tier="verified-exploitable"` with a
reproducible PoC + ECDSA/Dilithium attestation. **No scanner on the RealVuln leaderboard offers
exploit-proven findings.**

```bash
# 0. Confirm Docker is up
docker info >/dev/null && echo "docker OK"

# 1. Run the driver (added in this branch) — scans + detonates verifiable findings per repo
.venv/bin/python scripts/realvuln_exploit_verify.py \
  --repos realvuln-vfapi realvuln-vulnpy realvuln-dvpwa realvuln-dsvw

# It prints, per repo: findings, how many were exploit-verifiable, how many DETONATED, and writes
# PoC proof JSON for each proven finding.
```

**What to record:** the count of `verified-exploitable` findings = the **PROVEN tier** (~100%
precision, each with a PoC). Coverage is partial (not every repo spins up cleanly) — that's expected;
PROVEN is a premium tier *on top of* recall mode, not a replacement. Even a handful of exploit-proven
findings with signed PoCs is a category no competitor matches.

> If a repo won't boot, the verifier writes a default Dockerfile and retries; repos needing custom
> setup (DB seed, env vars) will skip — fine, they fall back to the static tiers.

---

## After running — fold results back

1. Add the slot-4 repos' numbers to `docs/evaluation/REALVULN_PURE_STATIC_2026_06_22.md` (held-out
   section) — they expand the unseen set.
2. Add the PROVEN-tier count to the confidence-tier table (a 4th, top tier above CONFIRMED).
3. Update `KOLEGA_PARITY_PLAN.md` (mark slots 2 / 4 done).
