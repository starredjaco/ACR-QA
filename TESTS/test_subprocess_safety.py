"""Subprocess sandbox audit (v5.0.0 Phase A.4).

Walks every Python file under CORE/, DATABASE/, FRONTEND/, and scripts/ and
asserts that no `subprocess.run` / `subprocess.Popen` / `subprocess.call`
invocation:

  1. Passes `shell=True`.
  2. Passes a raw string (rather than a list) as the command.

These are the two patterns that cause shell-injection in static analyzers' own
code — a category we explicitly check for in user code, so we must hold
ourselves to the same standard. (Dogfooding.)

If a future contributor genuinely needs `shell=True` (e.g. for a tested
pipeline) they can opt-out by adding `# acrqa-subprocess: allow-shell` to the
line — the audit will skip it and surface the exemption in the report.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCAN_DIRS = ("CORE", "DATABASE", "FRONTEND", "scripts")
SUBPROCESS_FUNCS = {"run", "Popen", "call", "check_call", "check_output"}
EXEMPT_MARKER = "acrqa-subprocess: allow-shell"


def _python_files() -> list[Path]:
    out: list[Path] = []
    for d in SCAN_DIRS:
        base = ROOT / d
        if not base.is_dir():
            continue
        for p in base.rglob("*.py"):
            if "__pycache__" in p.parts:
                continue
            out.append(p)
    return out


def _line_is_exempt(source_lines: list[str], lineno: int) -> bool:
    """Look at the call line and a small window above for the exemption marker."""
    start = max(0, lineno - 4)
    end = min(len(source_lines), lineno + 1)
    return any(EXEMPT_MARKER in line for line in source_lines[start:end])


class _SubprocessVisitor(ast.NodeVisitor):
    def __init__(self, source_lines: list[str]):
        self.source_lines = source_lines
        self.shell_true: list[tuple[int, str]] = []
        self.string_args: list[tuple[int, str]] = []

    def _is_subprocess_call(self, node: ast.Call) -> bool:
        # subprocess.run(...)
        if isinstance(node.func, ast.Attribute):
            return node.func.attr in SUBPROCESS_FUNCS and (
                isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess"
            )
        return False

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802 (ast API)
        if self._is_subprocess_call(node):
            if _line_is_exempt(self.source_lines, node.lineno):
                self.generic_visit(node)
                return
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    snippet = (
                        self.source_lines[node.lineno - 1].strip() if 0 < node.lineno <= len(self.source_lines) else ""
                    )
                    self.shell_true.append((node.lineno, snippet))
            # First positional arg must be a list, tuple, or Name binding to a list.
            if node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    snippet = (
                        self.source_lines[node.lineno - 1].strip() if 0 < node.lineno <= len(self.source_lines) else ""
                    )
                    self.string_args.append((node.lineno, snippet))
                # Disallow f-strings / .format / % into argv too — those become
                # plain str regardless of shell.
                elif isinstance(first, ast.JoinedStr | ast.BinOp) and not _line_is_exempt(
                    self.source_lines, node.lineno
                ):
                    snippet = (
                        self.source_lines[node.lineno - 1].strip() if 0 < node.lineno <= len(self.source_lines) else ""
                    )
                    self.string_args.append((node.lineno, snippet))
        self.generic_visit(node)


def _audit_file(path: Path) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return [], []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return [], []
    visitor = _SubprocessVisitor(text.splitlines())
    visitor.visit(tree)
    return visitor.shell_true, visitor.string_args


class TestSubprocessSafety:
    def test_no_shell_true_in_core(self):
        """No `shell=True` anywhere under CORE/, DATABASE/, FRONTEND/, scripts/."""
        violations: list[str] = []
        for p in _python_files():
            shell, _ = _audit_file(p)
            for lineno, snippet in shell:
                violations.append(f"{p.relative_to(ROOT)}:{lineno}: {snippet}")
        assert not violations, (
            "subprocess(shell=True) detected — add `# acrqa-subprocess: allow-shell` to the call line "
            "if intentional:\n  " + "\n  ".join(violations)
        )

    def test_no_string_argv_in_core(self):
        """First positional argument to subprocess must be a list / tuple / Name, never a string."""
        violations: list[str] = []
        for p in _python_files():
            _, strings = _audit_file(p)
            for lineno, snippet in strings:
                violations.append(f"{p.relative_to(ROOT)}:{lineno}: {snippet}")
        assert not violations, (
            "subprocess called with a single string argument (shell-style); pass a list/tuple instead:\n  "
            + "\n  ".join(violations)
        )

    def test_audit_visits_at_least_some_files(self):
        """Sanity: the audit must have something to scan; if scan dirs vanish this catches it."""
        assert len(_python_files()) > 50, f"subprocess audit only found {len(_python_files())} files — did CORE/ move?"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
