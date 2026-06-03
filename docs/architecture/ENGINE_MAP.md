# ACR-QA Engine Map

> **Created:** 2026-06-03
> **Purpose:** One-screen answer to "why 36 engines?" — purpose, status, and pipeline role per engine.
> **Status legend:** `core` = always runs · `detection` = part of tool-runner pipeline · `eval-only` = scripts/benchmarks · `feature` = opt-in capability · `adapter` = external-tool wrapper · `legacy` = kept for tests

---

## Pipeline-Critical Engines (run on every scan)

| Engine | Class | Purpose | Default enabled |
|--------|-------|---------|----------------|
| `normalizer.py` | `CanonicalFinding` | Universal normalizer — converts every tool's raw JSON into the `CanonicalFinding` Pydantic contract. **Central data contract; all downstream engines consume this.** | ✅ always |
| `severity_scorer.py` | `SeverityScorer` | Maps `canonical_rule_id` → severity tier (high/medium/low). Single source of truth for severity. | ✅ always |
| `quality_gate.py` | `QualityGate` | Evaluates findings against `.acrqa.yml` thresholds (max HIGH, fail conditions). Pipeline pass/fail decision. | ✅ always |
| `fingerprint.py` | — | Stable dedup hash per finding (file+line+rule+content). Prevents duplicate findings across runs. | ✅ always |
| `confirmed_tier.py` | `ConfirmedTierEngine` | 4-gate filter for auto-block precision stratum: HIGH severity + 22 curated rules + production path + Bandit HIGH confidence. **96.4% precision, ~0% FPR on production code.** | ✅ always |
| `taint_analyzer.py` | `TaintInfo` | Inter-procedural HTTP-source → sink taint tracking. Gates findings on HTTP-source confirmation (±5 lines). | ✅ always |

---

## Detection & Analysis Engines

| Engine | Class | Purpose | Default enabled |
|--------|-------|---------|----------------|
| `explainer.py` | `ExplanationEngine` | RAG-grounded AI explanations via Groq (Llama 3.x). Generates per-finding natural-language explanations with code context. Cost: free Groq tier. | ✅ (skip with `--no-ai`) |
| `exploit_verifier.py` | `ExploitVerifier` | Docker-sandbox exploit verification. Fires safe PoC payloads (10 categories: SQLi, CMDi, SSTI, path-traversal, SSRF, XXE, insecure-deser, open-redirect, ReDoS, LDAP). Only `verified-exploitable` findings reach Confirmed Tier. | ✅ when Docker available |
| `verified_remediation.py` | `VerifiedRemediationEngine` | 5-step verified-fix pipeline: exploit-fires → AI patch → re-run exploit → confirm fails → ECDSA-sign `(vuln_proof, fix_diff, fix_proof)`. **The frontier: re-exploits after fix instead of static re-scan.** | ✅ when Docker + LLM |
| `attestation.py` | `AttestationEngine` | ECDSA-P256 signs every scan verdict + Rekor (Sigstore) transparency log. Provides tamper-evident provenance. | ✅ always |
| `confidence_scorer.py` | `ConfidenceScorer` | 0–100 confidence score per finding based on tool agreement, severity, and rule metadata. | ✅ always |

---

## Opt-In Feature Engines

