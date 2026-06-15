#!/usr/bin/env python3
"""
Build the GP2 defense deck in Dr. Samy's KSIU template style (matches the required
presentation template used across the faculty: navy #002060 + gold, KSIU branding,
project-title header bar, blue section headings, white content slides).

Academic spine (mandated): Introduction → Problem → Motivation → Methodology →
Results → Use Cases → Conclusion → Future Work → Any Questions → Thank You.

Run:    .venv/bin/python3 scripts/build_template_deck.py
Then:   libreoffice --headless --convert-to odp --outdir docs/ docs/ACR-QA_Defense.pptx
"""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

# ── Template palette (extracted from the faculty template) ───────────────────
NAVY = RGBColor(0x00, 0x20, 0x60)
NAVY2 = RGBColor(0x00, 0x16, 0x42)
GOLD = RGBColor(0xD4, 0xAF, 0x37)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
INK = RGBColor(0x1A, 0x1F, 0x2B)
GRAY = RGBColor(0x5B, 0x66, 0x72)
LIGHT = RGBColor(0xF2, 0xF4, 0xF9)
GREEN = RGBColor(0x18, 0x8A, 0x4E)
RED = RGBColor(0xC2, 0x2E, 0x2E)
BLUEROW = RGBColor(0x2A, 0x4B, 0x8C)

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "docs" / "presentation_assets" / "shots"
FIGS = ROOT / "ACR-QA-Book" / "figures"
LOGO = ROOT / "docs" / "presentation_assets" / "ksiu-logo.png"
PHOTOS = ROOT / "docs" / "GEMINI_PHOTOS"
OUT = ROOT / "docs" / "ACR-QA_Defense.pptx"

EMU_W, EMU_H = Inches(13.333), Inches(7.5)
PROJECT_TITLE = "ACR-QA: Automated Code Review & Quality Assurance"


# ── primitives ───────────────────────────────────────────────────────────────
def _bg(slide, color):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = color


def _box(slide, l, t, w, h):
    tb = slide.shapes.add_textbox(l, t, w, h)
    tb.text_frame.word_wrap = True
    return tb.text_frame


def _run(p, text, size, color, *, bold=False, italic=False, font="Calibri"):
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = color
    r.font.name = font
    return r


def _rect(slide, l, t, w, h, fill, *, line=None, rounded=False):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE, l, t, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if line:
        shp.line.color.rgb = line
        shp.line.width = Pt(1)
    else:
        shp.line.fill.background()
    shp.shadow.inherit = False
    return shp


def _center(p):
    p.alignment = PP_ALIGN.CENTER


def _hero(slide, photo, alpha):
    p = PHOTOS / photo
    if not p.exists():
        return
    slide.shapes.add_picture(str(p), 0, 0, width=EMU_W, height=EMU_H)
    shp = _rect(slide, 0, 0, EMU_W, EMU_H, NAVY)
    sf = shp.fill._xPr.find(qn("a:solidFill"))
    clr = sf.find(qn("a:srgbClr"))
    clr.append(clr.makeelement(qn("a:alpha"), {"val": str(int(alpha * 1000))}))


def _fit_image(slide, img, left, top, max_w, max_h):
    """Place an image fitted within a box, preserving aspect, centred in the box."""
    if not img.exists():
        return
    pic = slide.shapes.add_picture(str(img), left, top, width=max_w)
    if pic.height > max_h:
        slide.shapes._spTree.remove(pic._element)
        pic = slide.shapes.add_picture(str(img), left, top, height=max_h)
    pic.left = Emu(int(left + (max_w - pic.width) / 2))
    pic.top = Emu(int(top + (max_h - pic.height) / 2))
    return pic


