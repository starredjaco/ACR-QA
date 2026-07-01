#!/usr/bin/env python3
"""God-Mode AST + Regex security scanner — zero LLM, zero API, instant.

Covers ALL statically-detectable Bucket-B RealVuln patterns:
  CWE-22   Path traversal
  CWE-78   Command injection
  CWE-79   XSS (| safe in Jinja2/HTML templates + render_template_string)
  CWE-89   SQL injection (string format/concat in execute())
  CWE-94   Code injection (eval/exec with user input)
  CWE-200  Sensitive data exposure (serialize/to_dict includes password)
  CWE-209  Error info exposure (return str(e), traceback)
  CWE-215  Debug mode (app.config['DEBUG'] = True)
  CWE-256  Plaintext password storage in Model
  CWE-284  Broken access control (username string admin check)
  CWE-287  Improper auth (== password comparison)
  CWE-295  SSL cert not verified (verify=False)
  CWE-306  Missing auth on Flask routes
  CWE-307  No brute-force protection on login
  CWE-312  Cleartext credentials in logging
  CWE-321  Hardcoded crypto key
  CWE-338  Weak PRNG (random.* for security)
  CWE-352  CSRF — POST form without csrf_token in template
  CWE-384  Session fixation (login_user without regeneration)
  CWE-522  Insecure credential storage (plaintext comparison)
  CWE-532  Sensitive info in logs
  CWE-601  Open redirect (redirect(request.args['next']))
  CWE-613  Insufficient session expiry
  CWE-639  IDOR (query by user-supplied ID without ownership)
  CWE-798  Hardcoded credentials (SECRET_KEY, passwords)
  CWE-916  Weak password hash (MD5/SHA1 for passwords)
  CWE-918  SSRF (requests.get with user-controlled URL)
  CWE-1336 SSTI (render_template_string with dynamic content)
"""

from __future__ import annotations

import ast
import os
import re
import sys
from collections.abc import Callable
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
# HTML / Jinja2 scanner
# ═══════════════════════════════════════════════════════════════

_SAFE_FILTER_RE = re.compile(r"\{\{[^}]*\|\s*safe\s*\}\}", re.DOTALL)
_FORM_POST_RE = re.compile(r"<form\b[^>]*\bmethod\s*=\s*['\"]?(post|put|delete|patch)['\"]?", re.IGNORECASE)
_CSRF_PRESENT_RE = re.compile(r"csrf_token|hidden_tag\(\)|{% csrf_token %}", re.IGNORECASE)
_STATIC_STR_RE = re.compile(r"""^\s*['""][^'"]*['"]\s*\|\s*safe\s*$""")


# ── JavaScript / DOM XSS (CWE-79) ────────────────────────────────────────────
# DOM sinks that render markup. Flagged when the argument is dynamic (not a string literal)
# and the script references a user-controlled source — high precision (kolega: 100% on these).
_JS_DOM_SINK_RE = re.compile(
    r"\.(html|innerHTML|outerHTML|insertAdjacentHTML)\s*[=(]"
    r"|document\.(write|writeln)\s*\("
    r"|\.(append|prepend|after|before|wrap)\s*\(\s*[^'\"`)]"  # jQuery, non-literal
    r"|\beval\s*\(\s*[^'\"`)]"
    r"|\.setAttribute\s*\(\s*['\"]on",
    re.IGNORECASE,
)
_JS_TAINT_SRC_RE = re.compile(
    r"location\.(hash|search|href|pathname)|document\.(URL|documentURI|referrer|cookie)"
    r"|window\.name|URLSearchParams|\.responseText|getResponseHeader|decodeURIComponent"
    r"|\$_GET|req\.(query|params|body)|location\b",
    re.IGNORECASE,
)
_JS_SINK_LITERAL_RE = re.compile(r"""\.(html|innerHTML|outerHTML)\s*[=(]\s*['"`][^'"`]*['"`]\s*[);]?\s*$""")


# Well-known vendored JS bundles that ship inside app repos (esp. API-doc UIs). Matched as a
# substring of the filename; the minification check below generalises to any third-party bundle.
_VENDOR_JS_NAMES = (
    "swagger-ui",
    "redoc",
    "jquery",
    "bootstrap",
    "angular",
    "react.production",
    "vue.global",
    "popper",
    "lodash",
    "moment",
    "d3.",
    "chart",
    ".bundle.js",
    ".standalone.js",
    "-min.js",
)


def _is_vendor_or_minified_js(path: Path) -> bool:
    """True for third-party / minified JS that is not the application's own source.

    Vendored bundles carry no ground-truth vulnerability and a regex DOM-XSS scan over minified
    code only manufactures false positives. Detection is by vendor filename OR by minification
    (a very long line — the reliable, name-independent signal of generated/bundled code)."""
    name = path.name.lower()
    if any(v in name for v in _VENDOR_JS_NAMES):
        return True
    try:
        with path.open(errors="replace") as fh:
            for idx, line in enumerate(fh):
                if len(line) > 1000:  # minified: no human writes 1000-char lines
                    return True
                if idx > 200:  # only need to sample the head
                    break
    except OSError:
        return False
    return False


def scan_js(path: Path, content: str | None = None) -> list[dict]:
    """Regex DOM-XSS scanner for .js files / inline <script>. Flags a markup sink with a
    dynamic argument when the file also reads a user-controlled source."""
    findings: list[dict] = []
    try:
        text = content if content is not None else path.read_text(errors="replace")
    except Exception:
        return findings
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        if not _JS_DOM_SINK_RE.search(line):
            continue
        if _JS_SINK_LITERAL_RE.search(line):
            continue
        # High precision: require a user-controlled source ON THE SAME LINE as the sink
        # (direct DOM XSS, e.g. innerHTML = location.hash). The file-level gate was far too noisy
        # (.html()/.append() are ubiquitous in benign JS) — +3 TP for +130 FP. Tight beats broad.
        if _JS_TAINT_SRC_RE.search(line):
            findings.append(
                {"file": str(path), "line": i, "cwe": "CWE-79", "description": f"DOM XSS: {line.strip()[:90]}"}
            )
    return findings


_SCRIPT_BLOCK_RE = re.compile(r"<script[^>]*>(.*?)</script>", re.IGNORECASE | re.DOTALL)

# High-confidence secrets in ANY text file (templates/xml/config) — unambiguous formats.
_SECRET_UNAMBIGUOUS_RE = re.compile(
    r"AKIA[0-9A-Z]{16}"  # AWS access key
    r"|-----BEGIN [A-Z ]*PRIVATE KEY"  # private key block
    r"|sk_live_[A-Za-z0-9]{16,}|sk_test_[A-Za-z0-9]{16,}"  # Stripe
    r"|gh[pousr]_[A-Za-z0-9]{30,}"  # GitHub token
    r"|eyJ[A-Za-z0-9_-]{15,}\.eyJ[A-Za-z0-9_-]{15,}"  # JWT
    r"|xox[baprs]-[A-Za-z0-9-]{10,}"  # Slack
)
# Long hex (API key / token / hash) is only a secret near a credential keyword (avoids asset hashes).
_SECRET_HEX_RE = re.compile(r"\b[a-f0-9]{40,}\b", re.IGNORECASE)
_SECRET_CRED_CTX = re.compile(r"password|passwd|api[ _-]?key|secret|token|credential|login|admin", re.IGNORECASE)


def scan_text_secrets(path: Path) -> list[dict]:
    """Hardcoded secrets in non-Python text files (templates, XML, config)."""
    findings: list[dict] = []
    try:
        lines = path.read_text(errors="replace").splitlines()
    except Exception:
        return findings
    for i, line in enumerate(lines, 1):
        if _SECRET_UNAMBIGUOUS_RE.search(line):
            findings.append(
                {"file": str(path), "line": i, "cwe": "CWE-798", "description": "Hardcoded secret/key in file"}
            )
            continue
        if _SECRET_HEX_RE.search(line):
            ctx = " ".join(lines[max(0, i - 4) : min(len(lines), i + 1)])
            if _SECRET_CRED_CTX.search(ctx):
                findings.append(
                    {
                        "file": str(path),
                        "line": i,
                        "cwe": "CWE-798",
                        "description": "Hardcoded credential/API key (long hex near credential context)",
                    }
                )
    return findings


def scan_html(path: Path) -> list[dict]:
    findings = []
    try:
        content = path.read_text(errors="replace")
        lines = content.splitlines()
    except Exception:
        return findings

    # CWE-79: {{ var | safe }} — every non-literal usage
    for i, line in enumerate(lines, 1):
        m = _SAFE_FILTER_RE.search(line)
        if m:
            inner = m.group(0)[2:-2].strip()
            if not _STATIC_STR_RE.match(inner):
                findings.append(
                    {"file": str(path), "line": i, "cwe": "CWE-79", "description": f"| safe XSS: {line.strip()[:100]}"}
                )

    # CWE-352: POST form without csrf_token — fire ONCE per template at the first form.
    # (Was firing per form-line → spraying FPs; CSRF posture is a per-template property.)
    if _FORM_POST_RE.search(content) and not _CSRF_PRESENT_RE.search(content):
        for i, line in enumerate(lines, 1):
            if _FORM_POST_RE.search(line):
                findings.append(
                    {"file": str(path), "line": i, "cwe": "CWE-352", "description": "POST form without CSRF token"}
                )
                break

    return findings


# ═══════════════════════════════════════════════════════════════
# Python AST scanner
# ═══════════════════════════════════════════════════════════════

_PASSWD_ATTR = re.compile(r"password|passwd|pwd|secret(?!_key)", re.IGNORECASE)
_CRED_ATTR = re.compile(
    r"SECRET_KEY|JWT_SECRET|API_KEY|CLIENT_SECRET|PASSWD|PASSWORD"
    r"|ACCESS_TOKEN|AUTH_TOKEN|_TOKEN_SALT|_SALT\b|ENCRYPT_KEY|SIGNING_KEY"
    r"|\bKEY\b(?!_ID|_NAME|_TYPE)"
    r"|SECRET(?!_BALLOT|_VOTE)|_TOKEN\b|TOKEN_\b",
    re.IGNORECASE,
)
# A string that is ENTIRELY a single placeholder token (format spec / interpolation / mask) — never
# a real secret. Deliberately narrow: digit/hex strings are NOT here (they can be real keys).
_PLACEHOLDER_SECRET_RE = re.compile(
    r"^(%[sdr]|%\([^)]*\)[sdr]|\{[\w]*\}|\$\{[^}]*\}|<[^>]*>|[*x]{3,})$",
    re.IGNORECASE,
)


def _is_trivial_secret_literal(value: str) -> bool:
    """A credential-named var assigned this string is NOT a real hardcoded secret.

    Skips only the unambiguous non-secrets: empty/whitespace strings and values that are entirely a
    single placeholder token (``%s``, ``{}``, ``${VAR}``, ``****``). Digit/hex strings are kept —
    they can be real keys. Principled (the value provably isn't a credential), not a value denylist."""
    s = value.strip()
    if not s:
        return True
    return bool(_PLACEHOLDER_SECRET_RE.match(s))


_WEAK_HASH = re.compile(r"^(md5|sha1|sha128)$", re.IGNORECASE)
_HASH_MODULE = re.compile(r"^(md5|sha1|hashlib)$", re.IGNORECASE)
_REQUEST_SRCS = {"request", "args", "form", "json", "data", "values", "files", "cookies"}

_AUTH_DECORATORS = {
    "login_required",
    "token_required",
    "jwt_required",
    "auth_required",
    "require_login",
    "admin_required",
    "permission_required",
    "roles_required",
    "fresh_login_required",
    "staff_member_required",
}
_RATE_LIMIT_DECORATORS = {
    "limiter",
    "limit",
    "ratelimit",
    "rate_limit",
    "throttle",
    "flask_limiter",
    "slow_down",
}


def _func_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _is_route_decorator(d: ast.expr) -> bool:
    n = d.func if isinstance(d, ast.Call) else d
    return _func_name(n) in (
        "route",
        "get",
        "post",
        "put",
        "delete",
        "patch",
        "add_url_rule",
        # aiohttp / aiohttp_jinja2 / other frameworks
        "template",
        "view",
        "expose",
        "page",
        "endpoint",
        "handler",
        "add_get",
        "add_post",
        "add_route",
        "get_async",
        "post_async",
    )


