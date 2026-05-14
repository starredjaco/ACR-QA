"""Intra-procedural taint analysis engine.

Tracks user-controlled data from HTTP/env sources to dangerous sinks.
Operates per-function using a single-pass AST visitor; no cross-function
propagation (MVP scope).
"""

from __future__ import annotations

import ast
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


def _load_sources() -> list[dict]:
    path = _CONFIG_DIR / "taint_sources.yml"
    with open(path) as f:
        return yaml.safe_load(f)["sources"]


def _load_sinks() -> list[dict]:
    path = _CONFIG_DIR / "taint_sinks.yml"
    with open(path) as f:
        return yaml.safe_load(f)["sinks"]


@dataclass
class TaintInfo:
    source: str
    steps: list[str] = field(default_factory=list)

    def hop(self, step: str) -> TaintInfo:
        return TaintInfo(source=self.source, steps=self.steps + [step])


class _FunctionTaintVisitor(ast.NodeVisitor):
    """Single-function intra-procedural taint visitor."""

    def __init__(
        self,
        source_patterns: set[str],
        sinks_by_name: dict[str, dict],
        filepath: str,
    ) -> None:
        self._source_patterns = source_patterns
        self._sinks = sinks_by_name
        self._filepath = filepath
        # variable name → TaintInfo
        self._tainted: dict[str, TaintInfo] = {}
        self.findings: list[dict] = []

    # ── source detection ──────────────────────────────────────────────────────

    def _extract_source(self, node: ast.expr) -> TaintInfo | None:
        """Return TaintInfo if node is a taint source, else None."""
        if isinstance(node, ast.Attribute):
            full = self._attr_chain(node)
            for pat in self._source_patterns:
                if full == pat or full.startswith(pat + "."):
                    return TaintInfo(source=pat, steps=[ast.unparse(node)])

        if isinstance(node, ast.Subscript):
            # request.form["key"] — subscript access on a source object
            inner = self._extract_source(node.value)
            if inner:
                return inner.hop(ast.unparse(node))

        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute):
                full = self._attr_chain(func)
                for pat in self._source_patterns:
                    if full == pat or full.startswith(pat + "."):
                        return TaintInfo(source=pat, steps=[ast.unparse(node)])
            # os.getenv as bare name after `from os import getenv`
            if isinstance(func, ast.Name) and func.id == "getenv":
                return TaintInfo(source="os.environ", steps=[ast.unparse(node)])
        return None

    @staticmethod
    def _attr_chain(node: ast.expr) -> str:
        parts: list[str] = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
        return ".".join(reversed(parts))

    # ── propagation ───────────────────────────────────────────────────────────

    def _propagate(self, node: ast.expr) -> TaintInfo | None:
        """Return TaintInfo if node carries taint from a tracked variable."""
        if isinstance(node, ast.Name):
            return self._tainted.get(node.id)

        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add | ast.Mod):
            left = self._propagate(node.left)
            right = self._propagate(node.right)
            if left:
                return left.hop(ast.unparse(node))
            if right:
                return right.hop(ast.unparse(node))

        if isinstance(node, ast.JoinedStr):
            for part in ast.walk(node):
                if isinstance(part, ast.Name):
                    t = self._tainted.get(part.id)
                    if t:
                        return t.hop(ast.unparse(node))

        if isinstance(node, ast.Call):
            # method call on a tainted object: tainted_var.strip()
            if isinstance(node.func, ast.Attribute):
                base = self._propagate(node.func.value)
                if base:
                    return base.hop(ast.unparse(node))
            # tainted arg passed through benign function: str(tainted)
            for arg in node.args:
                t = self._propagate(arg)
                if t:
                    return t.hop(ast.unparse(node))

        if isinstance(node, ast.Subscript):
            t = self._propagate(node.value)
            if t:
                return t.hop(ast.unparse(node))

        if isinstance(node, ast.IfExp):
            t = self._propagate(node.body) or self._propagate(node.orelse)
            if t:
                return t

        return None

    # ── visitors ──────────────────────────────────────────────────────────────

    def visit_Assign(self, node: ast.Assign) -> None:
        taint = self._extract_source(node.value) or self._propagate(node.value)
        for target in node.targets:
            if isinstance(target, ast.Name):
                if taint:
                    self._tainted[target.id] = taint.hop(ast.unparse(node))
                else:
                    self._tainted.pop(target.id, None)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        taint = self._propagate(node.value)
        if taint and isinstance(node.target, ast.Name):
            existing = self._tainted.get(node.target.id)
            base = existing or taint
            self._tainted[node.target.id] = base.hop(ast.unparse(node))
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None:
            taint = self._extract_source(node.value) or self._propagate(node.value)
            if isinstance(node.target, ast.Name):
                if taint:
                    self._tainted[node.target.id] = taint.hop(ast.unparse(node))
                else:
                    self._tainted.pop(node.target.id, None)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        sink_name = self._get_sink_name(node.func)
        if sink_name and sink_name in self._sinks:
            for arg in node.args:
                taint = self._extract_source(arg) or self._propagate(arg)
                if taint:
                    self._emit_finding(node, sink_name, taint)
            # also check keyword args (e.g. execute(statement=...))
            for kw in node.keywords:
                if kw.value is not None:
                    taint = self._extract_source(kw.value) or self._propagate(kw.value)
                    if taint:
                        self._emit_finding(node, sink_name, taint)
        self.generic_visit(node)

    def _get_sink_name(self, func: ast.expr) -> str | None:
        if isinstance(func, ast.Name):
            return func.id if func.id in self._sinks else None
        if isinstance(func, ast.Attribute):
            # cursor.execute → "execute"; subprocess.run → "subprocess"
            if func.attr in self._sinks:
                return func.attr
            chain = self._attr_chain(func)
            for name in self._sinks:
                if chain.startswith(name):
                    return name
        return None

    def _emit_finding(self, node: ast.Call, sink_name: str, taint: TaintInfo) -> None:
        sink_meta = self._sinks[sink_name]
        hops = len(taint.steps)
        path = taint.steps + [f"→ {ast.unparse(node)}"]
        self.findings.append(
            {
                "tool": "taint_analyzer",
                "canonical_rule_id": sink_meta["canonical_rule_id"],
                "cwe": sink_meta["cwe"],
                "severity": sink_meta["severity"],
                "file": self._filepath,
                "line": node.lineno,
                "message": (
                    f"Taint flow detected: {taint.source} → {sink_name}() " f"({hops} hop{'s' if hops != 1 else ''})"
                ),
                "taint_source": taint.source,
                "taint_path": path,
                "taint_confidence": max(0.4, 0.95 - 0.1 * max(0, hops - 1)),
            }
        )


