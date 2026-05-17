#!/bin/bash
set -e

TARGET="${ACRQA_TARGET_DIR:-.}"
FAIL_ON="${ACRQA_FAIL_ON:-high}"
REPO="${ACRQA_REPO_NAME:-local}"
LIMIT="${ACRQA_LIMIT:-0}"
SARIF="${ACRQA_OUTPUT_SARIF:-acrqa-results.sarif}"

echo "::group::ACR-QA v4.6.0 — scanning ${TARGET}"

# Build CLI args
ARGS="--target-dir ${TARGET} --repo ${REPO}"
[ "${LIMIT}" != "0" ] && ARGS="${ARGS} --limit ${LIMIT}"
[ -n "${SARIF}" ] && ARGS="${ARGS} --sarif ${SARIF}"

# Run scan
acrqa ${ARGS} --json-out /tmp/acrqa-results.json || SCAN_EXIT=$?

# Parse results and set outputs
if [ -f /tmp/acrqa-results.json ]; then
    TOTAL=$(python3 -c "import json,sys; d=json.load(open('/tmp/acrqa-results.json')); print(len(d.get('findings',[])))" 2>/dev/null || echo 0)
    HIGH=$(python3 -c "import json,sys; d=json.load(open('/tmp/acrqa-results.json')); print(sum(1 for f in d.get('findings',[]) if f.get('severity','').lower()=='high'))" 2>/dev/null || echo 0)
    MED=$(python3 -c "import json,sys; d=json.load(open('/tmp/acrqa-results.json')); print(sum(1 for f in d.get('findings',[]) if f.get('severity','').lower()=='medium'))" 2>/dev/null || echo 0)
    echo "findings-count=${TOTAL}" >> "$GITHUB_OUTPUT"
    echo "high-count=${HIGH}" >> "$GITHUB_OUTPUT"
    echo "medium-count=${MED}" >> "$GITHUB_OUTPUT"
    echo "sarif-file=${SARIF}" >> "$GITHUB_OUTPUT"
    echo "::notice::ACR-QA found ${TOTAL} findings (${HIGH} HIGH, ${MED} MEDIUM)"
fi

echo "::endgroup::"

# Fail CI based on threshold
case "${FAIL_ON}" in
    high)   [ "${HIGH:-0}" -gt 0 ] && { echo "::error::${HIGH} HIGH-severity findings detected"; exit 1; } ;;
    medium) [ "${MED:-0}" -gt 0 ] || [ "${HIGH:-0}" -gt 0 ] && { echo "::error::Findings at or above MEDIUM severity"; exit 1; } ;;
    none)   ;;
esac

exit 0