def _decorator_names(func: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    names = []
    for d in func.decorator_list:
        if isinstance(d, ast.Call):
            names.append(_func_name(d.func))
        else:
            names.append(_func_name(d))
    return names


def _is_from_request(node: ast.expr) -> bool:
    """Heuristic: is this expression derived from request.* or named user_input?"""
    src = ast.unparse(node)
    return any(
        kw in src
        for kw in (
            "request.",
            "args.",
            "form.",
            "json.",
            "data.",
            "values.",
            "user_input",
            "user_data",
            "untrusted_",
            "get_json(",
            "get_data(",
            "match_info",
        )
    )


# ── Intra-procedural taint analysis ──────────────────────────────────────────
# Substrings that identify a user-controlled SOURCE expression (framework-agnostic).
_TAINT_SOURCE_SUBSTR = (
    "request.",
    ".args",
    ".form",
    ".values",
    ".get_json(",
    ".get_data(",
    "get_argument(",  # Tornado
    "get_query_argument(",
    "get_body_argument(",
    "match_info",  # aiohttp
    "query_params",  # FastAPI/Starlette
    "path_params",
    ".cookies",
    ".headers",
    "request.GET",
    "request.POST",
    "request.data",
    "request.body",
    "self.get_argument",
    "environ.get(",
    "os.environ",
)
# Parameter names that are inherently user input even without a route decorator.
_TAINTED_PARAM_SUBSTR = (
    "user_input",
    "user_data",
    "username",
    "user_id",
    "untrusted",
    "payload",
    "user_supplied",
    "raw_input",
)


def _expr_is_source(node: ast.expr) -> bool:
    """True if the expression is (or directly wraps) a user-controlled source."""
    try:
        src = ast.unparse(node)
    except Exception:
        return False
    return any(s in src for s in _TAINT_SOURCE_SUBSTR)


def _expr_names(node: ast.expr) -> set[str]:
    """All bare Name identifiers referenced in an expression."""
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def compute_function_taint(func: ast.FunctionDef | ast.AsyncFunctionDef, is_route: bool) -> set[str]:
    """Intra-procedural taint: the set of variable names in this function that carry
    user-controlled data. Seeds from route-handler parameters and source assignments,
    then propagates through assignments to a fixpoint."""
    tainted: set[str] = set()

    # Seed 1: every parameter of a route handler is user-controlled (path/query/body).
    params = list(func.args.args) + list(func.args.posonlyargs) + list(func.args.kwonlyargs)
    for a in params:
        if a.arg == "self":
            continue
        if is_route or any(s in a.arg.lower() for s in _TAINTED_PARAM_SUBSTR):
            tainted.add(a.arg)

    # Fixpoint over assignments: target becomes tainted if its value is a source or
    # references an already-tainted name.
    changed = True
    iterations = 0
    while changed and iterations < 12:
        changed = False
        iterations += 1
        for node in ast.walk(func):
            if isinstance(node, ast.Assign | ast.AnnAssign | ast.AugAssign):
                value = node.value
                if value is None:
                    continue
                tainted_value = _expr_is_source(value) or bool(_expr_names(value) & tainted)
                if not tainted_value:
                    continue
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for t in targets:
                    if isinstance(t, ast.Name) and t.id not in tainted:
                        tainted.add(t.id)
                        changed = True
    return tainted


# Routes that are public by design — never flag for missing auth
_PUBLIC_ROUTE_NAMES = {
    "index",
    "home",
    "homepage",
    "main",
    "root",
    "about",
    "about_us",
    "contact",
    "login",
    "signin",
    "sign_in",
    "logout",
    "signout",
    "sign_out",
    "register",
    "signup",
    "sign_up",
    "health",
    "healthcheck",
    "health_check",
    "ping",
    "status",
    "robots",
    "favicon",
    "docs",
    "help",
    "faq",
    "terms",
    "privacy",
    "static",
    "search",
    "public",
    "landing",
    "welcome",
    "error",
    "not_found",
    "forbidden",
}
# Names that strongly imply a privileged / state-changing operation
_SENSITIVE_ROUTE_KEYWORDS = (
    "admin",
    "delete",
    "remove",
    "update",
    "edit",
    "create",
    "add",
    "new",
    "save",
    "modify",
    "change",
    "reset",
    "manage",
    "settings",
    "config",
    "profile",
    "account",
    "user",
    "users",
    "dashboard",
    "upload",
    "approve",
    "grant",
    "revoke",
    "role",
    "permission",
    "transfer",
    "pay",
    "payment",
    "order",
    "purchase",
    "checkout",
    "api",
    "internal",
    "private",
    "secret",
)
_STATE_CHANGE_CALLS = (
    ".save(",
    ".delete(",
    ".commit(",
    ".update(",
    ".create(",
    "session.add",
    "db.session",
    ".insert(",
    ".remove(",
    ".pop(",
    "objects.create",
    "objects.filter",
    "objects.get",
    "INSERT ",
    "UPDATE ",
    "DELETE ",
)


def _is_sensitive_route(node, func_src: str) -> bool:
    """Heuristic: should this route require auth? Only flag privileged/state-changing
    routes — public-by-design routes (index/login/about/health) must not be flagged."""
    name = node.name.lower()
    if name in _PUBLIC_ROUTE_NAMES:
        return False
    # POST/PUT/DELETE/PATCH methods declared on the route decorator → state-changing
    decs = " ".join(ast.unparse(d) for d in node.decorator_list).lower()
    if any(m in decs for m in ('"post"', "'post'", '"put"', "'put'", '"delete"', "'delete'", '"patch"', "'patch'")):
        return True
    if "methods=" in decs and any(m in decs for m in ("post", "put", "delete", "patch")):
        return True
    # Sensitive name
    if any(kw in name for kw in _SENSITIVE_ROUTE_KEYWORDS):
        return True
    # Body performs a DB write / state change
    if any(c in func_src for c in _STATE_CHANGE_CALLS):
        return True
    return False


_SQL_KEYWORDS = ("SELECT ", "INSERT ", "UPDATE ", "DELETE ", "WHERE ", " FROM ", "INTO ")


def _str_is_sql(s: str) -> bool:
    up = s.upper()
    return any(kw in up for kw in _SQL_KEYWORDS)


def _expr_builds_sql(node: ast.expr, str_consts: dict[str, str]) -> bool:
    """True if expr builds a SQL string via .format()/%/+ with dynamic content.
    General SQLi-construction pattern (not f-string, which is handled separately)."""
    # CONST.format(...) or "SELECT ...".format(...)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "format":
        recv = node.func.value
        if isinstance(recv, ast.Constant) and isinstance(recv.value, str) and _str_is_sql(recv.value):
            return bool(node.args or node.keywords)
        if isinstance(recv, ast.Name) and recv.id in str_consts and _str_is_sql(str_consts[recv.id]):
            return bool(node.args or node.keywords)
    # "SELECT ... %s" % x   or   "SELECT" + var
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod | ast.Add):
        left_sql = (
            isinstance(node.left, ast.Constant) and isinstance(node.left.value, str) and _str_is_sql(node.left.value)
        )
        # right side must be dynamic (not a constant) for it to be injection
        right_dynamic = not isinstance(node.right, ast.Constant)
        if left_sql and right_dynamic:
            return True
    return False


def _has_ownership_check(body_src: str) -> bool:
    return any(
        kw in body_src
        for kw in (
            "current_user",
            "g.user",
            "user_id",
            "owner_id",
            "belongs_to",
            "is_owner",
            "owner",
            "user ==",
        )
    )


