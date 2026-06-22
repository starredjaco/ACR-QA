#!/usr/bin/env python3
"""Multi-pass Groq LLM security scanner for RealVuln benchmark.

Runs 3 specialized passes (injection, auth, config) against a repo's
codebase using llama-3.3-70b-versatile, combines findings, and returns
{file, cwe, line} dicts compatible with the RealVuln scorer.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq, RateLimitError

load_dotenv()

_GROQ_KEYS = [
    os.getenv("GROQ_API_KEY_1"),
    os.getenv("GROQ_API_KEY_2"),
    os.getenv("GROQ_API_KEY_3"),
    os.getenv("GROQ_API_KEY_4"),
]
_GROQ_KEYS = [k for k in _GROQ_KEYS if k]

# Free-tier TPM: llama-3.3-70b = 12K/min per key.
# Proactively rotate keys round-robin to maximize throughput.
MODEL = "llama-3.3-70b-versatile"
CHUNK_CHARS = 28_000  # ~7,000 tokens; stays within per-key TPM
MAX_TOKENS = 4096

SYSTEM_PROMPT = """You are an expert Python/web application security auditor.
You MUST output ONLY a valid JSON array of findings — no prose, no markdown fences.
Each finding: {"file": "relative/path.py", "line": <integer>, "cwe": "CWE-NNN", "description": "brief explanation"}
If you find nothing, output: []
Line numbers are 1-indexed. Be as precise as possible.
Report EVERY single instance — do not stop at the first occurrence. Scan ALL files given.
For HTML templates: the | safe filter is ALWAYS a vulnerability when the variable comes from user input."""

# ── Pass definitions ────────────────────────────────────────────────────────

PASSES = {
    "injection": {
        "focus": "injection and input-validation vulnerabilities",
        "cwes": [
            "CWE-89 SQL Injection: cursor.execute() / db.query() with string format/concat/f-string/% substitution",
            "CWE-79 XSS: Jinja2 {{ var | safe }}, Markup(user_input), render_template_string with user data, unescaped output in HTML. In HTML templates: EVERY occurrence of {{ variable | safe }} where variable is NOT a static constant.",
            "CWE-918 SSRF: requests.get/post/put/request/Session.get() where URL comes from user input (request.args, request.form, request.json, request.data)",
            "CWE-78 Command injection: subprocess/os.system/os.popen with shell=True or user-controlled args",
            "CWE-22 Path traversal: open()/send_file()/send_from_directory() with user-supplied filename; os.path.join(base, user_input) passed to open/read",
            "CWE-1336 SSTI: render_template_string() with user input, Jinja2 Environment(autoescape=False)",
            "CWE-611 XXE: lxml/ElementTree parse with user input, defusedxml not used",
            "CWE-601 Open redirect: redirect(request.args.get('next')) or similar without URL validation",
            "CWE-94 Code injection: eval()/exec() with user input",
            "CWE-943 NoSQL injection: MongoDB/Redis queries built from user input",
        ],
        "extra": (
            "CRITICAL — For XSS in HTML templates (.html/.jinja2 files): "
            "scan EVERY {{ ... | safe }} occurrence. Report the file and exact line number of the line containing '| safe'. "
            "Variables like message, content, body, text, name, comment, username, feedback, description "
            "passed to | safe are ALWAYS CWE-79 vulnerabilities. Report ALL of them. "
            "For Python views.py: if a variable from request.args/form/json is passed to render_template(), "
            "it is CWE-79 at the line where render_template() is called. "
            "For SSRF: trace variables — if a URL variable is set from request.args/form/json, that is SSRF. "
            "Report the line where the dangerous function is called, not where the variable is assigned."
        ),
    },
    "auth": {
        "focus": "authentication, authorization, and session management vulnerabilities",
        "cwes": [
            "CWE-306 Missing authentication: Flask/Django route (@app.route, @blueprint.route, @api.route, MethodView) that performs sensitive operations WITHOUT @login_required, without checking session/current_user/g.user",
            "CWE-352 CSRF: HTML forms (POST/PUT/DELETE) that do NOT include a CSRF token. Also Flask routes that accept POST data without CSRF middleware.",
            "CWE-639 IDOR: Database queries fetching records by user-supplied ID WITHOUT verifying ownership",
            "CWE-307 Brute force: Login endpoints without rate limiting or lockout",
            "CWE-384 Session fixation: login_user() or session auth without session rotation/regeneration",
            "CWE-287 Improper authentication: passwords compared with == instead of secure hash",
            "CWE-522 Insecure credential storage: storing passwords WITHOUT hashing (plain text), or using weak hash",
            "CWE-256 Plaintext password storage: password column stores plain string, no hashing in model",
            "CWE-916 Weak password hash: MD5/SHA1/SHA256 used for passwords without salt",
            "CWE-862 Missing authorization: admin/privileged routes without role check",
            "CWE-284 Broken access control: admin role based on username string comparison instead of role field",
        ],
        "extra": (
            "CRITICAL: For EACH Flask route (@app.route / @blueprint.route / MethodView): check: "
            "(1) Does it modify data or access user-specific data WITHOUT session/current_user check? -> CWE-306 "
            "(2) Does it accept POST form data without CSRF token in the HTML template? -> CWE-352 "
            "(3) Does it query DB by user-supplied ID without ownership check? -> CWE-639 "
            "For session fixation (CWE-384): any login_user() / session assignment after auth WITHOUT session rotation. "
            "For plaintext passwords (CWE-522/CWE-256): check Model __init__, check login comparisons (== vs check_password_hash). "
            "Report ALL such routes — there may be MANY. "
            "For HTML forms: if a form has method='post' and no csrf_token -> CWE-352 at the form open tag line."
        ),
    },
    "config": {
        "focus": "configuration, credential, data-exposure, and cryptography vulnerabilities",
        "cwes": [
            "CWE-798 Hardcoded credentials: SECRET_KEY, PASSWORD, API_KEY, TOKEN, JWT_SECRET assigned a literal string",
            "CWE-259 Hardcoded password: password variable assigned a string literal, or default password in function args",
            "CWE-321 Hardcoded crypto key: crypto key or HMAC key as string literal",
            "CWE-489 Debug mode: app.run(debug=True), DEBUG=True in config",
            "CWE-215 Info through debug: app.config['DEBUG'] = True",
            "CWE-1004 Missing HttpOnly cookie: auth cookie without httponly=True",
            "CWE-614 Missing Secure cookie: session cookie without secure=True",
            "CWE-942 CORS misconfiguration: CORS(app) with origins='*' or allow_all=True",
            "CWE-327 Broken crypto: MD5/SHA1 for non-password hashing, DES/RC4, ECB mode",
            "CWE-338 Weak PRNG: random.random()/random.randint() for security tokens/OTP/CSRF",
            "CWE-295 Improper cert validation: requests with verify=False",
            "CWE-312 Cleartext sensitive data: logging passwords, writing credentials to files",
            "CWE-209 Error info: except Exception as e: return str(e) / return traceback.format_exc()",
            "CWE-200 Sensitive data exposure: API endpoint or serialization returns password/token field",
            "CWE-16 Security misconfiguration: X-XSS-Protection header disabled, security headers off",
        ],
        "extra": (
            "For hardcoded credentials: look for ANY string literal assigned to variables containing "
            "SECRET, KEY, PASSWORD, PASSWD, TOKEN, API_KEY, CLIENT_SECRET. Also dict assignments like "
            "app.config['SECRET_KEY'] = 'literal'. "
            "For debug mode: app.config['DEBUG'] = True is CWE-215. "
            "For data exposure (CWE-200): if a serialization method (serialize(), to_dict(), jsonify()) "
            "includes a password field without filtering, report that line. "
            "For cookies: look for set_cookie() and session config. "
            "Report EVERY file/line where a hardcoded credential appears."
        ),
    },
}


# ── File bundling ────────────────────────────────────────────────────────────


def _priority_score(path: Path) -> int:
    name = path.name.lower()
    parts = {p.lower() for p in path.parts}
    if any(x in name for x in ("route", "view", "api", "endpoint", "controller", "app", "main", "urls")):
        return 0
    if any(x in name for x in ("auth", "login", "user", "account", "session", "permission", "security")):
        return 1
    if any(x in name for x in ("model", "schema", "db", "database", "query")):
        return 2
    if any(x in name for x in ("form", "template", "html")):
        return 3
    if "test" in parts or "tests" in parts or name.startswith("test_"):
        return 10
    return 5


def bundle_repo_chunks(repo_path: str) -> list[str]:
    """Return list of code chunks, each <= CHUNK_CHARS characters."""
    repo = Path(repo_path)
    files: list[tuple[int, Path]] = []
    for ext in ("*.py", "*.html", "*.jinja2", "*.jinja", "*.j2"):
        for p in repo.rglob(ext):
            if any(x in str(p) for x in (".git", "__pycache__", "node_modules", ".venv", "venv", "env/")):
                continue
            files.append((_priority_score(p), p))
    files.sort(key=lambda x: (x[0], str(x[1])))

    chunks: list[str] = []
    current: list[str] = []
    current_size = 0
    for _, p in files:
        try:
            content = p.read_text(errors="replace")
        except Exception:
            continue
        rel = str(p.relative_to(repo)).replace("\\", "/")
        block = f"\n=== FILE: {rel} ===\n{content}\n"
        if len(block) > CHUNK_CHARS:
            lines = block.splitlines(keepends=True)
            sub_buf: list[str] = []
            sub_size = 0
            for line in lines:
                if sub_size + len(line) > CHUNK_CHARS and sub_buf:
                    chunks.append("".join(sub_buf))
                    sub_buf = []
                    sub_size = 0
                sub_buf.append(line)
                sub_size += len(line)
            if sub_buf:
                if current_size + sub_size > CHUNK_CHARS and current:
                    chunks.append("".join(current))
                    current = sub_buf
                    current_size = sub_size
                else:
                    current.extend(sub_buf)
                    current_size += sub_size
            continue
        if current_size + len(block) > CHUNK_CHARS and current:
            chunks.append("".join(current))
            current = []
            current_size = 0
        current.append(block)
        current_size += len(block)
    if current:
        chunks.append("".join(current))
    return chunks


# ── Groq call with proactive key rotation ────────────────────────────────────

_call_count = 0


def _call_groq(user_msg: str, pass_name: str) -> str:
    global _call_count
    n = len(_GROQ_KEYS)
    start_idx = _call_count % n
    _call_count += 1

    for attempt in range(n * 3):
        key_idx = (start_idx + attempt) % n
        key = _GROQ_KEYS[key_idx]
        try:
            client = Groq(api_key=key)
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=MAX_TOKENS,
                temperature=0,
            )
            return resp.choices[0].message.content or "[]"
        except RateLimitError:
            wait = 15 * (attempt // n + 1)
            print(f"    rate limit key {key_idx+1}, waiting {wait}s...", flush=True)
            time.sleep(wait)
        except Exception as e:
            print(f"    Groq error ({pass_name}): {e}", flush=True)
            time.sleep(3)
    return "[]"


# ── Output parsing ───────────────────────────────────────────────────────────

_CWE_RE = re.compile(r"CWE-\d+")


def _parse_output(text: str) -> list[dict]:
    text = text.strip()
    text = re.sub(r"^```[a-z]*\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n?```$", "", text, flags=re.MULTILINE)
    text = text.strip()

    for candidate in (text, re.search(r"\[.*\]", text, re.DOTALL)):
        raw = candidate if isinstance(candidate, str) else (candidate.group(0) if candidate else None)
        if not raw:
            continue
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

    bracket_start = text.find("[")
    if bracket_start != -1:
        for end in range(len(text), bracket_start, -1):
            try:
                data = json.loads(text[bracket_start:end] + "]")
                if isinstance(data, list):
                    return data
            except Exception:
                continue
    return []


def _normalise(findings: list[dict], repo_path: str) -> list[dict]:
    repo = Path(repo_path)
    out = []
    seen: set[tuple] = set()
    for f in findings:
        if not isinstance(f, dict):
            continue
        file_raw = str(f.get("file") or f.get("path") or "").replace("\\", "/").lstrip("./")
        cwe_raw = str(f.get("cwe") or "")
        m = _CWE_RE.search(cwe_raw)
        if not m:
            continue
        cwe = m.group(0)
        line = f.get("line") or f.get("start_line") or 0
        try:
            line = int(line)
        except (TypeError, ValueError):
            line = 0
        for prefix in (repo.name + "/", repo.name + "\\"):
            if file_raw.startswith(prefix):
                file_raw = file_raw[len(prefix) :]
        key = (file_raw, cwe, line // 5)
        if key in seen:
            continue
        seen.add(key)
        out.append({"file": file_raw, "cwe": cwe, "line": line, "description": f.get("description", "")})
    return out


# ── Public API ───────────────────────────────────────────────name──────────────


def scan_repo(repo_path: str, verbose: bool = True) -> list[dict]:
    """Run all 3 passes across chunked codebase; return combined normalised findings."""
    chunks = bundle_repo_chunks(repo_path)
    total_chars = sum(len(c) for c in chunks)
    if verbose:
        print(f"    chunks: {len(chunks)}, total {total_chars:,} chars (~{total_chars//4:,} tokens)", flush=True)

    all_findings: list[dict] = []
    for pass_name, cfg in PASSES.items():
        cwe_list = "\n".join(f"  - {c}" for c in cfg["cwes"])
        pass_raw_count = 0
        pass_norm_count = 0
        for ci, chunk in enumerate(chunks[:MAX_CHUNKS_PER_PASS]):
            effective_chunks = min(len(chunks), MAX_CHUNKS_PER_PASS)
            chunk_label = f"chunk {ci+1}/{effective_chunks}"
            user_msg = (
                f"You are scanning for {cfg['focus']}. {chunk_label}\n\n"
                f"Target CWEs to find:\n{cwe_list}\n\n"
                f"Additional guidance:\n{cfg['extra']}\n\n"
                f"Codebase ({chunk_label}):\n{chunk}\n\n"
                "Output ONLY a JSON array of ALL findings from THIS chunk. "
                "Be exhaustive — missing a vulnerability is worse than a false positive."
            )
            raw = _call_groq(user_msg, f"{pass_name}[{ci}]")
            parsed = _parse_output(raw)
            norm = _normalise(parsed, repo_path)
            pass_raw_count += len(parsed)
            pass_norm_count += len(norm)
            all_findings.extend(norm)
            time.sleep(1)
        if verbose:
            print(f"    pass={pass_name}: raw={pass_raw_count} -> normalised={pass_norm_count}", flush=True)

    seen: set[tuple] = set()
    deduped = []
    for f in all_findings:
        key = (f["file"], f["cwe"], (f["line"] or 0) // 5)
        if key not in seen:
            seen.add(key)
            deduped.append(f)
    return deduped


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python llm_security_scanner.py <repo_path>")
        sys.exit(1)
    findings = scan_repo(sys.argv[1])
    print(json.dumps(findings, indent=2))


# Allow callers to limit chunks processed (to skip very large repos)
MAX_CHUNKS_PER_PASS = int(os.getenv("LLM_MAX_CHUNKS", "8"))
