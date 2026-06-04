#!/usr/bin/env python3
"""
Post ACR-QA findings as GitHub PR comments
Sorted by severity: HIGH → MEDIUM → LOW
"""

import argparse
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from github import Github

from CORE import __version__
from DATABASE.database import Database

logger = logging.getLogger(__name__)


def clean_file_path(raw_path: str) -> str:
    """Strip CI/tmp prefixes from file paths for clean display in PR comments."""
    prefixes_to_strip = [
        "/tmp/pr-files/",
        "/home/runner/work/ACR-QA/ACR-QA/",
        "/home/runner/work/",
        "/tmp/",
    ]
    path = raw_path

    if "target-repo/" in path:
        return path.split("target-repo/")[-1]

    for prefix in prefixes_to_strip:
        if path.startswith(prefix):
            path = path[len(prefix) :]
            break

    return path


def format_severity_emoji(severity):
    """Get emoji for severity level"""
    return {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(severity, "⚪")


def format_detonation_trace(finding: dict) -> str:
    """
    Format the exploit-verification detonation trace for a PR comment.
    This is the 'ends the argument' block — shows the actual PoC that fired.
    """
    tier = finding.get("exploit_tier", "")
    proof_raw = finding.get("exploit_proof") or finding.get("proof_json") or ""
    if not tier or tier not in ("verified-exploitable", "verified-unexploitable"):
        return ""

    lines = []
    if tier == "verified-exploitable":
        lines.append("")
        lines.append("> **💥 EXPLOIT VERIFIED** — ACR-QA fired a real payload in a Docker sandbox")
        lines.append("> and received an exploitation signal. This finding is proven, not guessed.")
        lines.append("")
        # Parse proof JSON if available
        if proof_raw:
            try:
                import json as _json

                proof = _json.loads(proof_raw) if isinstance(proof_raw, str) else proof_raw
                if proof.get("payload"):
                    lines.append(f"> **Payload fired:** `{proof['payload']}`")
                if proof.get("evidence"):
                    evidence_snippet = str(proof["evidence"])[:200]
                    lines.append(f"> **Response signal:** `{evidence_snippet}`")
                if proof.get("category"):
                    lines.append(f"> **Category:** {proof['category']}")
            except Exception:
                pass
        lines.append("> **Fix priority:** BLOCK merge until resolved.")
        lines.append("")
    elif tier == "verified-unexploitable":
        lines.append("")
        lines.append("> **✅ Exploit attempt: NOT EXPLOITABLE** — payload fired; no exploitation signal.")
        lines.append("> Finding is still flagged (may be exploitable in different configuration).")
        lines.append("")

    return "\n".join(lines)


def format_verified_fix_trace(finding: dict) -> str:
    """Format the verified-remediation trace — proves fix killed the exploit."""
    fix_verified = finding.get("fix_verified", False)
    fix_diff = finding.get("fix_diff", "")
    if not fix_verified:
        return ""
    lines = [
        "",
        "> **🔒 FIX VERIFIED** — ACR-QA applied the AI patch and re-fired the exploit.",
        "> The exploit now FAILS on the patched code. Fix is cryptographically attested.",
        "",
    ]
    if fix_diff:
        lines.append("<details><summary>View verified fix diff</summary>")
        lines.append("")
        lines.append("```diff")
        for line in fix_diff.splitlines()[:20]:
            lines.append(line)
        if fix_diff.count("\n") > 20:
            lines.append("# ... (truncated)")
        lines.append("```")
        lines.append("")
        lines.append("</details>")
        lines.append("")
    return "\n".join(lines)


def format_inline_comment(finding):
    """Format a single finding into a short inline comment"""
    sev = finding.get("canonical_severity", "low")
    emoji = format_severity_emoji(sev)

    # Lead with exploit tier if available
    tier = finding.get("exploit_tier", "")
    tier_badge = ""
    if tier == "verified-exploitable":
        tier_badge = " 💥 **[EXPLOIT-PROVEN]**"
    elif tier == "verified-unexploitable":
        tier_badge = " ✅ [not exploitable in sandbox]"

    base_comment = (
        f"{emoji}{tier_badge} **{finding['canonical_rule_id']}** — {finding.get('category', 'security')}\n"
        f"> {finding['message']}\n"
        f"{sev.title()} Severity | [ACR-QA]"
    )

    # Add detonation trace
    trace = format_detonation_trace(finding)
    if trace:
        base_comment += "\n" + trace

    # Add verified fix trace
    fix_trace = format_verified_fix_trace(finding)
    if fix_trace:
        base_comment += "\n" + fix_trace

    fix_code = finding.get("fix_code")
    if fix_code and not finding.get("fix_verified"):
        suggestion = f"\n```suggestion\n{fix_code.strip()}\n```\n"
        return base_comment + "\n" + suggestion

    return base_comment


def format_pr_comment(findings):
    """
    Format findings as a single PR comment with severity sections

    Args:
        findings: List of finding dicts from database

    Returns:
        Formatted markdown comment
    """
    # Group by severity
    by_severity = {"high": [], "medium": [], "low": []}
    for f in findings:
        sev = f.get("canonical_severity", "low")
        by_severity[sev].append(f)

    # Count totals
    total = len(findings)
    high_count = len(by_severity["high"])
    medium_count = len(by_severity["medium"])
    low_count = len(by_severity["low"])

    # Separate exploit-verified findings
    verified = [f for f in findings if f.get("exploit_tier") == "verified-exploitable"]
    verified_fixes = [f for f in findings if f.get("fix_verified")]

    # Build comment
    lines = []
    lines.append("## 🛡️ ACR-QA — Provable AppSec Testing")
    lines.append("")

    # Exploit-verified banner (the wedge)
    if verified:
        lines.append(f"### 💥 {len(verified)} EXPLOIT-PROVEN Finding{'s' if len(verified) != 1 else ''}")
        lines.append("")
        lines.append("> These findings were **proven by firing real payloads in a Docker sandbox**.")
        lines.append("> Not alerts. Not estimates. Detonation traces with response evidence.")
        lines.append("> **Block this merge** until these are resolved.")
        lines.append("")
    if verified_fixes:
        lines.append(
            f"### 🔒 {len(verified_fixes)} AI Fix{'es' if len(verified_fixes) != 1 else ''} Cryptographically Verified"
        )
        lines.append("")
        lines.append("> These fixes were proven by re-firing the exploit on the patched code.")
        lines.append("> The exploit now fails. Evidence is ECDSA-signed.")
        lines.append("")

    lines.append(f"**Full scan:** {total} findings — {high_count} high · {medium_count} medium · {low_count} low")
    lines.append("")

    # Summary table
    lines.append("| | Count | Status |")
    lines.append("|---|:---:|---|")
    lines.append(f"| 💥 Exploit-verified (HIGH, proven) | {len(verified)} | Block merge |")
    lines.append(f"| 🔒 Fixes verified | {len(verified_fixes)} | Safe to merge after these |")
    lines.append(f"| 🔴 High (all) | {high_count} | Review required |")
    lines.append(f"| 🟡 Medium | {medium_count} | |")
    lines.append(f"| 🟢 Low | {low_count} | |")
    lines.append("")

    # EXPLOIT-VERIFIED findings first (the detonation traces)
    if verified:
        lines.append("---")
        lines.append("")
        lines.append("### 💥 Exploit-Proven Findings — Detonation Traces")
        lines.append("")
        for i, finding in enumerate(verified, 1):
            lines.append(
                f"#### {i}. `{finding['canonical_rule_id']}` in `{clean_file_path(finding.get('file_path', ''))}:{finding.get('line_number', '?')}`"
            )
            lines.append("")
            lines.append(f"> {finding['message']}")
            lines.append("")
            # The detonation trace
            trace = format_detonation_trace(finding)
            if trace:
                lines.append(trace)
            # Verified fix if available
            fix_trace = format_verified_fix_trace(finding)
            if fix_trace:
                lines.append(fix_trace)
            explanation = finding.get("explanation_text")
            if explanation:
                lines.append("<details><summary>AI Explanation</summary>")
                lines.append("")
                lines.append(explanation)
                lines.append("")
                lines.append("</details>")
                lines.append("")
            lines.append("---")
            lines.append("")

    # Non-verified HIGH severity findings
    non_verified_high = [f for f in by_severity["high"] if f.get("exploit_tier") != "verified-exploitable"]
    if non_verified_high:
        lines.append("---")
        lines.append("")
        lines.append("### 🔴 High Severity (Pattern-Detected)")
        lines.append("**⚠️ These issues should be addressed immediately**")
        lines.append("")

        for i, finding in enumerate(non_verified_high, 1):
            lines.append(f"#### {i}. {finding['canonical_rule_id']} - {finding.get('category', 'security')}")
            lines.append("")
            clean_path = clean_file_path(finding.get("file_path", ""))
            lines.append(f"**📍 Location:** `{clean_path}:{finding.get('line_number', '?')}`")
            lines.append("")
            lines.append("**📝 Issue:**")
            lines.append(f"> {finding['message']}")
            lines.append("")

            explanation = finding.get("explanation_text")
            if explanation:
                lines.append("**💡 AI Explanation:**")
                lines.append("")
                lines.append(explanation)
                lines.append("")

            lines.append("---")
            lines.append("")

    # MEDIUM severity findings (show first 5)
    if by_severity["medium"]:
        lines.append("### 🟡 Medium Priority Issues")
        lines.append("")

        to_show = by_severity["medium"][:5]
        for i, finding in enumerate(to_show, 1):
            lines.append(f"#### {i}. {finding['canonical_rule_id']}")
            lines.append(f"**Location:** `{clean_file_path(finding['file_path'])}:{finding['line_number']}`")
            lines.append(f"**Message:** {finding['message']}")

            explanation = finding.get("explanation_text")
            if explanation:
                # Truncate long explanations
                truncated = explanation[:200] + "..." if len(explanation) > 200 else explanation
                lines.append(f"**Explanation:** {truncated}")

            lines.append("")

        if len(by_severity["medium"]) > 5:
            remaining = len(by_severity["medium"]) - 5
            lines.append(f"*... and {remaining} more medium-priority issues*")
            lines.append("")

    # LOW severity summary
    if by_severity["low"]:
        lines.append("### 🟢 Low Priority Issues")
        lines.append("")
        lines.append(f"**Total:** {low_count} issues found")
        lines.append("")
        lines.append("*Low priority issues include style violations and minor improvements. ")
        lines.append("View the full report for details.*")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append(f"*Generated by [ACR-QA v{__version__}](https://github.com/ahmed-145/ACR-QA) - ")
    lines.append("Automated Code Review & Quality Assurance*")

    return "\n".join(lines)


def post_to_github(repo_name, pr_number, findings, summary_body, github_token):
    """
    Post comment to GitHub PR as an inline review

    Args:
        repo_name: Repository name (e.g., "user/repo")
        pr_number: Pull request number
        findings: List of finding dicts
        summary_body: Markdown text for the overall review body
        github_token: GitHub API token
    """
    try:
        g = Github(github_token)
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        # Get high findings for inline comments
        high_findings = [f for f in findings if f.get("canonical_severity", "low") == "high"]

        review_comments = []
        for finding in high_findings:
            try:
                line_no = int(finding["line_number"])
            except (ValueError, TypeError):
                continue

            review_comments.append(
                {"path": clean_file_path(finding["file_path"]), "line": line_no, "body": format_inline_comment(finding)}
            )

        # Post review comment
        commits = pr.get_commits()
        last_commit = commits[commits.totalCount - 1]

        pr.create_review(commit=last_commit, body=summary_body, event="COMMENT", comments=review_comments)

        logger.info(f"✅ Posted review to PR #{pr_number} with {len(review_comments)} inline comments")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to post comment: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Post ACR-QA findings to GitHub PR")
    parser.add_argument("--repo", required=True, help="Repository name (user/repo)")
    parser.add_argument("--pr-number", type=int, required=True, help="Pull request number")
    parser.add_argument("--run-id", type=int, help="Analysis run ID")
    parser.add_argument("--run-id-file", help="File containing run ID")

    args = parser.parse_args()

    # Get run ID
    run_id = args.run_id
    if not run_id and args.run_id_file:
        try:
            with open(args.run_id_file) as f:
                run_id = int(f.read().strip())
        except:
            pass

    if not run_id:
        # Get latest run
        db = Database()
        runs = db.get_recent_runs(limit=1)
        if runs:
            run_id = runs[0]["id"]
        else:
            logger.error("❌ No run ID found")
            sys.exit(1)

    # Get findings with explanations
    db = Database()
    findings = db.get_findings_with_explanations(run_id)

    if not findings:
        logger.info("ℹ️  No findings to post")
        return

    logger.info(f"📊 Found {len(findings)} issues")

    # Format comment
    comment = format_pr_comment(findings)

    # Post to GitHub
    github_token = os.getenv("GITHUB_TOKEN", "").strip()
    if not github_token:
        logger.error("❌ GITHUB_TOKEN not set")
        sys.exit(1)

    success = post_to_github(args.repo, args.pr_number, findings, comment, github_token)

    if success:
        logger.info("✅ PR comment posted successfully")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