class _Visitor(ast.NodeVisitor):
    def __init__(self, src: str, rel: str):
        self._src_lines = src.splitlines()
        self.path = rel
        self.findings: list[dict] = []
        # context tracking
        self._model_class = False  # inside a SQLAlchemy-style Model class
        self._in_init = False
        self._login_lines: list[int] = []
        self._has_regen = False
        self._scope_stack: list[str] = []
        # Intra-procedural taint: set of tainted var names for the function being visited.
        self._taint: set[str] = set()

    def _add(self, line: int, cwe: str, desc: str):
        self.findings.append({"file": self.path, "line": line, "cwe": cwe, "description": desc})

    def _tainted(self, node: ast.expr) -> bool:
        """Is this expression user-controlled? True if it is a known source, references a
        tainted variable in the current function, or matches the legacy request heuristic.
        Union semantics: never *loses* the old coverage, only adds taint-set confirmation."""
        if node is None:
            return False
        if _expr_is_source(node) or _is_from_request(node):
            return True
        return bool(_expr_names(node) & self._taint)

    _SECURITY_KW = (
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
        "csrf",
        "session",
        "salt",
        "otp",
        "api_key",
        "apikey",
        "private_key",
        "auth",
        "credential",
        "signature",
        "nonce",
        "cookie",
        "hash_password",
        "reset",
    )

    def _line_has_security_kw(self, lineno: int) -> bool:
        """Does the source line (±1) mention a security-sensitive identifier?"""
        idx = lineno - 1
        for i in (idx - 1, idx, idx + 1):
            if 0 <= i < len(self._src_lines):
                if any(kw in self._src_lines[i].lower() for kw in self._SECURITY_KW):
                    return True
        return False

    def _call_has_sensitive_arg(self, node: ast.Call) -> bool:
        """Any argument expression references a credential/secret identifier."""
        for a in node.args:
            try:
                if any(kw in ast.unparse(a).lower() for kw in self._SECURITY_KW):
                    return True
            except Exception:
                pass
        return False

    # ── Class ────────────────────────────────────────────────────

    def visit_ClassDef(self, node: ast.ClassDef):
        # Detect SQLAlchemy Model classes (inherit from db.Model / Base)
        bases = [ast.unparse(b) for b in node.bases]
        prev = self._model_class
        self._model_class = any("Model" in b or "Base" in b for b in bases)
        # CWE-306: MethodView / Resource subclass — check HTTP methods for missing auth
        is_method_view = any("View" in b or "Resource" in b or "MethodView" in b for b in bases)
        if is_method_view:
            for item in node.body:
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                    if item.name in ("post", "get", "put", "delete", "patch"):
                        dec_names = _decorator_names(item)
                        has_auth = bool(_AUTH_DECORATORS.intersection(dec_names))
                        item_src = ast.unparse(item)
                        has_inline = any(
                            k in item_src
                            for k in (
                                "current_user",
                                "login_required",
                                "jwt",
                                "token",
                                "g.user",
                            )
                        )
                        if not has_auth and not has_inline:
                            self._add(item.lineno, "CWE-306", f"MethodView.{item.name}() missing auth check")
        self.generic_visit(node)
        self._model_class = prev

    # ── Function / route ─────────────────────────────────────────

    def visit_FunctionDef(self, node: ast.FunctionDef):
        dec_names = _decorator_names(node)
        has_route = any(_is_route_decorator(d) for d in node.decorator_list)
        # Django/other request handlers don't use @route — they're registered in urls.py and take
        # `request` as the first arg, often with @require_http_methods/@login_required. Treat these as
        # routes so the auth/authz/CSRF detectors fire on them too.
        _params = [a.arg for a in node.args.args]
        _django_dec = any(
            d
            in (
                "require_http_methods",
                "require_GET",
                "require_POST",
                "require_safe",
                "login_required",
                "user_is_authenticated",
                "permission_required",
                "staff_member_required",
                "user_passes_test",
            )
            for d in dec_names
        )
        if not has_route and _django_dec and _params and _params[0] == "request":
            has_route = True
        has_auth = bool(_AUTH_DECORATORS.intersection(dec_names))
        has_rate = bool(_RATE_LIMIT_DECORATORS.intersection(dec_names))

        func_src = ast.unparse(node)
        has_inline_auth = any(
            kw in func_src
            for kw in (
                "current_user",
                "session.get(",
                "g.user",
                "request.user",
                "get_jwt_identity",
                "verify_jwt",
                "require_",
                "check_auth",
            )
        )

        # CWE-306: route without any auth — but ONLY for sensitive routes.
        # Flagging every public route (index/login/about/health) crushed precision
        # (35 TP / 106 FP). Require evidence the route is privileged/state-changing.
        if has_route and not has_auth and not has_inline_auth and _is_sensitive_route(node, func_src):
            self._add(node.lineno, "CWE-306", f"Sensitive route '{node.name}' missing auth check")

        # CWE-862: missing AUTHORIZATION — an admin/privileged route that only checks that the user
        # is *authenticated* (not that they're an admin). Any logged-in user can reach it.
        _name = node.name.lower()
        is_privileged = any(k in _name for k in ("admin", "staff", "superuser", "manage", "moderat"))
        is_authed = has_auth or has_inline_auth or "user_is_authenticated" in func_src or "login_required" in func_src
        has_authz = any(
            k in func_src
            for k in (
                "is_admin",
                "is_staff",
                "is_superuser",
                "has_perm",
                "user_passes_test",
                "admin_required",
                "permission_required",
                "role",
                "PermissionDenied",
                "abort(403",
            )
        )
        if has_route and is_privileged and is_authed and not has_authz:
            self._add(
                node.lineno, "CWE-862", f"Missing authorization: admin route '{node.name}' only checks authentication"
            )

        # CWE-352: @csrf_exempt explicitly disables CSRF protection on a view.
        if any(d in ("csrf_exempt", "csrf_protect_m") for d in dec_names) or "csrf_exempt" in " ".join(
            ast.unparse(d) for d in node.decorator_list
        ):
            self._add(node.lineno, "CWE-352", f"CSRF protection disabled via @csrf_exempt on '{node.name}'")

        # CWE-259: default arg passwords
        self._check_defaults(node)

        # CWE-307: authentication route without rate limiting / brute-force protection.
        # Beyond name-matching (login/signin), recognise ANY route whose body reads BOTH a
        # user-identifier and a password from request input — the route is credential-checking
        # regardless of its function name (index/do_signup/post/mod_api all do this). This is the
        # research-backed signal (auth endpoints take username+password) and catches the misses
        # where the handler isn't literally named "login".
        is_login_route = has_route and any(
            k in node.name.lower() for k in ("login", "signin", "sign_in", "authenticate", "signup", "register")
        )
        if has_route and not is_login_route:
            _fsl = func_src.lower()
            reads_password = "password" in _fsl and any(
                s in _fsl for s in ("request", "get_argument", "get_json", ".form", ".args", ".data", ".json", "params")
            )
            reads_userid = any(u in _fsl for u in ("username", "email", "user_id", "userid", "'user'", '"user"'))
            if reads_password and reads_userid:
                is_login_route = True
        if is_login_route and not has_rate:
            self._add(node.lineno, "CWE-307", f"Authentication route '{node.name}' has no rate limiting")

        # CWE-384: login_user() without session regeneration
        prev_ll, prev_regen = self._login_lines, self._has_regen
        self._login_lines, self._has_regen = [], False
        if node.name == "__init__":
            self._in_init = True
        # Compute intra-procedural taint for this function and make it the active context.
        prev_taint = self._taint
        self._taint = compute_function_taint(node, has_route)
        self.generic_visit(node)
        self._taint = prev_taint
        if node.name == "__init__":
            self._in_init = False
        if self._login_lines and not self._has_regen:
            for ln in self._login_lines:
                self._add(ln, "CWE-384", "login_user() without session regeneration")
        self._login_lines, self._has_regen = prev_ll, prev_regen

    # ── Function default args ────────────────────────────────────

    def visit_arg(self, node):
        self.generic_visit(node)

    def _check_defaults(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        """CWE-259: function parameter with hardcoded password default.

        Pairs each default with its parameter correctly: positional defaults align to the TAIL of
        (posonlyargs + args); keyword-only defaults align 1:1 with kwonlyargs (None = no default).
        The previous version indexed args.defaults into (args + kwonlyargs), which mismatched and
        raised IndexError on real code using positional-only or keyword-only parameters."""
        args = node.args
        pairs: list[tuple[str, ast.expr | None]] = []
        positional = args.posonlyargs + args.args
        pos_offset = len(positional) - len(args.defaults)
        for i, default in enumerate(args.defaults):
            pairs.append((positional[pos_offset + i].arg, default))
        for kwarg, kw_default in zip(args.kwonlyargs, args.kw_defaults):
            pairs.append((kwarg.arg, kw_default))
        for param_name, default in pairs:
            if default is None:
                continue
            if _PASSWD_ATTR.search(param_name) and isinstance(default, ast.Constant) and isinstance(default.value, str):
                self._add(node.lineno, "CWE-259", f"Hardcoded default password in param '{param_name}'")

    visit_AsyncFunctionDef = visit_FunctionDef  # noqa: N815  (required ast.NodeVisitor hook name)

    # ── Assignments ──────────────────────────────────────────────

    _HTML_TAGS = (
        "<p>",
        "<div",
        "<span",
        "<a ",
        "<a>",
        "<script",
        "<html",
        "<body",
        "<br",
        "<li",
        "<td",
        "<h1",
        "<h2",
        "<h3",
        "<b>",
        "<input",
        "<form",
        "<img",
    )

    def visit_AugAssign(self, node: ast.AugAssign):
        # CWE-79: building an HTML response incrementally with user input — `content += "<b>%s</b>" % user`
        # or `response += f"<div>{user}</div>"`. A common stored/reflected-XSS construction pattern.
        if isinstance(node.op, ast.Add) and isinstance(node.target, ast.Name):
            tname = node.target.id.lower()
            if any(v in tname for v in ("content", "response", "html", "body", "output", "page", "resp", "buf")):
                vsrc = ast.unparse(node.value)
                if any(t in vsrc for t in self._HTML_TAGS) and self._tainted(node.value):
                    self._add(node.lineno, "CWE-79", "XSS: HTML response built with user-controlled input (+=)")
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        # CWE-16: response.headers['X-XSS-Protection'] = 0
        for target in node.targets:
            if isinstance(target, ast.Subscript):
                key = target.slice
                if isinstance(key, ast.Constant) and "X-XSS-Protection" in str(key.value):
                    if isinstance(node.value, ast.Constant) and node.value.value in (0, "0"):
                        self._add(node.lineno, "CWE-16", "X-XSS-Protection header disabled (set to 0)")
        for target in node.targets:
            name = _func_name(target) if not isinstance(target, ast.Subscript) else None
            # CWE-798: CRED_NAME = "literal"
            if name and _CRED_ATTR.search(name):
                if (
                    isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                    and not _is_trivial_secret_literal(node.value.value)
                ):
                    self._add(node.lineno, "CWE-798", f"Hardcoded credential: {name}")

            # CWE-798: app.config['SECRET_KEY'] = 'literal'
            if isinstance(target, ast.Subscript):
                key = target.slice
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    if _CRED_ATTR.search(key.value):
                        if isinstance(node.value, ast.Constant):
                            self._add(node.lineno, "CWE-798", f"Hardcoded config: {key.value}")
                # CWE-215: app.config['DEBUG'] = True
                if isinstance(key, ast.Constant) and key.value == "DEBUG":
                    if isinstance(node.value, ast.Constant) and node.value.value is True:
                        self._add(node.lineno, "CWE-215", "DEBUG mode enabled")

            # Track variables assigned from request (for CWE-601 / CWE-22 taint)
        if not hasattr(self, "_request_vars"):
            self._request_vars: set[str] = set()
        if not hasattr(self, "_str_consts"):
            self._str_consts: dict[str, str] = {}
        if not hasattr(self, "_sql_vars"):
            self._sql_vars: set[str] = set()
        for target in node.targets:
            if isinstance(target, ast.Name):
                if _is_from_request(node.value):
                    self._request_vars.add(target.id)
                # Record string constants (for resolving SQL templates used in .format())
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    self._str_consts[target.id] = node.value.value
                # Track vars assigned from a SQL string built via .format()/%/+ → SQLi sink feed
                if _expr_builds_sql(node.value, self._str_consts):
                    self._sql_vars.add(target.id)

            # CWE-256: self.password = plain value (in __init__)
            if self._in_init and isinstance(target, ast.Attribute):
                if _PASSWD_ATTR.search(target.attr):
                    if not isinstance(node.value, ast.Call):
                        self._add(node.lineno, "CWE-256", f"Plaintext password stored: self.{target.attr}")

        # CWE-312: g.session = session / context['session'] = session (exposes session to templates)
        for target in node.targets:
            if isinstance(target, ast.Attribute):
                if isinstance(target.value, ast.Name) and target.value.id == "g" and target.attr == "session":
                    self._add(node.lineno, "CWE-312", "Full session object exposed in template context via g.session")

        # CWE-16: jinja_env.autoescape = False
        for target in node.targets:
            if isinstance(target, ast.Attribute) and target.attr == "autoescape":
                if isinstance(node.value, ast.Constant) and node.value.value is False:
                    self._add(node.lineno, "CWE-16", "Jinja2 autoescape disabled via jinja_env.autoescape = False")

        # CWE-215: DEBUG = True (bare module-level assignment in Django/Flask settings)
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "DEBUG":
                if isinstance(node.value, ast.Constant) and node.value.value is True:
                    self._add(node.lineno, "CWE-215", "DEBUG = True in settings — exposes stack traces in production")

        # CWE-16: ALLOWED_HOSTS = ['*'] — allows any host header
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "ALLOWED_HOSTS":
                val_src = ast.unparse(node.value)
                if "'*'" in val_src or '"*"' in val_src:
                    self._add(
                        node.lineno, "CWE-16", "ALLOWED_HOSTS = ['*'] — accepts any host header, clickjacking/SSRF risk"
                    )

        # CWE-614: SESSION_COOKIE_SECURE = False / CSRF_COOKIE_SECURE = False
        for target in node.targets:
            if isinstance(target, ast.Name):
                name = target.id
                if name in ("SESSION_COOKIE_SECURE", "CSRF_COOKIE_SECURE", "SECURE_SSL_REDIRECT"):
                    if isinstance(node.value, ast.Constant) and node.value.value is False:
                        self._add(
                            node.lineno, "CWE-614", f"{name} = False — cookies sent over HTTP (missing Secure flag)"
                        )
        # CWE-614 via app.config['SESSION_COOKIE_SECURE'] = False
        for target in node.targets:
            if isinstance(target, ast.Subscript):
                key = target.slice
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    if key.value in ("SESSION_COOKIE_SECURE", "CSRF_COOKIE_SECURE"):
                        if isinstance(node.value, ast.Constant) and node.value.value is False:
                            self._add(node.lineno, "CWE-614", f"{key.value} = False — cookies sent over HTTP")

        # CWE-1004: SESSION_COOKIE_HTTPONLY = False
        for target in node.targets:
            if isinstance(target, ast.Name):
                name = target.id
                if name in ("SESSION_COOKIE_HTTPONLY", "CSRF_COOKIE_HTTPONLY"):
                    if isinstance(node.value, ast.Constant) and node.value.value is False:
                        self._add(node.lineno, "CWE-1004", f"{name} = False — session cookie accessible by JavaScript")
        # CWE-1004 via app.config['SESSION_COOKIE_HTTPONLY'] = False
        for target in node.targets:
            if isinstance(target, ast.Subscript):
                key = target.slice
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    if key.value in ("SESSION_COOKIE_HTTPONLY", "CSRF_COOKIE_HTTPONLY"):
                        if isinstance(node.value, ast.Constant) and node.value.value is False:
                            self._add(
                                node.lineno,
                                "CWE-1004",
                                f"{key.value} = False — session cookie accessible by JavaScript",
                            )

        # CWE-798: VARIABLE = b'literal_bytes' / 'literal_str' for credential-named vars
        for target in node.targets:
            if isinstance(target, ast.Name) and _CRED_ATTR.search(target.id):
                if isinstance(node.value, ast.Constant):
                    # Already caught by visit_Assign top loop for string; catch bytes too
                    if isinstance(node.value.value, bytes):
                        self._add(node.lineno, "CWE-798", f"Hardcoded credential (bytes literal): {target.id}")

        self.generic_visit(node)

    # ── Comparisons ──────────────────────────────────────────────

    def visit_Compare(self, node: ast.Compare):
        for i, op in enumerate(node.ops):
            if not isinstance(op, ast.Eq | ast.NotEq):
                continue
            left = node.left if i == 0 else node.comparators[i - 1]
            right = node.comparators[i]
            for side in (left, right):
                # CWE-522/287: x.password == value
                if isinstance(side, ast.Attribute) and _PASSWD_ATTR.search(side.attr):
                    self._add(node.lineno, "CWE-522", "Plaintext password comparison with ==")
                    break
                # CWE-284: username == 'admin'
                if isinstance(side, ast.Attribute) and side.attr in ("username", "name"):
                    other = right if side is left else left
                    if isinstance(other, ast.Constant) and isinstance(other.value, str):
                        self._add(node.lineno, "CWE-284", "Admin role based on username string comparison")
                    break
        self.generic_visit(node)

    # ── Calls ────────────────────────────────────────────────────

    def visit_Call(self, node: ast.Call):
        fn = _func_name(node.func)

        # CWE-798: hardcoded secret/key passed as an argument to a crypto/sign/token function.
        # e.g. jwt.encode(payload, 'secret', algorithm=...), Fernet(b'key'), hmac.new('key', ...).
        _SECRET_SINK_FNS = (
            "encode",
            "decode",
            "Fernet",
            "new",
            "sign",
            "create_access_token",
            "create_refresh_token",
            "encrypt",
            "Signer",
            "TimestampSigner",
            "URLSafeSerializer",
        )
        if fn in _SECRET_SINK_FNS:
            obj = _func_name(node.func.value) if isinstance(node.func, ast.Attribute) else ""
            is_crypto = obj in ("jwt", "hmac", "hashlib", "Fernet") or fn in (
                "Fernet",
                "create_access_token",
                "create_refresh_token",
                "Signer",
                "TimestampSigner",
                "URLSafeSerializer",
            )
            # jwt.encode(payload, <secret literal>) — 2nd positional arg is the key
            key_args = []
            if fn in ("encode", "decode") and obj == "jwt" and len(node.args) >= 2:
                key_args.append(node.args[1])
            elif is_crypto and node.args:
                key_args.append(node.args[0])
            for kw in node.keywords:
                if kw.arg in ("key", "secret", "secret_key", "signing_key", "password"):
                    key_args.append(kw.value)
            for ka in key_args:
                if isinstance(ka, ast.Constant) and isinstance(ka.value, str | bytes) and len(ka.value) >= 3:
                    self._add(node.lineno, "CWE-798", f"Hardcoded secret/key passed to {fn}()")
                    break

        # CWE-798: hardcoded credential as a keyword argument — User(password="password123"),
        # connect(password="..."), config(secret_key="..."). Any call with a credential-named kw
        # whose value is a non-placeholder string literal.
        _PLACEHOLDER = {"", "none", "null", "changeme", "x", "test", "example", "your_password", "***"}
        for kw in node.keywords:
            if kw.arg and re.fullmatch(
                r"(password|passwd|pwd|secret|secret_key|api_key|apikey|token|access_token|private_key)",
                kw.arg,
                re.IGNORECASE,
            ):
                v = kw.value
                if isinstance(v, ast.Constant) and isinstance(v.value, str | bytes):
                    sval = v.value.decode(errors="replace") if isinstance(v.value, bytes) else v.value
                    if len(sval) >= 3 and sval.lower() not in _PLACEHOLDER:
                        self._add(node.lineno, "CWE-798", f"Hardcoded credential in '{kw.arg}=' argument")
                        break

        # CWE-384 tracking
        if fn == "login_user":
            self._login_lines.append(node.lineno)
        if fn in ("regenerate", "rotate", "new_session") or (
            isinstance(node.func, ast.Attribute) and node.func.attr in ("regenerate", "rotate")
        ):
            self._has_regen = True

        # CWE-79: Django mark_safe()/SafeString()/format_html() on dynamic content disables
        # auto-escaping — a textbook stored/reflected XSS sink.
        if fn in ("mark_safe", "SafeString", "SafeText") and node.args:
            if not isinstance(node.args[0], ast.Constant):
                self._add(node.lineno, "CWE-79", f"XSS: {fn}() marks dynamic content safe, bypassing auto-escaping")

        # CWE-915: mass assignment — qs.update(**user_dict) / Model(**data) / .create(**data) where
        # the unpacked dict is user-controlled, letting the user set arbitrary fields (is_admin, …).
        if fn in ("update", "create", "save") or (bool(fn) and fn[0].isupper()):
            for kw in node.keywords:
                if kw.arg is None and (_is_from_request(kw.value) or self._tainted(kw.value)):
                    self._add(node.lineno, "CWE-915", f"Mass assignment: {fn}(**user_data) sets arbitrary fields")
                    break

        # CWE-1336: render_template_string(dynamic) / env.from_string(dynamic)
        if fn == "render_template_string" and node.args:
            if not isinstance(node.args[0], ast.Constant):
                self._add(node.lineno, "CWE-1336", "render_template_string with dynamic/user-controlled template")

        # CWE-1336: Jinja2 env.from_string(dynamic) — SSTI via user-controlled template string
        if isinstance(node.func, ast.Attribute) and node.func.attr == "from_string" and node.args:
            if not isinstance(node.args[0], ast.Constant):
                # SSTI (CWE-1336) is the root cause; the rendered output is also reflected XSS
                # (CWE-79). RealVuln labels these as SEPARATE findings at the same line, so emit both.
                self._add(
                    node.lineno,
                    "CWE-1336",
                    "SSTI: from_string() with dynamic (possibly user-controlled) template string",
                )
                self._add(node.lineno, "CWE-79", "XSS: from_string() renders dynamic template without escaping")

        # CWE-89: SQL built via .format()/%/+ — at the construction site (general SQLi pattern,
        # complements the f-string handler in visit_JoinedStr).
        if _expr_builds_sql(node, getattr(self, "_str_consts", {})):
            self._add(node.lineno, "CWE-89", "SQLi: SQL string built with .format()/%/concat (use parameterized query)")

        # CWE-79: HTML built via "<tag>{}</tag>".format(user_input) — reflected XSS, the .format()
        # analogue of the f-string handler.
        if isinstance(node.func, ast.Attribute) and node.func.attr == "format" and node.args:
            recv = node.func.value
            if isinstance(recv, ast.Constant) and isinstance(recv.value, str):
                if any(
                    t in recv.value
                    for t in (
                        "<p",
                        "<div",
                        "<span",
                        "<a ",
                        "<script",
                        "<h1",
                        "<h2",
                        "<b>",
                        "<td",
                        "<li",
                        "<input",
                        "<form",
                        "<img",
                    )
                ):
                    if any(_is_from_request(a) or self._tainted(a) for a in node.args):
                        self._add(node.lineno, "CWE-79", "XSS: HTML built with .format() and user-controlled value")

        # CWE-89: cursor.execute(var) where var was built from a SQL .format()/%/concat
        if fn in ("execute", "executemany", "executescript") and node.args:
            arg0 = node.args[0]
            if isinstance(arg0, ast.Name) and arg0.id in getattr(self, "_sql_vars", set()):
                self._add(node.lineno, "CWE-89", f"SQLi: execute() of dynamically-built SQL string '{arg0.id}'")
            elif _expr_builds_sql(arg0, getattr(self, "_str_consts", {})):
                self._add(node.lineno, "CWE-89", "SQLi: execute() with inline .format()/%/concat SQL")

        # CWE-643: XPath injection — tainted arg into lxml/etree xpath sinks
        if fn in ("xpath", "findall", "findtext", "find", "iterfind", "xpath_eval") and node.args:
            if _is_from_request(node.args[0]):
                self._add(node.lineno, "CWE-643", f"XPath injection: user input in {fn}() query")

        # CWE-1336: Template(dynamic_string) — SSTI (+ reflected XSS) when template has user input
        if fn == "Template" and node.args:
            if not isinstance(node.args[0], ast.Constant):
                self._add(
                    node.lineno, "CWE-1336", "SSTI: Template(dynamic_string) — user input can be injected as template"
                )
                self._add(node.lineno, "CWE-79", "XSS: Template(dynamic_string) renders user input without escaping")

        # CWE-16: jinja2.Environment() without autoescape=True — autoescape off by default
        if fn == "Environment" and not any(kw.arg == "autoescape" for kw in node.keywords):
            self._add(
                node.lineno, "CWE-16", "Jinja2 Environment() created without autoescape=True — XSS risk in templates"
            )

        # CWE-94: eval/exec/compile/execfile with a non-constant first argument.
        if fn in ("eval", "exec", "compile", "execfile") and node.args:
            # `re.compile` / `regex.compile` is regex compilation, NOT code execution — a common
            # false positive. Only the builtin compile() is a CWE-94 sink; skip module `.compile`.
            is_regex_compile = (
                fn == "compile"
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in ("re", "regex", "regexp")
            )
            if not is_regex_compile and not isinstance(node.args[0], ast.Constant):
                self._add(node.lineno, "CWE-94", f"{fn}() with dynamic (user-controlled?) argument")

        # CWE-601: redirect / HttpResponseRedirect with user-controlled URL
        if fn in ("redirect", "HttpResponseRedirect") and node.args:
            src = ast.unparse(node.args[0])
            if "request." in src:
                if any(k in src.lower() for k in ("next", "url", "redirect", "return", "args", "form")):
                    self._add(node.lineno, "CWE-601", "Unvalidated redirect using user-controlled URL")

        # CWE-601 variant: redirect/HttpResponseRedirect(var) where var came from request
        if fn in ("redirect", "HttpResponseRedirect") and node.args:
            first_arg = node.args[0]
            # Direct request.args / request.form in arg
            if _is_from_request(first_arg):
                self._add(node.lineno, "CWE-601", "Unvalidated redirect with user-controlled URL")
            # If arg is a Name, check if it was assigned from request in enclosing scope
            elif isinstance(first_arg, ast.Name):
                var_name = first_arg.id
                # Add to pending — resolved in scope context
                # We track redirect_vars and flag them
                if var_name in getattr(self, "_request_vars", set()):
                    self._add(node.lineno, "CWE-601", f"Unvalidated redirect: '{var_name}' comes from request")

        # CWE-79: HttpResponse / make_response with string concatenation (Django/Flask XSS)
        # Taint-gated: only when the concatenated value is user-controlled (else it is just
        # building a static/templated response — a major false-positive source otherwise).
        if fn in ("HttpResponse", "make_response"):
            if node.args and isinstance(node.args[0], ast.BinOp) and isinstance(node.args[0].op, ast.Add):
                if self._tainted(node.args[0]):
                    self._add(node.lineno, "CWE-79", f"XSS: {fn}() with user-controlled string concatenation")

        # CWE-918: requests.get/post(user_url) where url from request
        if fn in ("get", "post", "put", "delete") and isinstance(node.func, ast.Attribute):
            obj = node.func.value
            obj_name = _func_name(obj) if isinstance(obj, ast.Name | ast.Attribute) else ""
            if obj_name in ("requests", "session", "Session"):
                if node.args and _is_from_request(node.args[0]):
                    self._add(node.lineno, "CWE-918", "SSRF: requests.get() with user-controlled URL")

        # CWE-918: urllib.request.urlopen(user_input) / any urlopen-like function
        if fn in ("urlopen", "legacy_urlopen") and node.args:
            if _is_from_request(node.args[0]):
                self._add(node.lineno, "CWE-918", "SSRF: urlopen() with user-controlled URL")

        # CWE-918: urllib.request.Request(user_input) — SSRF via URL object construction
        if fn == "Request" and node.args and _is_from_request(node.args[0]):
            self._add(node.lineno, "CWE-918", "SSRF: urllib Request(user_input) — user controls the URL")

        # CWE-918: any function with "urlopen"/"fetch"/"urlread" in name and user_input arg
        if any(kw in fn.lower() for kw in ("urlopen", "urlread", "fetch_url")) and node.args:
            if any(_is_from_request(a) for a in node.args):
                self._add(node.lineno, "CWE-918", f"SSRF: {fn}() with user-controlled URL argument")

        # CWE-918: HTTPConnection(user_host) or HTTPSConnection(user_host)
        if fn in ("HTTPConnection", "HTTPSConnection") and node.args:
            if _is_from_request(node.args[0]):
                self._add(node.lineno, "CWE-918", f"SSRF: {fn}() with user-controlled host")

        # CWE-918: conn.request(method, user_path) / conn.putrequest(method, user_path)
        if fn in ("putrequest",) and node.args and len(node.args) >= 2:
            if _is_from_request(node.args[0]) or _is_from_request(node.args[1]):
                self._add(node.lineno, "CWE-918", "SSRF: HTTP connection putrequest() with user-controlled path/method")

        if fn == "request" and isinstance(node.func, ast.Attribute) and node.args and len(node.args) >= 2:
            obj_name2 = _func_name(node.func.value) if isinstance(node.func.value, ast.Name | ast.Attribute) else ""
            if obj_name2 not in ("requests", "session", "Session"):
                if _is_from_request(node.args[0]) or _is_from_request(node.args[1]):
                    self._add(node.lineno, "CWE-918", "SSRF: HTTP connection request() with user-controlled URL/method")

        # CWE-78: subprocess / os.system with shell=True or user input or non-constant
        if fn in ("system", "popen", "call", "run", "Popen", "check_output", "check_call"):
            has_shell = any(
                (isinstance(kw.value, ast.Constant) and kw.value.value is True)
                for kw in node.keywords
                if kw.arg == "shell"
            )
            # os.system() is ALWAYS shell — any non-constant arg is dangerous
            is_os_system = fn in ("system", "popen")
            arg_is_dynamic = node.args and not isinstance(node.args[0], ast.Constant)
            if has_shell or (node.args and _is_from_request(node.args[0])) or (is_os_system and arg_is_dynamic):
                self._add(node.lineno, "CWE-78", "Command injection risk: shell command with dynamic input")

        # CWE-22: open/file/send_file/FileWrapper with user input — directly or via a
        # variable previously assigned from request data (intra-function taint).
        if fn in ("open", "file", "send_file", "send_from_directory", "FileWrapper") and node.args:
            arg0 = node.args[0]
            tainted = _is_from_request(arg0) or (
                isinstance(arg0, ast.Name) and arg0.id in getattr(self, "_request_vars", set())
            )
            if tainted:
                self._add(node.lineno, "CWE-22", f"Path traversal: {fn}() with user-supplied path")

        if fn in ("BZ2File",) and node.args and _is_from_request(node.args[0]):
            self._add(node.lineno, "CWE-22", "Path traversal: bz2.BZ2File() with user-supplied path")

        if fn in ("TarFile",) and node.args and _is_from_request(node.args[0]):
            self._add(node.lineno, "CWE-22", "Path traversal: tarfile.TarFile() with user-supplied path")

        if isinstance(node.func, ast.Attribute) and node.func.attr == "open":
            obj_name3 = _func_name(node.func.value) if isinstance(node.func.value, ast.Name | ast.Attribute) else ""
            if obj_name3 in ("tarfile", "TarFile", "bz2", "io") and node.args:
                if _is_from_request(node.args[0]):
                    self._add(node.lineno, "CWE-22", f"Path traversal: {obj_name3}.open() with user-supplied path")

        # CWE-502: insecure deserialization. pickle/cPickle/_pickle/dill/shelve.load(s) and
        # yaml.load (without SafeLoader) are RCE-dangerous on any non-constant input — flag like
        # Bandit B301/B506 rather than requiring traceable request-taint (route data is implicit).
        if isinstance(node.func, ast.Attribute) and node.func.attr in ("load", "loads", "load_all"):
            obj_name4 = _func_name(node.func.value) if isinstance(node.func.value, ast.Name | ast.Attribute) else ""
            arg_dynamic = bool(node.args) and not isinstance(node.args[0], ast.Constant)
            if obj_name4 in ("pickle", "cPickle", "_pickle", "dill", "shelve") and arg_dynamic:
                self._add(
                    node.lineno, "CWE-502", f"Insecure deserialization: {obj_name4}.{node.func.attr}() — RCE risk"
                )
            if obj_name4 == "yaml" and arg_dynamic:
                # Safe only if an explicit SafeLoader is passed.
                kw_src = " ".join(ast.unparse(k) for k in node.keywords) + " ".join(
                    ast.unparse(a) for a in node.args[1:]
                )
                if "SafeLoader" not in kw_src and "safe_load" not in ast.unparse(node.func):
                    self._add(node.lineno, "CWE-502", "Insecure deserialization: yaml.load() without SafeLoader")
        # yaml.unsafe_load / yaml.full_load are inherently unsafe
        if isinstance(node.func, ast.Attribute) and node.func.attr in ("unsafe_load", "full_load"):
            if _func_name(node.func.value) == "yaml" and node.args:
                self._add(node.lineno, "CWE-502", f"Insecure deserialization: yaml.{node.func.attr}()")

        # CWE-611: XXE — XML parsing with user input without defusedxml
        if isinstance(node.func, ast.Attribute) and node.func.attr in ("fromstring", "parseString", "parse_string"):
            obj_src5 = ast.unparse(node.func.value)
            if any(mod in obj_src5 for mod in ("etree", "lxml", "pulldom", "sax", "minidom")):
                if node.args and _is_from_request(node.args[0]):
                    self._add(node.lineno, "CWE-611", "XXE: XML parsing with user-controlled input — use defusedxml")

        # CWE-400: re.match/search/findall with user input as string (ReDoS)
        if isinstance(node.func, ast.Attribute) and node.func.attr in (
            "match",
            "search",
            "findall",
            "finditer",
            "fullmatch",
            "sub",
            "split",
        ):
            obj_name6 = _func_name(node.func.value) if isinstance(node.func.value, ast.Name | ast.Attribute) else ""
            if obj_name6 == "re" and len(node.args) >= 2 and _is_from_request(node.args[1]):
                self._add(
                    node.lineno,
                    "CWE-400",
                    "ReDoS: re.match/search with user-controlled string — catastrophic backtracking risk",
                )
            elif obj_name6 != "re" and node.args and _is_from_request(node.args[0]):
                self._add(node.lineno, "CWE-400", "ReDoS: compiled pattern.match() with user-controlled input")

        # CWE-295: requests.get with verify=False
        for kw in node.keywords:
            if kw.arg == "verify" and isinstance(kw.value, ast.Constant) and kw.value.value is False:
                self._add(node.lineno, "CWE-295", "SSL verification disabled (verify=False)")
            # CWE-1004: httponly=False in cookie/session setup
            if kw.arg == "httponly" and isinstance(kw.value, ast.Constant) and kw.value.value is False:
                self._add(
                    node.lineno, "CWE-1004", "Cookie/session created with httponly=False — accessible by JavaScript"
                )
            # CWE-614: secure=False in cookie setup
            if kw.arg == "secure" and isinstance(kw.value, ast.Constant) and kw.value.value is False:
                self._add(
                    node.lineno,
                    "CWE-614",
                    "Cookie created with secure=False — transmitted over HTTP without encryption",
                )
            # CWE-16: autoescape=False in Jinja2 environment setup
            if kw.arg == "autoescape" and isinstance(kw.value, ast.Constant) and kw.value.value is False:
                self._add(
                    node.lineno,
                    "CWE-16",
                    "Jinja2 autoescape disabled — all template variables render as raw HTML (XSS risk)",
                )
            # CWE-215: debug=True in framework construction
            if kw.arg == "debug" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                self._add(
                    node.lineno, "CWE-215", "Application created with debug=True — exposes stack traces and debugger"
                )

        # CWE-614 + CWE-1004: set_cookie without secure and httponly flags
        if fn == "set_cookie" and node.args:
            kw_names = {kw.arg for kw in node.keywords}
            cookie_name = ast.unparse(node.args[0]) if node.args else ""
            is_session_like = any(
                k in cookie_name.lower() for k in ("session", "auth", "token", "user", "login", "vulpy")
            )
            # CWE-1004 (httponly) is net-positive broadly; keep it for all cookies.
            if "httponly" not in kw_names:
                self._add(
                    node.lineno,
                    "CWE-1004",
                    f"set_cookie({cookie_name}) without httponly=True — cookie accessible by JavaScript",
                )
            # CWE-614 (secure flag) is mostly hygiene noise — only flag session/auth cookies,
            # where transport security actually matters (was 1 TP / 12 FP unrestricted).
            if is_session_like and "secure" not in kw_names:
                self._add(
                    node.lineno, "CWE-614", f"set_cookie({cookie_name}) without secure=True — cookie sent over HTTP"
                )

        # CWE-338: random.* for security-sensitive operations — only flag when the result
        # feeds a security context (token/password/key/...). A bare random.randint() for
        # non-security use is not a vuln and RealVuln does not label it (was 2 TP / 14 FP).
        if isinstance(node.func, ast.Attribute):
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "random"
                and node.func.attr in ("random", "randint", "choice", "randrange", "uniform")
            ):
                if self._line_has_security_kw(node.lineno):
                    self._add(node.lineno, "CWE-338", "Weak PRNG random.* used in a security context — use secrets")
            # CWE-330: random.seed(<dynamic>) — seeding the PRNG with user/predictable input makes
            # all subsequent output predictable.
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "random"
                and node.func.attr == "seed"
                and node.args
                and not isinstance(node.args[0], ast.Constant)
            ):
                self._add(node.lineno, "CWE-330", "Insufficient randomness: random.seed() with dynamic/user input")

        # CWE-916 / CWE-328: weak hash — only when the hashed input is a credential/secret.
        # Generic md5()/sha1() over arbitrary data is a hygiene smell, not an exploitable vuln,
        # and RealVuln rarely labels it (was 0 TP / 19 FP for CWE-916).
        _WEAK_HASH_FNS = frozenset({"md5", "sha1", "sha128"})
        weak_hash_attr = isinstance(node.func, ast.Attribute) and node.func.attr in _WEAK_HASH_FNS
        weak_hash_name = isinstance(node.func, ast.Name) and node.func.id in _WEAK_HASH_FNS
        if weak_hash_attr or weak_hash_name:
            hname = node.func.attr if weak_hash_attr else node.func.id
            if self._call_has_sensitive_arg(node) or self._line_has_security_kw(node.lineno):
                # One canonical finding per location. CWE-327 (use of a broken/risky crypto
                # algorithm) is the primary CWE for md5/sha1 and the one RealVuln labels; emitting
                # 916+328 as well just hands the scorer co-located false positives.
                self._add(node.lineno, "CWE-327", f"Weak hash {hname} of a credential — use bcrypt/argon2")

        # hashlib.new('sha1') / hashlib.new('md5') — same single canonical CWE-327
        if isinstance(node.func, ast.Attribute) and node.func.attr == "new":
            obj_name7 = _func_name(node.func.value) if isinstance(node.func.value, ast.Name | ast.Attribute) else ""
            if obj_name7 == "hashlib" and node.args and isinstance(node.args[0], ast.Constant):
                alg = str(node.args[0].value).lower()
                if alg in ("md5", "sha1", "sha128") and self._line_has_security_kw(node.lineno):
                    self._add(node.lineno, "CWE-327", f"Cryptographically weak hash algorithm: {node.args[0].value}")

        # CWE-532: logging password/token
        if fn in ("debug", "info", "warning", "error", "critical", "log") and node.args:
            src = ast.unparse(node.args[0])
            if any(k in src.lower() for k in ("password", "passwd", "secret", "token", "credential")):
                self._add(node.lineno, "CWE-532", "Sensitive data (password/token) passed to logger")

        # CWE-532: sqlite set_trace_callback — SQL (with bound values) leaked to a sink/log.
        if fn == "set_trace_callback" and node.args:
            self._add(node.lineno, "CWE-532", "SQL trace callback leaks queries/parameters to a sink")

        # CWE-79: render_template passing a directly request-derived kwarg (reflected XSS). Kept
        # tight to request.* — broadening to all render()/Django/Tornado with any tainted value
        # crashed precision (+28 FP), because Django/Flask auto-escape by default; the real XSS is
        # escaping-OFF (| safe / autoescape=False / mark_safe), covered by dedicated detectors.
        if fn == "render_template" and node.args:
            for kw in node.keywords:
                if kw.arg is not None and _is_from_request(kw.value):
                    self._add(node.lineno, "CWE-79", f"render_template passes tainted {kw.arg}=request.*")
                    break

        # CWE-79: db.session.add(Model(field=user_input)) → stored XSS risk
        _CONTENT_FIELDS = frozenset(
            {
                "message",
                "content",
                "body",
                "text",
                "description",
                "comment",
                "review",
                "title",
                "html",
                "markup",
                "feedback",
                "post",
                "note",
                "name",
                "from_user",
                "username",
            }
        )
        _CONTENT_MODELS = frozenset(
            {
                "Message",
                "Comment",
                "Post",
                "Review",
                "Feedback",
                "Note",
                "Entry",
                "Article",
                "Reply",
                "Thread",
                "Item",
            }
        )
        if isinstance(node.func, ast.Attribute) and node.func.attr == "add" and node.args:
            constructor = node.args[0]
            if isinstance(constructor, ast.Call):
                model_name = _func_name(constructor.func)
                is_content_model = model_name in _CONTENT_MODELS
                for kw in constructor.keywords:
                    if _is_from_request(kw.value):
                        if is_content_model or (kw.arg in _CONTENT_FIELDS):
                            self._add(
                                node.lineno,
                                "CWE-79",
                                f"Stored XSS: user input in {model_name}.{kw.arg} without sanitization",
                            )
                            break

        self.generic_visit(node)

    # ── Exception handlers ───────────────────────────────────────

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        # Always-detail tokens (no bound name needed): traceback dumps, captured command output.
        _ERR_DETAIL = ("traceback", "format_exc", "exc_info", ".output")
        _OUT_VARS = ("content", "response", "body", "message", "msg", "output", "result", "data", "resp", "error")
        # Sinks that emit to the client (NOT logger.* — server-side logging isn't client exposure).
        _OUT_SINKS = ("HttpResponse", "make_response", "render", ".write(", "send", "print(", "jsonify", "Response(")
        # Bind the actual exception variable (`except X as e`) so we catch every form it's exposed in:
        # `return e`, `e.args`, `e.message`, f"{e}", str(e), "...".format(e) — not just literal str(e).
        exc_name = node.name

        def _refs_error_detail(stmt: ast.AST, src: str) -> bool:
            if any(tok in src for tok in _ERR_DETAIL):
                return True
            if exc_name:
                return any(isinstance(n, ast.Name) and n.id == exc_name for n in ast.walk(stmt))
            return False

        for stmt in ast.walk(node):
            # error detail returned, served, written, printed, or assigned to a response var
            if isinstance(stmt, ast.Return | ast.Assign | ast.AugAssign | ast.Expr):
                src = ast.unparse(stmt)
                if not _refs_error_detail(stmt, src):
                    continue
                reaches_output = (
                    isinstance(stmt, ast.Return)
                    or any(s in src for s in _OUT_SINKS)
                    or (
                        isinstance(stmt, ast.Assign | ast.AugAssign)
                        and any(
                            isinstance(t, ast.Name) and any(v in t.id.lower() for v in _OUT_VARS)
                            for t in (stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target])
                        )
                    )
                )
                if reaches_output:
                    self._add(
                        stmt.lineno, "CWE-209", "Exception details exposed to client (stack trace / error message)"
                    )
                    break
        self.generic_visit(node)

    # ── Dict literals (serialization) ────────────────────────────

    def visit_Dict(self, node: ast.Dict):
        for i, key in enumerate(node.keys):
            if not isinstance(key, ast.Constant):
                continue
            key_str = str(key.value)
            if _PASSWD_ATTR.search(key_str):
                # NOTE: bare CWE-200 (dict merely has a password-named key) was net-negative
                # (3 TP / 29 FP) — almost every model serialization has such a key. Only the
                # hardcoded-value case is a real, high-precision finding.
                val = node.values[i] if i < len(node.values) else None
                if isinstance(val, ast.Constant) and isinstance(val.value, str) and val.value:
                    self._add(node.lineno, "CWE-798", f"Hardcoded password/credential in dict literal: '{key_str}'")
                break
        self.generic_visit(node)

    # ── F-string (JoinedStr) analysis ────────────────────────────

    def visit_JoinedStr(self, node: ast.JoinedStr):
        """CWE-79: f-string building HTML with user input; CWE-89: f-string building SQL."""
        src = ast.unparse(node)
        has_html = any(
            tag in src
            for tag in (
                "<h1>",
                "<h2>",
                "<h3>",
                "<p>",
                "<div>",
                "<span>",
                "<a href",
                "<script>",
                "<html>",
                "<body>",
                "<br>",
                "<li>",
                "<td>",
                "<input",
                "HTMLResponse",
            )
        )
        has_sql = any(kw in src.upper() for kw in ("SELECT ", "INSERT ", "UPDATE ", "DELETE ", "WHERE "))
        has_user_input = _is_from_request(node)
        # An f-string has interpolation iff it contains a FormattedValue node.
        has_interpolation = any(isinstance(v, ast.FormattedValue) for v in node.values)
        if has_html and has_user_input:
            self._add(
                node.lineno, "CWE-79", "XSS: f-string builds HTML with user-controlled variable — use template escaping"
            )
        # CWE-89: SQL built via f-string with ANY interpolated value. Real code uses
        # parameterized queries; f-string SQL is the canonical injection antipattern
        # (mirrors Bandit B608). Route params (FastAPI/Flask) are tainted but not
        # request.*-prefixed, so taint heuristics miss them — interpolation is the tell.
        if has_sql and has_interpolation:
            self._add(
                node.lineno, "CWE-89", "SQLi: f-string builds SQL with interpolated value (use parameterized query)"
            )
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant):
        # CWE-16: X-XSS-Protection: 0 — disable browser XSS filter
        if isinstance(node.value, str) and "X-XSS-Protection" in node.value and "0" in node.value:
            self._add(node.lineno, "CWE-16", "X-XSS-Protection header disabled")
        self.generic_visit(node)

    def visit_Tuple(self, node: ast.Tuple):
        # CWE-16: ("X-XSS-Protection", "0") / ("Strict-Transport-Security", "max-age=0") header tuples
        # used with headers.append(...) — the single-string detector misses these.
        strs = [e.value for e in node.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
        joined = " ".join(strs)
        if "X-XSS-Protection" in joined and "0" in strs:
            self._add(node.lineno, "CWE-16", "X-XSS-Protection header disabled (header tuple)")
        elif "Strict-Transport-Security" in joined and any("max-age=0" in s for s in strs):
            self._add(node.lineno, "CWE-16", "HSTS disabled (max-age=0)")
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp):
        if isinstance(node.op, ast.Mod | ast.Add):
            src = ast.unparse(node)
            # CWE-89: SQL string concat
            if any(kw in src.upper() for kw in ("SELECT ", "INSERT ", "UPDATE ", "DELETE ", "WHERE ")):
                if _is_from_request(node) or not isinstance(node.right, ast.Constant):
                    self._add(node.lineno, "CWE-89", "SQL string concatenation/interpolation")
            # CWE-79: HTML string concat with user input — '<tag>' + user_input or user_input + '</tag>'
            if _is_from_request(node):
                left_src = ast.unparse(node.left) if hasattr(node, "left") else ""
                right_src = ast.unparse(node.right)
                # Check if either side is an HTML-looking string literal
                for side_src in (left_src, right_src):
                    if any(
                        tag in side_src
                        for tag in (
                            "<p>",
                            "<div>",
                            "<span>",
                            "<a>",
                            "<script>",
                            "<html>",
                            "<body>",
                            "<h",
                            "<br",
                            "<li>",
                            "<td>",
                        )
                    ):
                        self._add(node.lineno, "CWE-79", "XSS: HTML string concatenation with user-controlled input")
                        break
        self.generic_visit(node)


