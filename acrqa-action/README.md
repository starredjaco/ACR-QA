# ACR-QA — Provable AppSec Testing

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-ACR--QA-green?logo=github)](https://github.com/marketplace/actions/acr-qa-provable-appsec-testing)

**Exploit-proven findings. Verified fixes. Cryptographically attested.**

ACR-QA goes beyond static analysis: it fires real exploits in a Docker sandbox to prove
each finding is genuinely exploitable, and re-fires the exploit on the patched code to prove
your fix actually worked — then ECDSA-signs the entire chain to Sigstore Rekor.

> Exploit-verified remediation became the 2026 vanguard (Qualys/ZeroPath commercially;
> VulnRepairEval/PatchEval academically). ACR-QA converges for **first-party app source code,
> in CI, at $0**.

## Quick Start — Merge-blocking with 96.4% precision

```yaml
- uses: ahmed-145/acrqa-action@latest
  with:
    confirmed-only: "true"   # only exploit-verified or pattern-confirmed findings block the merge
    fail-on: high
    groq-key: ${{ secrets.GROQ_API_KEY }}   # optional — static scan runs without it
```

## Full Example — SARIF + GHAS upload

```yaml
name: ACR-QA Security Review

on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
    steps:
      - uses: actions/checkout@v4

      - name: Run ACR-QA
        id: acrqa
        uses: ahmed-145/acrqa-action@latest
        with:
          confirmed-only: "true"
          fail-on: high
          groq-key: ${{ secrets.GROQ_API_KEY }}

      - name: Upload SARIF to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: ${{ steps.acrqa.outputs.sarif-file }}

      - name: Print verified counts
        run: |
          echo "Exploit-proven: ${{ steps.acrqa.outputs.verified-count }}"
          echo "Confirmed Tier: ${{ steps.acrqa.outputs.confirmed-count }}"
```

## Inputs

| Input | Description | Default |
|---|---|---|
| `target-dir` | Directory to scan | `.` |
| `confirmed-only` | SARIF contains only Confirmed Tier (96.4% precision) | `true` |
| `fail-on` | Severity to fail CI on (`high`/`medium`/`low`/`none`) | `high` |
| `groq-key` | Groq API key — for AI explanations + LLM detection (optional) | — |
| `llm-detect` | Enable LLM-augmented detection (+7.4pp recall, gated) | `false` |
| `sarif-output` | SARIF output file path | `acrqa-results.sarif` |

## Outputs

| Output | Description |
|---|---|
| `verified-count` | Exploit-PROVEN findings (Docker sandbox confirmed real) |
| `confirmed-count` | Confirmed Tier findings (96.4% precision) |
| `total-count` | All findings (full output) |
| `sarif-file` | SARIF v2.1.0 path |
| `attestation-id` | Sigstore Rekor entry for ECDSA-signed attestation |

## Why ACR-QA vs incumbents

| Feature | Snyk/Semgrep/GHAS | Qualys/ZeroPath | **ACR-QA** |
|---|:---:|:---:|:---:|
| Static detection | ✅ | ✅ | ✅ |
| Exploit-verify finding | ❌ | ✅ | ✅ |
| Re-exploit to verify fix | ❌ | ✅ | ✅ |
| First-party SAST in CI | ✅ | ❌ (ETM layer) | ✅ |
| ECDSA-signed attestation | ❌ | ❌ | ✅ |
| Open source / $0 | ❌ | ❌ | ✅ |

## Numbers

- **96.4%** precision (Confirmed Tier, 30-repo corpus)
- **91.0%** recall (SecurityEval detectable CWEs)
- **25.1%** / **~48%** recall (RealVuln full / detectable — beats Semgrep 17.5%, Snyk 17.4, SonarQube 6.5%)
- **13** exploit categories (SQLi, CMDi, SSTI, SSRF, XXE, path-traversal, insecure-deser, open-redirect, ReDoS, LDAP, NoSQL, GraphQL, JWT-alg)

Built as a KSIU CS thesis project (2026). `pip install acrqa`. ECDSA-P256 + Sigstore Rekor attestation.
