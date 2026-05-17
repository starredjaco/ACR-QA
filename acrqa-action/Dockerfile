FROM python:3.11-slim

LABEL org.opencontainers.image.title="ACR-QA Action"
LABEL org.opencontainers.image.description="AI-powered code review for GitHub Actions"
LABEL org.opencontainers.image.version="4.6.0"
LABEL org.opencontainers.image.authors="Ahmed Mahmoud Abbas <ahmedabbass871@gmail.com>"
LABEL org.opencontainers.image.source="https://github.com/ahmed-145/acr-qa"
LABEL org.opencontainers.image.licenses="MIT"

# Install system dependencies for static analysis tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# Install acrqa from PyPI
RUN pip install --no-cache-dir acrqa==4.6.0

# Install optional JS/Node analysers
RUN npm install -g eslint semgrep 2>/dev/null || true

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