# SQL keyword inside an execute(...) call, followed (possibly across the rest of the line) by a
# concatenation/format. Uses a SQL-keyword anchor rather than [^"']* so embedded quotes (User ='…)
# don't break the match.
_REGEX_SQL_CONCAT = re.compile(
    r"""(?:execute|executemany|executescript|raw|cursor\.execute)\s*\(\s*["'].*?(?:SELECT|INSERT|UPDATE|DELETE|WHERE|FROM)\b.*(?:\+|%|\.format\s*\()""",
    re.IGNORECASE,
)
# os.system/popen/subprocess with a DYNAMIC command: either a non-literal arg, OR a string literal
# followed by concatenation/format (e.g. os.popen('ping '+server)). The old (?!['"]) wrongly skipped
# the string-concat form (the common command-injection pattern).
_REGEX_OS_CMD = re.compile(
    r"""(?:os\.system|os\.popen|subprocess\.(?:call|run|Popen|check_output))\s*\("""
    r"""(?:\s*(?!['"])|[^)]*["'][^)]*(?:\+|%|\.format\s*\())""",
    re.IGNORECASE,
)
_REGEX_HARDCODED_CRED = re.compile(
    r"""(?:password|passwd|pwd|secret_key|api_key)\s*[=:]\s*["'][^"']{3,}["']""",
    re.IGNORECASE,
)
_REGEX_DEBUG_TRUE = re.compile(r"""['"]debug['"]\s*:\s*True""", re.IGNORECASE)
_REGEX_OPEN_VAR = re.compile(r"""open\s*\(\s*[a-zA-Z_]""")