class TaintAnalyzer:
    """Public interface: analyze a file or directory for taint flows."""

    def __init__(self) -> None:
        sources = _load_sources()
        self._source_patterns: set[str] = set()
        for s in sources:
            self._source_patterns.update(s["patterns"])

        sinks_raw = _load_sinks()
        self._sinks_by_name: dict[str, dict] = {s["name"]: s for s in sinks_raw}

    def analyze_file(self, filepath: str | Path) -> list[dict[str, Any]]:
        filepath = Path(filepath)
        try:
            source = filepath.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str(filepath))
        except SyntaxError:
            return []

        all_findings: list[dict] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                visitor = _FunctionTaintVisitor(
                    self._source_patterns,
                    self._sinks_by_name,
                    str(filepath),
                )
                visitor.visit(node)
                all_findings.extend(visitor.findings)

        # deduplicate within file: same line + rule
        seen: set[tuple] = set()
        unique: list[dict] = []
        for f in all_findings:
            key = (f["file"], f["line"], f["canonical_rule_id"])
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    def analyze_directory(self, target_dir: str | Path) -> list[dict[str, Any]]:
        target_dir = Path(target_dir)
        findings: list[dict] = []
        for py_file in target_dir.rglob("*.py"):
            try:
                findings.extend(self.analyze_file(py_file))
            except Exception as err:
                logger.debug(f"Taint analysis skipped {py_file}: {err}")
        return findings

    def enrich_findings(
        self,
        findings: list[dict[str, Any]],
        target_dir: str | Path,
    ) -> list[dict[str, Any]]:
        """Generate new taint findings and merge with existing pipeline findings."""
        new_findings = self.analyze_directory(target_dir)
        if new_findings:
            logger.info(f"      - Taint Analyzer: {len(new_findings)} taint flow(s) detected")
        return findings + new_findings
