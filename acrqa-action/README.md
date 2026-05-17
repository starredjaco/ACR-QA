# ACR-QA GitHub Action

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-ACR--QA-purple?logo=github)](https://github.com/marketplace/actions/acr-qa-code-review)

AI-powered code review for GitHub Actions. 10 static analysers + RAG-grounded AI explanations + ECDSA-signed provenance. 97.1% precision on OWASP benchmark repos.

## Quick Start

```yaml
- uses: ahmed-145/acrqa-action@v1
  with:
    target-dir: ./src
    fail-on: high
    groq-key: ${{ secrets.GROQ_API_KEY }}
```

## Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `target-dir` | Directory to scan | `.` |
| `fail-on` | Severity threshold to fail CI (`high`/`medium`/`low`/`none`) | `high` |
| `groq-key` | Groq API key for AI explanations (optional) | — |
| `repo-name` | Repository label for reports | `${{ github.repository }}` |
| `limit` | Max findings to return (0 = unlimited) | `0` |
| `output-sarif` | SARIF output file path | `acrqa-results.sarif` |

## Outputs

| Output | Description |
|--------|-------------|
| `findings-count` | Total findings detected |
| `high-count` | HIGH-severity count |
| `medium-count` | MEDIUM-severity count |
| `sarif-file` | Path to SARIF output |

## Full Example

```yaml
name: ACR-QA Security Review

on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    permissions:
      security-events: write   # required for SARIF upload
    steps:
      - uses: actions/checkout@v4

      - name: Run ACR-QA
        id: acrqa
        uses: ahmed-145/acrqa-action@v1
        with:
          target-dir: .
          fail-on: high
          groq-key: ${{ secrets.GROQ_API_KEY }}

      - name: Upload SARIF to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: ${{ steps.acrqa.outputs.sarif-file }}

      - name: Report findings
        run: |
          echo "Total: ${{ steps.acrqa.outputs.findings-count }}"
          echo "HIGH:  ${{ steps.acrqa.outputs.high-count }}"
```

## About

Built as a KSIU Computer Science thesis project (2026). Ships on PyPI (`pip install acrqa`) and the GitHub Actions Marketplace.

**Precision:** 97.1% on OWASP benchmark repos · **Cost:** $0 recurring (Groq free tier) · **Signing:** ECDSA-P256 attestation bundle