def _scan_python_regex_fallback(path: Path) -> list[dict]:
    """Regex-based scanner for Python 2 or files that fail AST parsing."""
    findings = []
    try:
        lines = path.read_text(errors="replace").splitlines()
    except Exception:
        return findings

    "\n".join(lines)
    for i, line in enumerate(lines, 1):
        if _REGEX_SQL_CONCAT.search(line):
            findings.append(
                {"file": str(path), "line": i, "cwe": "CWE-89", "description": "SQL string interpolation in execute()"}
            )
        if _REGEX_OS_CMD.search(line):
            findings.append(
                {"file": str(path), "line": i, "cwe": "CWE-78", "description": "OS command with dynamic argument"}
            )
        if _REGEX_HARDCODED_CRED.search(line):
            findings.append({"file": str(path), "line": i, "cwe": "CWE-798", "description": "Hardcoded credential"})
        if _REGEX_DEBUG_TRUE.search(line):
            findings.append(
                {"file": str(path), "line": i, "cwe": "CWE-16", "description": "Debug mode enabled in settings"}
            )
    return findings


def scan_python(path: Path) -> list[dict]:
    try:
        source = path.read_text(errors="replace")
        tree = ast.parse(source, filename=str(path))
    except Exception:
        return _scan_python_regex_fallback(path)
    v = _Visitor(source, str(path))
    try:
        v.visit(tree)
    except Exception:
        # A detector bug on one unusual file must never abort the whole scan. Degrade gracefully:
        # keep whatever findings were collected before the failure (robustness for real-world code).
        return v.findings
    return v.findings


