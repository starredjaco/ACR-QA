# ACR-QA — VS Code Extension

Run ACR-QA security scans, see findings as inline diagnostics, and get AI-generated fix suggestions — all without leaving VS Code.

## Features

- **Scan Workspace** — runs ACR-QA on your entire project, shows findings as squiggly underlines
- **Scan Current File** — scans only the open file's directory for fast feedback
- **Auto-scan on save** — optional; configurable per workspace
- **P4 Confirmed Tier mode** — show only 96.4%-precision findings (zero noise)
- **Two modes**: `server` (talks to your running ACR-QA instance) or `standalone` (runs CLI locally)

## Quick Start

### Standalone mode (no server needed)

1. Install the extension from the VS Code Marketplace
2. Set `acrqa.groqApiKey` in Settings (get a free key at [console.groq.com](https://console.groq.com))
3. Press `Ctrl+Shift+P` → `ACR-QA: Scan Workspace`

### Server mode

1. Start ACR-QA: `docker run -p 8000:8000 ghcr.io/ahmed-145/acrqa:latest`
2. Set `acrqa.serverUrl` to `http://localhost:8000`
3. Press `Ctrl+Shift+P` → `ACR-QA: Scan Workspace`

## Extension Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `acrqa.serverUrl` | `http://localhost:8000` | ACR-QA FastAPI server URL |
| `acrqa.apiKey` | `""` | API key for server mode |
| `acrqa.groqApiKey` | `""` | Groq key for standalone mode |
| `acrqa.mode` | `server` | `server` or `standalone` |
| `acrqa.severity` | `["critical","high","medium"]` | Severities to highlight |
| `acrqa.autoScanOnSave` | `false` | Scan on every save |
| `acrqa.confirmedTierOnly` | `false` | P4 Confirmed Tier only |

## Requirements

- VS Code 1.85+
- For standalone mode: Python 3.11+ with ACR-QA installed (`pip install -r requirements.txt`)
- For server mode: ACR-QA running on `acrqa.serverUrl`

## License

PolyForm Noncommercial 1.0.0 — see [LICENSE](../LICENSE). Noncommercial use only.