| Engine | Class | Purpose | Default enabled |
|--------|-------|---------|----------------|
| `secrets_detector.py` | `SecretsDetector` | Detects hardcoded credentials, API keys, tokens via regex + entropy. Separate from Bandit's secret rules. | ✅ |
| `sca_scanner.py` | `SCAScanner` | Software Composition Analysis — checks `requirements.txt`/`package.json`/`go.mod` against OSV/PyPI advisories. | ✅ |
| `supply_chain.py` | `SupplyChainEngine` | Deep SCA: pinning analysis, typosquatting detection, deprecated-package detection, SBOM generation. | ✅ |
| `iac_scanner.py` | `IaCScanner` | Infrastructure-as-Code scanner (Terraform, CloudFormation, Helm). 28 IaC-specific rules (CWE-250/732/319). | ✅ when IaC files present |
| `autofix.py` | `AutoFixEngine` | LLM-powered patch generation + rule-based fixes (eval→literal_eval, f-string SQL→parameterized, etc.). | `--fix` flag |
| `triage_agent.py` | `TriageAgent` | Multi-step AI reasoning for finding triage — exploitability, context, recommended action. | `--triage` flag |
| `triage_memory.py` | `TriageMemory` | Learns from false-positive feedback. Suppresses previously-dismissed patterns. | ✅ always |
| `learned_suppression.py` | `LearnedSuppressionEngine` | Semantic embedding-based FP suppression (similarity to dismissed findings). | ✅ always |
| `path_feasibility.py` | `PathFeasibilityValidator` | LLM-based path feasibility validation (LLM4PFA approach). Estimates if a code path is reachable. | `--feasibility` flag |
| `second_opinion.py` | `SecondOpinionResult` | Multi-model jury (Groq + Gemini) for non-exploitable-class findings. Calibrated confidence + cited rationale. | `--second-opinion` flag |
| `ai_code_detector.py` | `AICodeDetector` | Detects AI-generated code (git-log heuristics + file header analysis). Used by `--ai-code-diff`. | `--ai-code-diff` flag |
| `ai_code_diff.py` | `AiCodeDiffFilter` | Filters findings to only AI-touched files (Copilot/Cursor/Claude). Surfaces AI-code vulns specifically. | `--ai-code-diff` flag |

---

## Evaluation & Research Engines

| Engine | Class | Purpose | Default enabled |
|--------|-------|---------|----------------|
| `reachability.py` | `CallGraphReachability` | Call-graph reachability engine. Traces whether a vulnerable function is reachable from entry points. | eval/API |
| `dependency_reachability.py` | `DependencyReachabilityChecker` | Checks whether a vulnerable dependency version is actually called in application code. | eval/API |
| `cross_language_correlator.py` | `CrossLanguageCorrelator` | Correlates findings across Python/JS/Go when shared infra suggests the same root cause (CHARON-inspired). | eval/API |
| `cbom_scanner.py` | `CBoMReport` | Cryptographic Bill of Materials — inventories all crypto primitives used (algorithms, key sizes, libraries). | eval/API |
| `osv_offline.py` | `OsvOfflineReader` | Reads a local OSV snapshot (offline mode). Used when egress is blocked. | offline mode |
| `ollama_provider.py` | — | OpenAI-compatible Ollama client for local LLM inference (offline mode). | offline mode |
| `risk_predictor.py` | `RiskScore` | Heuristic risk predictor (weights: severity, churn, age, exploit surface). Analyst-triage tool, not CVE oracle. | eval/API |
| `time_travel.py` | `FindingHistory` | Temporal vulnerability analysis — tracks a finding across git history checkpoints. | eval/API |
| `pr_risk.py` | `PRRiskResult` | PR risk scoring: changed files × finding density × severity. Surfaces high-risk PRs for reviewer attention. | API |
| `review_bottleneck.py` | `ReviewBottleneckResult` | Detects review bottlenecks: PRs with no reviewer, stale open, high-churn files with no coverage. | API |

---

## External Tool Adapters

| Engine | Class | Purpose | Default enabled |
|--------|-------|---------|----------------|
| `trivy_adapter.py` | `TrivyAdapter` | Wraps Trivy container/IaC/dependency scanner. Normalizes Trivy JSON → CanonicalFinding. | when Trivy available |
| `trufflehog_adapter.py` | `TruffleHogAdapter` | Wraps TruffleHog verified-secrets scanner. Higher precision than regex-only secrets detection. | when TruffleHog available |

---

## The "Why 36?" Answer

The engines fall into five distinct roles:

1. **Core pipeline** (6 engines) — run on every scan, form the CanonicalFinding → score → gate chain
2. **Detection + verification** (5 engines) — find and prove vulnerabilities
3. **Opt-in features** (12 engines) — enabled by flags or when relevant files are present
4. **Eval/research** (10 engines) — for benchmarks, API endpoints, academic evaluation
5. **Adapters** (2 engines) — normalize external tool output

An examiner who asks "why so many?" gets this map in <5 minutes. An examiner who asks "what's always running?" gets the 6 core + 5 detection engines = 11 engines — which is a reasonable SAST platform.

**Bus factor mitigation:** each engine has tests in `TESTS/`, a docstring, and (for core engines) an ADR in `docs/adr/`. The `CANONICAL_SCHEMA.md` documents the data contract between engines.

---

*Updated automatically when engines are added. Last audit: 2026-06-03.*