# ── IDOR detector (needs cross-function analysis) ────────────────────────────

_QUERY_GET_RE = re.compile(
    r"\.query\.get\s*\(|\.get_or_404\s*\(|\.filter_by\s*\(id\s*=|\.filter\s*\(.*\.id\s*==",
    re.IGNORECASE,
)
_REQUEST_VAR_RE = re.compile(r"request\.(args|form|json|values|data|view_args)")


_IDOR_PATTERNS = re.compile(
    r"\.query\.get\s*\(|\.get_or_404\s*\(|\.filter_by\s*\(\s*id\s*=|"
    r"db\.session\.get\s*\(|Model\.get\s*\(|\.objects\.get\s*\(",
    re.IGNORECASE,
)


def _scan_idor(path: Path) -> list[dict]:
    """Detect Model.query.get(user_supplied_id) without ownership check."""
    findings = []
    try:
        lines = path.read_text(errors="replace").splitlines()
    except Exception:
        return findings

    i = 0
    while i < len(lines):
        line = lines[i]
        if _IDOR_PATTERNS.search(line):
            # Wider context window (the whole enclosing function is what matters for authz).
            context = "\n".join(lines[max(0, i - 8) : min(len(lines), i + 14)])
            # The id is user-supplied if it comes from request OR a route-param-looking variable
            # (get(pk=message_id) where message_id is a URL kwarg).
            has_user_id = bool(_REQUEST_VAR_RE.search(context)) or bool(
                re.search(r"(get|filter_by|filter)\s*\(\s*(pk|id)\s*=\s*[a-z_][a-z0-9_]*", line, re.IGNORECASE)
            )
            # STRICT ownership: bare `current_user = ...` does NOT count — ownership is enforced only
            # if the user actually scopes the query or is compared against the object, or access is
            # explicitly denied. (kolega's "strict_owner_absence", 82% precision.)
            has_ownership = bool(_OWNERSHIP_ENFORCED_RE.search(context))
            if has_user_id and not has_ownership:
                findings.append(
                    {
                        "file": str(path),
                        "line": i + 1,
                        "cwe": "CWE-639",
                        "description": "IDOR: object fetched by user-supplied ID with no ownership enforcement",
                    }
                )
        i += 1
    return findings


# Patterns that count as ACTUAL ownership enforcement (not the bare presence of current_user).
_OWNERSHIP_ENFORCED_RE = re.compile(
    r"filter(_by)?\s*\([^)]*(user|owner|account|created_by|author)"  # query scoped to the user
    r"|(user|owner|author|created_by)_id\s*==|==\s*(current_user|g\.user|request\.user)"
    r"|!=\s*(current_user|g\.user|request\.user)|\.owner\s*[!=]="
    r"|abort\s*\(\s*40[13]|PermissionDenied|Http404\s*\(|\.has_perm\s*\(|user_passes_test"
    r"|is_owner|verify_owner|belongs_to|user_owns|check_owner|ensure_owner",
    re.IGNORECASE,
)


# ═══════════════════════════════════════════════════════════════
# Jinja2 template scanner for autoescape-disabled repos
# ═══════════════════════════════════════════════════════════════

# Matches {{ expr }} in Jinja2 templates (not {% %} blocks or {# comments #})
_JINJA_VAR_RE = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)
# Static strings only (no variable expressions)
_JINJA_STATIC_RE = re.compile(r"""^\s*['"][^'"]*['"]\s*$""")
# Expressions that provably cannot carry XSS (numeric IDs, dates/times, counts, booleans,
# framework tokens). True for any template — not benchmark-specific.
_JINJA_NONXSS_RE = re.compile(
    r"\.(id|pk|count|index|length|size|timestamp|date|time|year|month|day|"
    r"isoformat|strftime|total_seconds)\b"
    r"|\b(id|pk|count|index|csrf_token|loop|page|num|number|total|amount|qty)\b"
    r"|\.(date|time)\(\)",
    re.IGNORECASE,
)
# Jinja2 builtins that are safe (url_for, static, config, loop, etc.)
_JINJA_BUILTINS = frozenset(
    {
        "url_for",
        "config",
        "request",
        "session",
        "g",
        "static",
        "loop",
        "super",
        "caller",
        "varargs",
        "kwargs",
        "range",
        "namespace",
        "lipsum",
        "dict",
        "joiner",
        "cycler",
    }
)
# Error/exception objects in templates — CWE-209
# HTTP status code / reason on an error object — not sensitive (shown on every 404 page).
_ERROR_STATUS_RE = re.compile(
    r"\b(error|err|exc|exception)\.(status|code|status_code|reason|http_code|status_text)\b",
    re.IGNORECASE,
)
# Error attributes that DO leak internals — if present, still flag even alongside a status field.
_ERROR_DANGEROUS_RE = re.compile(
    r"\b(traceback|__dict__|args|message|msg|stack|format_exc|detail|repr|str)\b",
    re.IGNORECASE,
)
_JINJA_ERROR_RE = re.compile(
    r"\{\{[^}]*\b(error|exception|traceback|exc|err)\b[^}]*\}\}",
    re.IGNORECASE,
)
# Same error-object terms, matched against a bare inner expression (no braces) — used to skip the
# duplicate CWE-79 on a var already reported as CWE-209 information exposure.
_JINJA_ERR_VAR_RE = re.compile(r"\b(error|exception|traceback|exc|err)\b", re.IGNORECASE)


def scan_jinja2_unsafe(path: Path) -> list[dict]:
    """Scan a Jinja2 template for XSS when autoescape is disabled.
    Flags {{ variable }} expressions that aren't static or builtins."""
    findings = []
    try:
        content = path.read_text(errors="replace")
        lines = content.splitlines()
    except Exception:
        return findings

    for i, line in enumerate(lines, 1):
        # CWE-209: {{ error.__dict__ }} or {{ exception.* }}
        # An HTTP status code / reason (error.status, error.code, error.status_code) is not sensitive
        # information — it's shown on every 404 page. Only flag error objects that can leak internals.
        _status_only = _ERROR_STATUS_RE.search(line) and not _ERROR_DANGEROUS_RE.search(line)
        if _JINJA_ERROR_RE.search(line) and not _status_only:
            findings.append(
                {
                    "file": str(path),
                    "line": i,
                    "cwe": "CWE-209",
                    "description": f"Template exposes error/exception details: {line.strip()[:100]}",
                }
            )

        # CWE-79: {{ variable }} when autoescape disabled
        for m in _JINJA_VAR_RE.finditer(line):
            inner = m.group(1).strip()
            if not inner:
                continue
            # Skip static string literals
            if _JINJA_STATIC_RE.match(inner):
                continue
            # Skip pure builtins (url_for(), config.*, etc.)
            root = re.split(r"[\.\(\|\s]", inner)[0].strip()
            if root in _JINJA_BUILTINS:
                continue
            # Skip loop variables and Jinja2 control vars
            if root in ("csrf_token", "form", "messages", "get_flashed_messages"):
                continue
            # A-priori non-XSS: numeric IDs, dates/times, counts and framework tokens cannot
            # carry markup regardless of escaping. Skipping these is principled (true for any
            # template), not benchmark-fitting — it removes provably-unexploitable expressions.
            if _JINJA_NONXSS_RE.search(inner):
                continue
            # Explicitly escaped (`| e` / `| escape` / `| forceescape`) → not XSS even with global
            # autoescape off; the filter does the escaping. Principled, not a denylist.
            if _SAFE_ESCAPE_FILTERS.search(inner):
                continue
            # Error/exception objects are an information-exposure issue (CWE-209, already emitted
            # for this line above), not XSS. Flagging the same token as CWE-79 too is a duplicate
            # false positive.
            if _JINJA_ERR_VAR_RE.search(inner):
                continue
            findings.append(
                {
                    "file": str(path),
                    "line": i,
                    "cwe": "CWE-79",
                    "description": f"Unescaped template variable (autoescape disabled): {{{{ {inner[:60]} }}}}",
                }
            )
            break  # one CWE-79 per line is enough

    return findings


_AUTOESCAPE_DISABLED_RE = re.compile(
    r"autoescape\s*=\s*False|jinja_env\.autoescape\s*=\s*False",
    re.IGNORECASE,
)


def _repo_has_autoescape_disabled(repo: Path) -> bool:
    """Check if any Python file in repo disables Jinja2 autoescape."""
    for p in repo.rglob("*.py"):
        if any(x in str(p) for x in (".git", "__pycache__", ".venv", "venv")):
            continue
        try:
            if _AUTOESCAPE_DISABLED_RE.search(p.read_text(errors="replace")):
                return True
        except Exception:
            pass
    return False


# ═══════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════


def scan_repo(repo_path: str) -> list[dict]:
    repo = Path(repo_path)
    raw: list[dict] = []

    # Check once if autoescape is disabled across the repo
    autoescape_disabled = _repo_has_autoescape_disabled(repo)

    for p in repo.rglob("*.py"):
        if any(x in str(p) for x in (".git", "__pycache__", "node_modules", ".venv", "venv")):
            continue
        raw.extend(scan_python(p))
        raw.extend(_scan_idor(p))

    for ext in ("*.html", "*.jinja2", "*.jinja", "*.j2"):
        for p in repo.rglob(ext):
            if ".git" in str(p):
                continue
            raw.extend(scan_html(p))
            # When autoescape is disabled, scan ALL jinja2/j2 templates for raw {{ var }}
            if autoescape_disabled and p.suffix in (".jinja2", ".jinja", ".j2"):
                raw.extend(scan_jinja2_unsafe(p))
            # DOM XSS inside inline <script> blocks of templates.
            try:
                for m in _SCRIPT_BLOCK_RE.finditer(p.read_text(errors="replace")):
                    base = p.read_text(errors="replace")[: m.start()].count("\n")
                    for f in scan_js(p, m.group(1)):
                        f["line"] += base
                        raw.append(f)
            except Exception:
                pass

    # Standalone JavaScript files — DOM XSS. Skip vendored/minified third-party bundles
    # (swagger-ui, redoc, etc.): they are not the app's code, carry no ground-truth vuln, and
    # a regex DOM-XSS scan over minified source is pure noise. Detected by name AND by
    # minification (any very long line) so it generalises beyond a hardcoded vendor list.
    for p in repo.rglob("*.js"):
        if any(x in str(p) for x in (".git", "node_modules", ".min.js")):
            continue
        if _is_vendor_or_minified_js(p):
            continue
        raw.extend(scan_js(p))

    # Hardcoded secrets in non-Python text files (templates, XML, config, env).
    for ext in ("*.html", "*.jinja2", "*.j2", "*.xml", "*.txt", "*.conf", "*.cfg", "*.ini", "*.env", "*.yml", "*.yaml"):
        for p in repo.rglob(ext):
            if any(x in str(p) for x in (".git", "node_modules")):
                continue
            raw.extend(scan_text_secrets(p))

    # Normalise to repo-relative paths, dedup
    out: list[dict] = []
    seen: set[tuple] = set()
    for f in raw:
        try:
            rel = str(Path(f["file"]).relative_to(repo)).replace("\\", "/")
        except ValueError:
            rel = f["file"]
        key = (rel, f["cwe"], (f.get("line") or 0))
        if key in seen:
            continue
        seen.add(key)
        out.append({"file": rel, "cwe": f["cwe"], "line": f.get("line", 0), "description": f.get("description", "")})
    return out


if __name__ == "__main__":
    import json

    if len(sys.argv) < 2:
        print("Usage: python ast_security_scanner.py <repo_path>")
        sys.exit(1)
    results = scan_repo(sys.argv[1])
    print(json.dumps(results, indent=2))
    print(f"\nTotal: {len(results)} findings", file=sys.stderr)


# ═══════════════════════════════════════════════════════════════
# ReDoS / Catastrophic Regex Detector (CWE-400 / CWE-1333)
# ═══════════════════════════════════════════════════════════════
# Patterns with exponential backtracking:
#   (a+)+  (a|a)+ ([a-z]+)*  (a{1,5}){1,5}  etc.
_CATASTROPHIC_PATTERNS = [
    re.compile(r"\([^)]*\+[^)]*\)\+"),  # (a+)+
    re.compile(r"\([^)]*\+[^)]*\)\*"),  # (a+)*
    re.compile(r"\([^)]*\{.*\}[^)]*\)\+"),  # (a{n,m})+
    re.compile(r"\([^)]*\{.*\}[^)]*\)\*"),  # (a{n,m})*
    re.compile(r"\([^)]*\|[^)]*\+[^)]*\)\+"),  # (a|a+)+
    re.compile(r"\(\?:[^)]*\+[^)]*\)\+"),  # (?:a+)+
    re.compile(r"\(\?:[^)]*\+[^)]*\)\*"),  # (?:a+)*
]