def _content(prs, heading, page):
    """White content slide with the template header bar + blue section heading. Returns slide."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s, WHITE)
    # top header: project title centred (small), KSIU logo top-right, thin rule
    htf = _box(s, Inches(2.0), Inches(0.18), Inches(9.3), Inches(0.4))
    p = htf.paragraphs[0]
    _center(p)
    _run(p, PROJECT_TITLE, 11, GRAY, italic=True)
    if LOGO.exists():
        s.shapes.add_picture(str(LOGO), Inches(12.55), Inches(0.12), height=Inches(0.5))
    _rect(s, Inches(0.5), Inches(0.66), Inches(12.33), Pt(1.4), NAVY)
    # section heading
    htf2 = _box(s, Inches(0.5), Inches(0.8), Inches(11.0), Inches(0.7))
    _run(htf2.paragraphs[0], heading, 28, NAVY, bold=True)
    # page badge bottom-left
    _rect(s, Inches(0.2), Inches(7.05), Inches(0.4), Inches(0.4), NAVY)
    ptf = _box(s, Inches(0.2), Inches(7.05), Inches(0.4), Inches(0.4))
    ptf.vertical_anchor = MSO_ANCHOR.MIDDLE
    pp = ptf.paragraphs[0]
    _center(pp)
    _run(pp, str(page), 12, WHITE, bold=True)
    return s


# ── slides ───────────────────────────────────────────────────────────────────
def title_slide(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s, NAVY)
    _hero(s, "Gemini_1.png", alpha=66)
    # gold geometric accent strip on the right
    _rect(s, Inches(11.7), 0, Inches(1.63), EMU_H, GOLD)
    _rect(s, Inches(11.4), 0, Inches(0.3), EMU_H, NAVY2)
    # left info blocks
    blocks = [
        ("BRANCH / FACULTY", "El Tur / Faculty of Computer Science and Engineering", 13),
        ("PROGRAM", "Computer Science", 13),
        ("COURSE", "CSE494 — Graduation Project 2", 13),
    ]
    y = Inches(0.7)
    for label, val, sz in blocks:
        ltf = _box(s, Inches(0.7), y, Inches(9.5), Inches(0.32))
        _run(ltf.paragraphs[0], label, 11, GOLD, bold=True)
        vtf = _box(s, Inches(0.7), Emu(y + Inches(0.3)), Inches(10.0), Inches(0.4))
        _run(vtf.paragraphs[0], val, sz, WHITE)
        y = Emu(y + Inches(0.82))
    # project title (big)
    ttf = _box(s, Inches(0.7), Inches(3.25), Inches(10.3), Inches(1.7))
    _run(ttf.paragraphs[0], "PROJECT TITLE", 11, GOLD, bold=True)
    p = ttf.add_paragraph()
    p.space_before = Pt(4)
    _run(p, "ACR-QA", 40, WHITE, bold=True)
    p2 = ttf.add_paragraph()
    _run(p2, "Automated Code Review & Quality Assurance", 22, GOLD, bold=True)
    p3 = ttf.add_paragraph()
    p3.space_before = Pt(4)
    _run(p3, "A trust layer for AI-written code — exploit-verified, cryptographically attested", 12, WHITE, italic=True)
    # presenter + supervisor (right of the logo so nothing overlaps)
    if LOGO.exists():
        s.shapes.add_picture(str(LOGO), Inches(0.7), Inches(5.85), height=Inches(1.0))
    pf = _box(s, Inches(1.95), Inches(5.7), Inches(9.0), Inches(1.4))
    _run(pf.paragraphs[0], "Presented by", 11, GOLD, bold=True)
    p = pf.add_paragraph()
    _run(p, "Ahmed Mahmoud Abbas", 17, WHITE, bold=True)
    p = pf.add_paragraph()
    p.space_before = Pt(8)
    _run(p, "Supervisor", 11, GOLD, bold=True)
    p = pf.add_paragraph()
    _run(p, "Dr. Samy Abdel Nabi", 15, WHITE)
    yr = _box(s, Inches(8.4), Inches(6.95), Inches(3.0), Inches(0.4))
    pr = yr.paragraphs[0]
    pr.alignment = PP_ALIGN.RIGHT
    _run(pr, "KSIU · Egypt · 2026", 11, WHITE)


def outline_slide(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s, NAVY)
    if LOGO.exists():
        s.shapes.add_picture(str(LOGO), Inches(0.5), Inches(0.4), height=Inches(1.05))
    ltf = _box(s, Inches(0.6), Inches(3.0), Inches(3.0), Inches(1.4))
    _run(ltf.paragraphs[0], "PRESENTATION", 14, GOLD, bold=True)
    p = ltf.add_paragraph()
    _run(p, "OUTLINE", 34, WHITE, bold=True)
    sections = [
        "Introduction",
        "Problem Statement",
        "Solution",
        "Methodology",
        "Results & Evaluation",
        "Use Cases",
        "Future Work",
        "Conclusion",
    ]
    x = Inches(4.3)
    w = Inches(8.4)
    row_h = Inches(0.62)
    top = Inches(0.55)
    for i, sec in enumerate(sections):
        y = Emu(top + i * row_h)
        _rect(s, x, y, Inches(0.7), Inches(0.6), GOLD)
        ntf = _box(s, x, y, Inches(0.7), Inches(0.6))
        ntf.vertical_anchor = MSO_ANCHOR.MIDDLE
        np = ntf.paragraphs[0]
        _center(np)
        _run(np, f"{i + 1:02d}", 16, NAVY, bold=True)
        _rect(s, Emu(x + Inches(0.7)), y, Emu(w - Inches(0.7)), Inches(0.6), BLUEROW)
        ttf = _box(s, Emu(x + Inches(1.0)), y, Emu(w - Inches(1.1)), Inches(0.6))
        ttf.vertical_anchor = MSO_ANCHOR.MIDDLE
        _run(ttf.paragraphs[0], sec, 16, WHITE, bold=True)


def introduction_slide(prs):
    s = _content(prs, "Introduction", 3)
    tf = _box(s, Inches(0.5), Inches(1.55), Inches(6.4), Inches(0.9))
    _run(tf.paragraphs[0], "AI now writes a third of new code — and trust hasn't caught up.", 19, INK, bold=True)
    # stat pills
    stats = [
        ("45%", "of AI code\nships a flaw", RED),
        ("+107%", "vulns / codebase\nin one year", RED),
        ("$10–50k", "/yr for tools\nmost can't afford", NAVY),
    ]
    x = Inches(0.5)
    for big, lab, col in stats:
        _rect(s, x, Inches(2.65), Inches(2.0), Inches(1.4), LIGHT, rounded=True)
        c = _box(s, x, Inches(2.78), Inches(2.0), Inches(1.2))
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        pp = c.paragraphs[0]
        _center(pp)
        _run(pp, big, 26, col, bold=True)
        p2 = c.add_paragraph()
        _center(p2)
        _run(p2, lab, 11, GRAY)
        x = Emu(x + Inches(2.15))
    # three pillars — full width, no screenshot
    pillars = [
        ("Detect", "19 engines · 3 languages · 12-stage async pipeline", NAVY),
        ("Prove", "Exploit-verified in a real Docker sandbox — binary ground truth", RED),
        ("Sign", "ECDSA-P256 + Dilithium3 — every scan is cryptographically attested", GREEN),
    ]
    x = Inches(0.5)
    for label, body, col in pillars:
        _rect(s, x, Inches(4.3), Inches(4.05), Inches(2.2), LIGHT, rounded=True)
        _rect(s, x, Inches(4.3), Inches(4.05), Inches(0.14), col)
        c = _box(s, x + Inches(0.25), Inches(4.55), Inches(3.6), Inches(1.8))
        _run(c.paragraphs[0], label, 20, col, bold=True)
        p = c.add_paragraph()
        p.space_before = Pt(6)
        _run(p, body, 13, INK)
        x = Emu(x + Inches(4.2))


def problem_slide(prs):
    s = _content(prs, "Problem Statement", 4)
    tf = _box(s, Inches(0.5), Inches(1.55), Inches(12.3), Inches(0.6))
    _run(tf.paragraphs[0], "Your scanner flags ~1,900 issues per scan. Which one breaches you?", 18, INK, bold=True)
    cards = [
        (
            "Quality variance",
            "Manual review is inconsistent — the SQL injection on line 47 slips through on the 50th PR of the day.",
            NAVY,
        ),
        ("Cost barrier", "Enterprise tools cost $10–50k/year — unaffordable for universities and most startups.", GOLD),
        (
            "Hallucination",
            "AI explainers invent confident, wrong advice. A developer gets burned once and never trusts the tool again.",
            RED,
        ),
    ]
    x = Inches(0.5)
    for head, body, col in cards:
        _rect(s, x, Inches(2.4), Inches(3.95), Inches(3.9), LIGHT, rounded=True)
        _rect(s, x, Inches(2.4), Inches(3.95), Inches(0.14), col)
        c = _box(s, x + Inches(0.25), Inches(2.7), Inches(3.45), Inches(3.4))
        _run(c.paragraphs[0], head, 18, col if col != GOLD else RGBColor(0xB8, 0x8A, 0x1E), bold=True)
        p = c.add_paragraph()
        p.space_before = Pt(8)
        _run(p, body, 13, INK)
        x = Emu(x + Inches(4.15))


def solution_slide(prs):
    s = _content(prs, "Solution — ACR-QA", 5)
    tf = _box(s, Inches(0.5), Inches(1.55), Inches(12.3), Inches(0.75))
    _run(tf.paragraphs[0], "A trust layer on top of your scanners — one question at merge time:", 20, INK, bold=True)
    p = tf.add_paragraph()
    p.space_before = Pt(2)
    _run(p, "Is this finding real enough to stop a release on its own?", 20, GREEN, bold=True)
    # three design pillars as cards
    pillars = [
        (
            "Confirmed Tier",
            "Four gates: HIGH severity + 22-rule set + production path + Bandit HIGH confidence.",
            "96.4% precision — safe to auto-block without human review.",
            NAVY,
        ),
        (
            "Exploit Verification",
            "Docker sandbox fires a real payload. Same payload must FAIL after the AI patch.",
            "Binary ground truth — not static re-analysis. 5/5 verified live.",
            RED,
        ),
        (
            "Cryptographic Attestation",
            "ECDSA-P256 + Dilithium3 (post-quantum) sign every scan as a tamper-evident bundle.",
            "EU CRA Sept 2026 compliance out of the box, at zero recurring cost.",
            GREEN,
        ),
    ]
    x = Inches(0.5)
    cw = Inches(4.05)
    for head, body, payoff, col in pillars:
        _rect(s, x, Inches(2.55), cw, Inches(4.0), LIGHT, rounded=True)
        _rect(s, x, Inches(2.55), cw, Inches(0.14), col)
        c = _box(s, x + Inches(0.22), Inches(2.85), Emu(cw - Inches(0.44)), Inches(3.5))
        _run(c.paragraphs[0], head, 17, col, bold=True)
        p = c.add_paragraph()
        p.space_before = Pt(7)
        _run(p, body, 12, INK)
        p2 = c.add_paragraph()
        p2.space_before = Pt(9)
        _run(p2, payoff, 11.5, col, bold=True)
        x = Emu(x + Inches(4.2))


def methodology_arch_slide(prs):
    s = _content(prs, "Methodology — System Architecture", 6)
    sub = _box(s, Inches(0.5), Inches(1.5), Inches(12.3), Inches(0.4))
    _run(
        sub.paragraphs[0],
        "19 engines · 3 language adapters · 12-stage async pipeline · 52-endpoint FastAPI",
        13,
        GOLD,
        italic=True,
    )
    _fit_image(s, FIGS / "arch_overview.png", Inches(0.6), Inches(1.95), Inches(12.1), Inches(4.6))


def methodology_exploit_slide(prs):
    s = _content(prs, "Methodology — Exploit Verification", 7)
    sub = _box(s, Inches(0.5), Inches(1.5), Inches(12.3), Inches(0.4))
    _run(
        sub.paragraphs[0],
        "We don't claim a vulnerability — we detonate it in a sandbox, then re-detonate the fix.",
        13,
        GOLD,
        italic=True,
    )
    phases = [
        ("1  DETECT", "Rule maps to an exploit category — SQLi, command injection, SSTI (13 categories).", NAVY),
        ("2  DETONATE", "Docker sandbox fires a real canary payload: ' OR 1=1 · {{7×7}}→49. Attack confirmed.", RED),
        ("3  PATCH", "AI generates a fix. The SAME payload fires again — it must now FAIL.", GREEN),
        ("4  SIGN", "vuln-proof + fix-diff + fix-proof signed as one ECDSA-P256 + Dilithium3 bundle.", NAVY),
    ]
    x = Inches(0.5)
    bw = Inches(2.95)
    for label, body, col in phases:
        _rect(s, x, Inches(2.2), bw, Inches(3.7), LIGHT, rounded=True)
        _rect(s, x, Inches(2.2), bw, Inches(0.6), col)
        h = _box(s, x, Inches(2.28), bw, Inches(0.5))
        h.vertical_anchor = MSO_ANCHOR.MIDDLE
        hp = h.paragraphs[0]
        _center(hp)
        _run(hp, label, 15, WHITE, bold=True)
        b = _box(s, x + Inches(0.18), Inches(3.0), Emu(bw - Inches(0.36)), Inches(2.8))
        _run(b.paragraphs[0], body, 13, INK)
        x = Emu(x + Inches(3.07))
    foot = _box(s, Inches(0.5), Inches(6.1), Inches(12.3), Inches(0.5))
    _run(
        foot.paragraphs[0],
        "Verified live: 5/5 exploit tests — SQLi & SSTI fire; safe code is proven UN-exploitable.",
        13,
        GREEN,
        bold=True,
        italic=True,
    )


def funnel_slide(prs):
    s = _content(prs, "Results — The Precision Funnel", 8)
    sub = _box(s, Inches(0.5), Inches(1.5), Inches(12.3), Inches(0.4))
    _run(
        sub.paragraphs[0],
        "30-repo adversarial corpus · 1,942 raw findings → 55 Confirmed Tier @ 96.4% precision",
        13,
        GOLD,
        italic=True,
    )
    _fit_image(s, FIGS / "FUNNEL_SLIDE.png", Inches(0.6), Inches(1.95), Inches(12.1), Inches(4.7))


def results_slide(prs):
    s = _content(prs, "Results & Evaluation", 9)
    rows = [
        ("Confirmed-Tier precision (auto-block)", "96.4%  (95% CI 90.9–100%)"),
        ("CVE recall (pre-registered battery)", "100% — 8 / 8 detectable"),
        ("Head-to-head F₁", "98.2%  vs Semgrep 45.7%"),
        ("RealVuln 2026 leaderboard", "25.1% — beats Semgrep, Snyk, SonarQube"),
        ("OWASP Top 10 coverage", "9 / 10 categories"),
        ("Test suite / CORE coverage", "3,247 tests · 88%"),
    ]
    tbl = s.shapes.add_table(len(rows) + 1, 2, Inches(0.5), Inches(1.7), Inches(7.2), Inches(4.6)).table
    tbl.columns[0].width = Inches(4.3)
    tbl.columns[1].width = Inches(2.9)
    for c, h in enumerate(["What we measured", "Result"]):
        cell = tbl.cell(0, c)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        r = cell.text_frame.paragraphs[0].runs[0]
        r.font.color.rgb = WHITE
        r.font.bold = True
        r.font.size = Pt(12)
    for i, (a, b) in enumerate(rows, 1):
        for c, val in enumerate((a, b)):
            cell = tbl.cell(i, c)
            cell.text = val
            r = cell.text_frame.paragraphs[0].runs[0]
            r.font.size = Pt(11)
            r.font.color.rgb = GREEN if c == 1 else INK
            r.font.bold = c == 1
    # RealVuln chart on the right
    _fit_image(s, FIGS / "REALVULN_LEADERBOARD.png", Inches(8.0), Inches(1.7), Inches(5.0), Inches(3.4))
    foot = _box(s, Inches(8.0), Inches(5.3), Inches(5.0), Inches(1.2))
    _run(
        foot.paragraphs[0],
        "Live demo: payments-api → 64 findings → toggle Confirmed Tier → 4 remain. "
        "The funnel, on real data, in front of you.",
        12,
        NAVY,
        italic=True,
    )


def _persona_card(s, x, y, w, h, head, body, payoff, col):
    _rect(s, x, y, w, h, LIGHT, rounded=True)
    _rect(s, x, y, w, Inches(0.14), col)
    c = _box(s, x + Inches(0.28), Emu(y + Inches(0.28)), Emu(w - Inches(0.56)), Emu(h - Inches(0.5)))
    _run(c.paragraphs[0], head, 18, col if col != GOLD else RGBColor(0xB8, 0x8A, 0x1E), bold=True)
    p = c.add_paragraph()
    p.space_before = Pt(8)
    _run(p, body, 13, INK)
    p2 = c.add_paragraph()
    p2.space_before = Pt(10)
    _run(p2, payoff, 12.5, col if col != GOLD else RGBColor(0xB8, 0x8A, 0x1E), bold=True)


def use_cases_1_slide(prs):
    s = _content(prs, "Use Cases — Education & Startups", 10)
    _persona_card(
        s,
        Inches(0.5),
        Inches(1.7),
        Inches(6.0),
        Inches(4.6),
        "The University Instructor",
        "Grades hundreds of student repos a term. Enterprise scanners cost $10–50k — out of reach. "
        "Needs to catch the real SQL injection without drowning in style noise.",
        "→ Free & self-hosted · Confirmed Tier surfaces the real bug · RAG explanation teaches the learner.",
        NAVY,
    )
    _persona_card(
        s,
        Inches(6.8),
        Inches(1.7),
        Inches(6.0),
        Inches(4.6),
        "The Startup / CI Tech Lead",
        "Ships dozens of AI-written PRs a day. Needs an auto-block at merge that won't cry wolf, "
        "and a signed audit trail for compliance (EU CRA, Sept 2026).",
        "→ 96.4% Confirmed-Tier auto-block · ECDSA + PQ attestation = the audit trail · $0 recurring.",
        GREEN,
    )


def use_cases_2_slide(prs):
    s = _content(prs, "Use Cases — Open Source & Enterprise", 11)
    _persona_card(
        s,
        Inches(0.5),
        Inches(1.7),
        Inches(6.0),
        Inches(4.6),
        "The Open-Source Maintainer",
        "Reviews drive-by PRs from strangers with no time and no budget. Can't tell a real fix "
        "from a subtle supply-chain attack.",
        "→ Exploit-verified findings + signed provenance — trust a contribution without trusting the contributor.",
        GOLD,
    )
    _persona_card(
        s,
        Inches(6.8),
        Inches(1.7),
        Inches(6.0),
        Inches(4.6),
        "The Enterprise Security Auditor",
        "Must prove to regulators what was scanned, when, and what was found — months later, " "tamper-free.",
        "→ Every scan ECDSA + Dilithium3 signed · verify in one command · EU CRA-ready provenance.",
        NAVY,
    )


def conclusion_slide(prs):
    s = _content(prs, "Conclusion", 13)
    tf = _box(s, Inches(0.5), Inches(1.6), Inches(7.0), Inches(0.9))
    _run(tf.paragraphs[0], "The open, attested, $0 quadrant the market leaves empty.", 19, INK, bold=True)
    lines = [
        ("Trust", "96.4% Confirmed-Tier precision — high enough to auto-block a merge."),
        ("Proof", "Exploit-verified in a sandbox + cryptographically signed — not guesses."),
        ("Reach", "19 engines · Python / JS / Go · 9/10 OWASP · 100% CVE recall."),
        ("Price", "Self-hosted, your data never leaves, $0 recurring — vs $10–50k/year."),
    ]
    y = Inches(2.7)
    for k, v in lines:
        _rect(s, Inches(0.6), y, Inches(1.5), Inches(0.6), GOLD, rounded=True)
        kt = _box(s, Inches(0.6), y, Inches(1.5), Inches(0.6))
        kt.vertical_anchor = MSO_ANCHOR.MIDDLE
        kp = kt.paragraphs[0]
        _center(kp)
        _run(kp, k, 15, NAVY, bold=True)
        vt = _box(s, Inches(2.3), y, Inches(5.0), Inches(0.6))
        vt.vertical_anchor = MSO_ANCHOR.MIDDLE
        _run(vt.paragraphs[0], v, 12.5, INK)
        y = Emu(y + Inches(0.82))
    _fit_image(s, PHOTOS / "Gemini_6.png", Inches(7.7), Inches(2.0), Inches(5.3), Inches(4.2))


def future_work_slide(prs):
    s = _content(prs, "Future Work", 12)
    items = [
        (
            "Inter-procedural taint analysis",
            "Trace tainted data across files and functions — worth an estimated +10–15pp recall.",
        ),
        ("More languages", "Extend adapters beyond Python / JS / Go to Java, C#, and Rust."),
        ("Managed / hosted offering", "A one-click GitHub App so teams adopt the trust layer without self-hosting."),
        (
            "Independent expert labelling",
            "A multi-annotator ground-truth study to harden the precision numbers further.",
        ),
    ]
    y = Inches(1.8)
    for head, body in items:
        _rect(s, Inches(0.5), y, Inches(12.3), Inches(1.05), LIGHT, rounded=True)
        _rect(s, Inches(0.5), y, Inches(0.14), Inches(1.05), GOLD)
        c = _box(s, Inches(0.85), Emu(y + Inches(0.12)), Inches(11.6), Inches(0.85))
        _run(c.paragraphs[0], head, 16, NAVY, bold=True)
        p = c.add_paragraph()
        _run(p, body, 13, INK)
        y = Emu(y + Inches(1.22))


def section_closer(prs, big, small, photo=None):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s, NAVY)
    if photo:
        _hero(s, photo, alpha=70)
    _rect(s, 0, Inches(6.95), EMU_W, Inches(0.55), GOLD)
    if LOGO.exists():
        s.shapes.add_picture(str(LOGO), Inches(6.17), Inches(1.4), height=Inches(1.3))
    tf = _box(s, Inches(0.8), Inches(3.1), Inches(11.7), Inches(2.2))
    _center(tf.paragraphs[0])
    _run(tf.paragraphs[0], big, 48, WHITE, bold=True)
    if small:
        p = tf.add_paragraph()
        _center(p)
        _run(p, small, 18, GOLD)


def build():
    prs = Presentation()
    prs.slide_width, prs.slide_height = EMU_W, EMU_H

    title_slide(prs)  # 1
    outline_slide(prs)  # 2
    introduction_slide(prs)  # 3
    problem_slide(prs)  # 4
    solution_slide(prs)  # 5
    methodology_arch_slide(prs)  # 6
    methodology_exploit_slide(prs)  # 7
    funnel_slide(prs)  # 8
    results_slide(prs)  # 9
    use_cases_1_slide(prs)  # 10
    use_cases_2_slide(prs)  # 11
    future_work_slide(prs)  # 12
    conclusion_slide(prs)  # 13
    future_work_slide(prs)  # 13
    section_closer(prs, "Any Questions?", "Happy to go deeper on any number, any slide.")  # 14
    section_closer(
        prs, "Thank You", "Ahmed Mahmoud Abbas · Supervisor: Dr. Samy Abdel Nabi", photo="Gemini_2.png"
    )  # 15

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUT)
    print(f"✓ Template deck written: {OUT}  ({len(prs.slides._sldIdLst)} slides)")


if __name__ == "__main__":
    build()