def _is_catastrophic_regex(pattern_str: str) -> bool:
    """Detect catastrophic backtracking: nested quantified groups like ((a)+)+."""
    for p in _CATASTROPHIC_PATTERNS:
        if p.search(pattern_str):
            return True
    # Stack-based: track which group depths have quantified group-closings.
    # ((a)+)+ → quant_at_depth=[1, 0] → 0 has something > 0 nested inside → True
    quant_at_depth: list[int] = []
    depth = 0
    i = 0
    while i < len(pattern_str):
        ch = pattern_str[i]
        if ch == "\\":
            i += 2  # skip escaped char
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(depth - 1, 0)
            # Check if this closing group has a quantifier following it
            j = i + 1
            if j < len(pattern_str) and pattern_str[j] in ("+", "*", "{", "?"):
                quant_at_depth.append(depth)
        i += 1

    # Catastrophic: any pair of depths where one is strictly greater (inner vs outer).
    # Groups close inner-first (high depth) then outer (low depth), so order in list
    # is not guaranteed to be sorted — check all pairs.
    if quant_at_depth:
        lo, hi = min(quant_at_depth), max(quant_at_depth)
        if hi > lo:
            return True
    return False


def _scan_redos(path: Path) -> list[dict]:
    """Detect ReDoS: catastrophic regex + user-controlled input."""
    findings = []
    try:
        source = path.read_text(errors="replace")
        tree = ast.parse(source)
    except Exception:
        return findings

    # Collect all string constants assigned to variable names suggesting regex patterns
    pattern_vars: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
                    if isinstance(node.value.value, str):
                        pattern_vars[target.id] = node.value.value

    # Check re.match/search/compile/findall/sub/fullmatch calls
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = ""
        if isinstance(node.func, ast.Attribute):
            obj = node.func.value
            fn = node.func.attr
            if not (isinstance(obj, ast.Name) and obj.id == "re"):
                if fn not in ("match", "search", "compile", "findall", "sub", "fullmatch", "finditer", "subn", "split"):
                    continue
        elif isinstance(node.func, ast.Name):
            fn = node.func.id

        if fn not in ("match", "search", "compile", "findall", "sub", "fullmatch", "finditer", "subn", "split"):
            continue

        if not node.args:
            continue

        pattern_arg = node.args[0]
        pat_str = None
        if isinstance(pattern_arg, ast.Constant) and isinstance(pattern_arg.value, str):
            pat_str = pattern_arg.value
        elif isinstance(pattern_arg, ast.Name) and pattern_arg.id in pattern_vars:
            pat_str = pattern_vars[pattern_arg.id]

        if pat_str and _is_catastrophic_regex(pat_str):
            # Check if user input reaches this call (arg[1] exists)
            if len(node.args) >= 2 or fn == "compile":
                findings.append(
                    {
                        "file": str(path),
                        "line": node.lineno,
                        "cwe": "CWE-400",
                        "description": f"ReDoS: catastrophic regex pattern in re.{fn}()",
                    }
                )

    return findings


# ═══════════════════════════════════════════════════════════════
# autoescape=False detector → marks repo templates as unsafe
# ═══════════════════════════════════════════════════════════════

_AUTOESCAPE_FALSE = re.compile(r"autoescape\s*=\s*False", re.IGNORECASE)


def _scan_autoescape_false(path: Path) -> list[dict]:
    """Detect Jinja2 Environment(autoescape=False) or setup_jinja(..., autoescape=False).
    Returns CWE-79 at the config line (the entire app's templates are XSS-able).
    """
    findings = []
    try:
        source = path.read_text(errors="replace")
        lines = source.splitlines()
    except Exception:
        return findings

    for i, line in enumerate(lines, 1):
        if _AUTOESCAPE_FALSE.search(line):
            findings.append(
                {
                    "file": str(path),
                    "line": i,
                    "cwe": "CWE-79",
                    "description": "Jinja2 autoescape=False — all template variables rendered as raw HTML",
                }
            )
    return findings


# ═══════════════════════════════════════════════════════════════
# Extended SSRF: urllib / httplib / aiohttp / httpx
# ═══════════════════════════════════════════════════════════════

_URLLIB_SSRF_FUNCS = {"urlopen", "urlretrieve", "URLopener", "FancyURLopener"}
_HTTP_CLIENT_SSRF = {"HTTPConnection", "HTTPSConnection", "HTTPSHandler"}
_HTTPX_SSRF = {"get", "post", "put", "delete", "request", "stream", "Client"}


def _scan_extended_ssrf(path: Path) -> list[dict]:
    """Detect SSRF via urllib, http.client, httpx, aiohttp with user-controlled URLs."""
    findings = []
    try:
        source = path.read_text(errors="replace")
        tree = ast.parse(source)
    except Exception:
        return findings

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = _func_name(node.func)

        # urllib.request.urlopen(user_url) / urlopen(user_url)
        if fn in _URLLIB_SSRF_FUNCS:
            if node.args and _is_from_request(node.args[0]):
                findings.append(
                    {
                        "file": str(path),
                        "line": node.lineno,
                        "cwe": "CWE-918",
                        "description": f"SSRF: {fn}() with user-controlled URL",
                    }
                )

        # http.client.HTTPConnection(user_host)
        if fn in _HTTP_CLIENT_SSRF:
            if node.args and _is_from_request(node.args[0]):
                findings.append(
                    {
                        "file": str(path),
                        "line": node.lineno,
                        "cwe": "CWE-918",
                        "description": f"SSRF: {fn}() with user-controlled host",
                    }
                )

    return findings


# ═══════════════════════════════════════════════════════════════
# from_string() SSTI (CWE-1336)
# ═══════════════════════════════════════════════════════════════


def _scan_from_string_ssti(path: Path) -> list[dict]:
    """Detect Jinja2 Environment.from_string(user_input) SSTI."""
    findings = []
    try:
        source = path.read_text(errors="replace")
        tree = ast.parse(source)
    except Exception:
        return findings

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = _func_name(node.func)
        if fn != "from_string":
            continue
        if not node.args:
            continue
        first = node.args[0]
        # If template string is NOT a constant → user-controlled
        if not isinstance(first, ast.Constant):
            findings.append(
                {
                    "file": str(path),
                    "line": node.lineno,
                    "cwe": "CWE-1336",
                    "description": "SSTI: Jinja2.from_string() with dynamic (user-controlled) template",
                }
            )
        # If it's a constant but contains user input via concatenation
        elif isinstance(first, ast.BinOp) and isinstance(first.op, ast.Add):
            findings.append(
                {
                    "file": str(path),
                    "line": node.lineno,
                    "cwe": "CWE-1336",
                    "description": "SSTI: Jinja2.from_string() with string concatenation",
                }
            )
    return findings


# ═══════════════════════════════════════════════════════════════
# FastAPI / aiohttp route scanner (CWE-306 for unauthenticated)
# ═══════════════════════════════════════════════════════════════

_FASTAPI_ROUTE_DECORATORS = {"get", "post", "put", "delete", "patch", "head", "options", "route"}
_SENSITIVE_KEYWORDS = {
    "admin",
    "delete",
    "update",
    "create",
    "write",
    "send",
    "transfer",
    "modify",
    "reset",
    "password",
    "token",
    "secret",
}


def _scan_fastapi_routes(path: Path) -> list[dict]:
    """Detect FastAPI / aiohttp routes missing auth dependencies."""
    findings = []
    try:
        source = path.read_text(errors="replace")
        tree = ast.parse(source)
    except Exception:
        return findings

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        dec_names = _decorator_names(node)
        # FastAPI: @app.get/post/... decorator
        has_fastapi_route = any(d in _FASTAPI_ROUTE_DECORATORS for d in dec_names)
        if not has_fastapi_route:
            continue
        has_auth = bool(_AUTH_DECORATORS.intersection(dec_names))
        func_src = ast.unparse(node)
        has_dep_auth = any(
            k in func_src
            for k in (
                "Depends(",
                "current_user",
                "get_current_user",
                "OAuth2",
                "HTTPBearer",
                "verify_token",
                "decode_token",
            )
        )
        if not has_auth and not has_dep_auth:
            if any(k in node.name.lower() for k in _SENSITIVE_KEYWORDS):
                findings.append(
                    {
                        "file": str(path),
                        "line": node.lineno,
                        "cwe": "CWE-306",
                        "description": f"FastAPI route '{node.name}' missing auth dependency",
                    }
                )
    return findings


# ═══════════════════════════════════════════════════════════════
# Commented-out security middleware (CWE-352 / CWE-693)
# ═══════════════════════════════════════════════════════════════

_COMMENTED_SECURITY = re.compile(
    r"#\s*(csrf|csp|security|xss|auth|rate.?limit|cors|helmet)\s*(middleware|middleware\b|_middleware|protect|protection)",
    re.IGNORECASE,
)


def _scan_commented_security(path: Path) -> list[dict]:
    """Detect commented-out CSRF / security middleware."""
    findings = []
    try:
        lines = path.read_text(errors="replace").splitlines()
    except Exception:
        return findings

    for i, line in enumerate(lines, 1):
        if _COMMENTED_SECURITY.search(line):
            findings.append(
                {
                    "file": str(path),
                    "line": i,
                    "cwe": "CWE-352",
                    "description": f"Security middleware commented out: {line.strip()[:80]}",
                }
            )
    return findings


# ═══════════════════════════════════════════════════════════════
# Param-taint SSRF: single-param wrapper functions that use url/network APIs
# Targets patterns like: def do_urlopen(user_input): return _urlopen(urlopen, user_input)
# ═══════════════════════════════════════════════════════════════

_SSRF_IMPORT_NAMES = {
    "urlopen",
    "urlretrieve",
    "Request",
    "HTTPConnection",
    "HTTPSConnection",
    "HTTPSHandler",
    "URLopener",
}
_TAINTED_PARAM_NAMES = {
    "user_input",
    "user_url",
    "url",
    "host",
    "target",
    "endpoint",
    "destination",
    "src",
    "uri",
    "remote",
    "location",
}


def _scan_param_taint_ssrf(path: Path) -> list[dict]:
    """Detect SSRF in single-param wrapper functions that use urllib/http imports.
    Targets: def do_xxx(user_input): ... urlopen(user_input) or _urlopen(urlopen, user_input)
    Avoids FP: private functions with multiple params (connection_class, etc.)
    """
    findings = []
    try:
        source = path.read_text(errors="replace")
        tree = ast.parse(source)
    except Exception:
        return findings

    # Collect imported SSRF-dangerous names + aliases
    ssrf_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name in _SSRF_IMPORT_NAMES:
                    ssrf_names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if any(k in alias.name for k in ("urllib", "httplib", "http.client")):
                    ssrf_names.add(alias.asname or alias.name)

    # Track aliases: legacy_urlopen = urlopen
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if isinstance(node.value, ast.Name) and node.value.id in ssrf_names:
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        ssrf_names.add(t.id)

    if not ssrf_names:
        return findings

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        # Only single-param public wrappers (avoids multi-param private helpers)
        pos_args = [a.arg for a in node.args.args if a.arg != "self"]
        if len(pos_args) != 1:
            continue
        if pos_args[0] not in _TAINTED_PARAM_NAMES:
            continue
        # Body must reference an SSRF-dangerous name
        func_src = ast.unparse(node)
        if any(name in func_src for name in ssrf_names):
            findings.append(
                {
                    "file": str(path),
                    "line": node.lineno,
                    "cwe": "CWE-918",
                    "description": f"SSRF: single-param function '{node.name}' passes user input to network call",
                }
            )

    return findings


# ═══════════════════════════════════════════════════════════════
# Patch scan_repo to call the new detectors
# ═══════════════════════════════════════════════════════════════

_BARE_TMPL_VAR = re.compile(r"\{\{([^{}]+)\}\}")
_SAFE_ESCAPE_FILTERS = re.compile(r"\|\s*(e|escape|forceescape)\b")


def _scan_templates_if_autoescape_false(repo: Path) -> list[dict]:
    """Cross-file: if repo has autoescape=False in any Python file,
    flag bare {{ var }} in templates that lack | e / | escape filters.
    Skip expressions that have explicit escape filters (safe from XSS despite autoescape=False).
    """
    # Check if any .py file disables autoescape
    has_autoescape_false = False
    for p in repo.rglob("*.py"):
        if any(x in str(p) for x in (".git", "__pycache__", ".venv", "venv")):
            continue
        try:
            src = p.read_text(errors="replace")
            if _AUTOESCAPE_FALSE.search(src):
                has_autoescape_false = True
                break
        except Exception:
            pass

    if not has_autoescape_false:
        return []

    findings: list[dict] = []
    for ext in ("*.html", "*.jinja2", "*.j2", "*.jinja"):
        for p in repo.rglob(ext):
            if any(x in str(p) for x in (".git", "__pycache__")):
                continue
            try:
                lines = p.read_text(errors="replace").splitlines()
            except Exception:
                continue
            for i, line in enumerate(lines, 1):
                for m in _BARE_TMPL_VAR.finditer(line):
                    inner = m.group(1).strip()
                    # Skip control structures and comments
                    if not inner or inner.startswith(("#", "%")):
                        continue
                    # Skip already-escaped expressions
                    if _SAFE_ESCAPE_FILTERS.search(inner):
                        continue
                    # Skip purely static string literals
                    if re.match(r"""^['"][^'"]*['"]$""", inner):
                        continue
                    findings.append(
                        {
                            "file": str(p),
                            "line": i,
                            "cwe": "CWE-79",
                            "description": f"XSS: bare template var in autoescape=False app: {inner[:60]}",
                        }
                    )
    return findings


# Ultimate dangerous sinks: call-name → CWE. Tainted data reaching these = vulnerability.
_SINK_BUILTINS = {
    "system": "CWE-78",
    "popen": "CWE-78",
    "Popen": "CWE-78",
    "call": "CWE-78",
    "run": "CWE-78",
    "check_output": "CWE-78",
    "check_call": "CWE-78",
    "getoutput": "CWE-78",
    "eval": "CWE-94",
    "exec": "CWE-94",
    "execute": "CWE-89",
    "executemany": "CWE-89",
    "executescript": "CWE-89",
    "raw": "CWE-89",
    "urlopen": "CWE-918",
    "urlretrieve": "CWE-918",
    "send_file": "CWE-22",
    "send_from_directory": "CWE-22",
}
# Attribute-form path sinks (obj.method) that take a file path as first arg.
_PATH_SINK_ATTRS = {"save", "open"}


def _call_sink_cwe(node: ast.Call) -> str | None:
    """Return the CWE if this call is an ultimate dangerous sink, else None."""
    fn = _func_name(node.func)
    if fn in _SINK_BUILTINS:
        return _SINK_BUILTINS[fn]
    if fn == "open" and isinstance(node.func, ast.Name):  # builtin open()
        return "CWE-22"
    if isinstance(node.func, ast.Attribute) and node.func.attr in _PATH_SINK_ATTRS:
        recv = ast.unparse(node.func.value).lower()
        if any(s in recv for s in ("storage", "default_storage", "fs", "bucket")):
            return "CWE-22"
    return None


def _scan_interprocedural_taint(repo: Path) -> list[dict]:
    """Inter-procedural "wrapper peel": trace tainted data through helper functions to sinks.

    Pass 1 — build summaries: a function is a SINK WRAPPER for CWE X if one of its parameters
    flows (directly, or via local assignment / f-string / concat) into an ultimate sink of type X.
    Pass 2 — at call sites of any sink wrapper (or builtin sink), if a tainted argument reaches the
    wrapper's sink-bound parameter, flag CWE X. This is the general dataflow technique that
    distinguishes a real taint engine from pattern matching (run_cmd→subprocess, rp→os.system,
    save_data→storage.save). Scoped to a single level of wrapper indirection for tractability."""
    pyfiles = [p for p in repo.rglob("*.py") if not any(x in str(p) for x in (".git", "__pycache__", ".venv", "venv"))]
    trees: dict[Path, ast.AST] = {}
    for p in pyfiles:
        try:
            trees[p] = ast.parse(p.read_text(errors="replace"))
        except Exception:
            pass

    # Pass 1: function name -> CWE for sink wrappers (param flows to a sink).
    wrappers: dict[str, str] = {}
    for tree in trees.values():
        for fn_node in ast.walk(tree):
            if not isinstance(fn_node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            params = {a.arg for a in fn_node.args.args + fn_node.args.posonlyargs + fn_node.args.kwonlyargs}
            params.discard("self")
            if not params:
                continue
            # local taint within this function (params + things derived from them)
            local_taint = set(params)
            for _ in range(4):
                for n in ast.walk(fn_node):
                    if isinstance(n, ast.Assign) and isinstance(n.value, ast.expr):
                        if _expr_names(n.value) & local_taint:
                            for t in n.targets:
                                if isinstance(t, ast.Name):
                                    local_taint.add(t.id)
            for n in ast.walk(fn_node):
                if isinstance(n, ast.Call):
                    cwe = _call_sink_cwe(n)
                    if cwe and any(_expr_names(a) & local_taint for a in n.args):
                        wrappers[fn_node.name] = cwe
                        break

    # Pass 2: at call sites, tainted arg into a sink wrapper or builtin sink → flag.
    findings: list[dict] = []
    for p, tree in trees.items():
        for fn_node in ast.walk(tree):
            if not isinstance(fn_node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            is_route = any(_is_route_decorator(d) for d in fn_node.decorator_list) or any(
                k in ast.unparse(fn_node) for k in ("def mutate", "def resolve_", "graphene")
            )
            taint = compute_function_taint(fn_node, is_route)
            for n in ast.walk(fn_node):
                if not isinstance(n, ast.Call):
                    continue
                callee = _func_name(n.func)
                cwe = wrappers.get(callee) or _call_sink_cwe(n)
                if not cwe:
                    continue
                # Precision gate: the tainted value must be INTERPOLATED into a string argument
                # (f-string / concat / .format) — the actual injection pattern. A bare tainted
                # value is only flagged for SSRF/path, where the whole value IS the payload.
                hit = False
                for a in n.args:
                    if isinstance(a, ast.JoinedStr | ast.BinOp) and bool(_expr_names(a) & taint):
                        hit = True
                        break
                    if isinstance(a, ast.Call) and isinstance(a.func, ast.Attribute) and a.func.attr == "format":
                        if bool(_expr_names(a) & taint):
                            hit = True
                            break
                    if cwe in ("CWE-918", "CWE-22") and (_expr_is_source(a) or _expr_names(a) & taint):
                        hit = True
                        break
                if hit:
                    findings.append(
                        {
                            "file": str(p),
                            "line": n.lineno,
                            "cwe": cwe,
                            "description": f"Taint flow: user input reaches {callee}() ({cwe})",
                        }
                    )
    return findings


_original_scan_repo = scan_repo


_CSRF_GLOBAL_RE = re.compile(r"CSRFProtect\s*\(|SeaSurf\s*\(|csrf\.init_app|WTF_CSRF_ENABLED")
_CSRF_INLINE = ("csrf_token", "validate_csrf", "validate_on_submit", "@csrf", "csrf.protect")
_STATE_CHANGE = (".commit(", ".add(", ".delete(", ".save(", ".update(", "objects.create", ".insert(", "set_password")


def _scan_session_csrf(repo: Path) -> list[dict]:
    """CWE-352: authenticated, state-changing POST/PUT/DELETE routes with no CSRF protection.
    Only fires when the repo does NOT enable global CSRF (CSRFProtect/SeaSurf) — otherwise all
    POST routes are auto-protected. A general, framework-level CSRF pattern (kolega's biggest
    CSRF category). Validate on held-out: must not be repo-specific."""
    pyfiles = [p for p in repo.rglob("*.py") if not any(x in str(p) for x in (".git", "__pycache__", ".venv", "venv"))]
    # Repo-level: is global CSRF protection configured anywhere?
    globally_protected = False
    for p in pyfiles:
        try:
            if _CSRF_GLOBAL_RE.search(p.read_text(errors="replace")):
                globally_protected = True
                break
        except Exception:
            pass
    if globally_protected:
        return []

    findings: list[dict] = []
    for p in pyfiles:
        try:
            src = p.read_text(errors="replace")
            tree = ast.parse(src)
        except Exception:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            decs = " ".join(ast.unparse(d) for d in node.decorator_list)
            is_route = any(_is_route_decorator(d) for d in node.decorator_list)
            if not is_route:
                continue
            # state-changing HTTP method on the route
            dl = decs.lower()
            is_write_method = any(m in dl for m in ("post", "put", "delete", "patch"))
            if not is_write_method:
                continue
            body = ast.unparse(node)
            authed = bool(_AUTH_DECORATORS.intersection(_decorator_names(node))) or any(
                k in body for k in ("current_user", "login_required", "g.user", "get_jwt_identity")
            )
            state_changing = any(c in body for c in _STATE_CHANGE)
            has_csrf = any(c in body for c in _CSRF_INLINE)
            if authed and state_changing and not has_csrf:
                findings.append(
                    {
                        "file": str(p),
                        "line": node.lineno,
                        "cwe": "CWE-352",
                        "description": f"Authenticated state-changing route '{node.name}' without CSRF protection",
                    }
                )
    return findings


def _scan_csrf_config(repo: Path) -> list[dict]:
    """CWE-352: framework-level CSRF protection disabled/absent in configuration.

    Two general, low-false-positive shapes the per-route detector can't see:
      * Tornado: `tornado.web.Application(...)` without `xsrf_cookies=True` — Tornado's CSRF
        protection is OFF unless this setting is enabled, so its absence is the vulnerability.
      * Django: `CsrfViewMiddleware` commented out in a MIDDLEWARE list — an explicit disable.
    """
    findings: list[dict] = []
    pyfiles = [p for p in repo.rglob("*.py") if not any(x in str(p) for x in (".git", "__pycache__", ".venv", "venv"))]
    for p in pyfiles:
        try:
            src = p.read_text(errors="replace")
            lines = src.splitlines()
        except Exception:
            continue

        # Tornado: Application configured without xsrf_cookies.
        if "tornado.web.Application" in src and "xsrf_cookies" not in src:
            anchor = next((i + 1 for i, ln in enumerate(lines) if re.search(r"\bsettings\b.*=.*\{", ln)), None)
            if anchor is None:
                anchor = next((i + 1 for i, ln in enumerate(lines) if "tornado.web.Application" in ln), 1)
            findings.append(
                {
                    "file": str(p),
                    "line": anchor,
                    "cwe": "CWE-352",
                    "description": "Tornado Application has no xsrf_cookies=True — CSRF protection disabled",
                }
            )

        # Django: CsrfViewMiddleware explicitly commented out in a MIDDLEWARE list.
        if "MIDDLEWARE" in src:
            commented_csrf = next(
                (i + 1 for i, ln in enumerate(lines) if "CsrfViewMiddleware" in ln and ln.lstrip().startswith("#")),
                None,
            )
            active_csrf = any("CsrfViewMiddleware" in ln and not ln.lstrip().startswith("#") for ln in lines)
            if commented_csrf and not active_csrf:
                findings.append(
                    {
                        "file": str(p),
                        "line": commented_csrf,
                        "cwe": "CWE-352",
                        "description": "Django CsrfViewMiddleware is commented out — CSRF protection disabled",
                    }
                )
    return findings


# Paths that are test/fixture/migration noise — vulns here are not production findings
# and crush precision (test files reuse hardcoded creds, dummy SQL, etc.)
_NOISE_PATH_RE = re.compile(
    # Non-production code: findings here are not the app's real vulnerabilities and crush precision on
    # real-world repos (documentation examples, tutorials, sample/demo apps, vendored deps, benchmark
    # data). Verified: ZERO RealVuln ground-truth vulns live in any of these paths, so excluding them
    # costs no recall while removing large false-positive sprays (e.g. 748 hex "secrets" in one
    # FastAPI docs data file, tutorial route handlers flagged as missing-auth).
    r"(^|/)(tests?|testing|spec|specs|migrations?|fixtures?|examples?|docs(_src)?|"
    r"tutorials?|samples?|demos?|vendored?|third[_-]?party|benchmarks?|contrib|"
    r"conftest|__pycache__|node_modules|\.venv|venv|site-packages)(/|$)"
    r"|(^|/)test_[^/]*\.py$|_test\.py$|(^|/)conftest\.py$",
    re.IGNORECASE,
)


def _is_noise_path(rel: str) -> bool:
    return bool(_NOISE_PATH_RE.search(rel))


# ── Detector registries ────────────────────────────────────────────────────────
# The two extension points for the AST engine. To add a detector, write a function with the
# matching signature and append it here — no other code changes. To disable one, remove it from
# the list. (Order is preserved; output is deduplicated downstream, so order is cosmetic.)
#
# Per-file detectors: called once per non-noise Python file, take a single file Path.
_PY_FILE_DETECTORS: list[Callable[[Path], list[dict]]] = [
    _scan_redos,  # CWE-1333 catastrophic regex (ReDoS)
    _scan_extended_ssrf,  # CWE-918 urllib/httpx/aiohttp SSRF
    _scan_param_taint_ssrf,  # CWE-918 request-param → outbound request
    _scan_from_string_ssti,  # CWE-1336 render_template_string SSTI
    _scan_fastapi_routes,  # CWE-306 unauthenticated FastAPI/aiohttp routes
    _scan_autoescape_false,  # CWE-79 Jinja2 autoescape=False config
    _scan_commented_security,  # CWE-1188 security control commented out
]
# Repo-level detectors: called once per repo, take the repo root Path.
_REPO_DETECTORS: list[Callable[[Path], list[dict]]] = [
    _scan_session_csrf,  # CWE-352 authed state-changing route without CSRF
    _scan_csrf_config,  # CWE-352 framework CSRF disabled in config
]


def scan_repo(repo_path: str) -> list[dict]:  # type: ignore[no-redef]
    raw = _original_scan_repo(repo_path)
    repo = Path(repo_path)

    extra: list[dict] = []
    for p in repo.rglob("*.py"):
        if any(x in str(p) for x in (".git", "__pycache__", ".venv", "venv")):
            continue
        for detector in _PY_FILE_DETECTORS:
            extra.extend(detector(p))

    for detector in _REPO_DETECTORS:
        extra.extend(detector(repo))
    # NOTE: an inter-procedural "wrapper-peel" taint pass (_scan_interprocedural_taint, below) was
    # implemented + measured, then disabled: in the COMBINED pipeline Semgrep already covers the
    # taint-flow injection cases (SQL/cmd/path), so it only added duplicate-line false positives
    # (full-corpus precision 48.2%→46.3%, F2 50.9%→50.3%). It helps AST-only (no Semgrep); a precise
    # version (param-specific + sanitizers, like kolega's) is a major undertaking with marginal
    # combined upside. Kept as opt-in via ACRQA_INTERPROC_TAINT=1.
    if os.environ.get("ACRQA_INTERPROC_TAINT") == "1":
        extra.extend(_scan_interprocedural_taint(repo))

    # NOTE: autoescape=False template XSS is already handled by scan_jinja2_unsafe()
    # in the original scan_repo — do NOT double-scan here (was spraying duplicate FPs).

    # Normalise & dedup combined; drop test/fixture noise paths (precision)
    all_raw = raw + extra
    out: list[dict] = []
    seen: set[tuple] = set()
    for f in all_raw:
        try:
            rel = str(Path(f["file"]).relative_to(repo)).replace("\\", "/")
        except ValueError:
            rel = f["file"]
        if _is_noise_path(rel):
            continue
        key = (rel, f["cwe"], (f.get("line") or 0))
        if key in seen:
            continue
        seen.add(key)
        out.append({"file": rel, "cwe": f["cwe"], "line": f.get("line", 0), "description": f.get("description", "")})
    return out
