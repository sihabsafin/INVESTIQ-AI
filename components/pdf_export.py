"""
InvestIQ AI — PDF Export Component
Generates a branded, multi-page investment report using ReportLab.
"""

import io
from datetime import datetime
import streamlit as st

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table,
        TableStyle, HRFlowable, PageBreak,
    )
    from reportlab.pdfgen import canvas
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False


# ── BRAND COLORS (RGB 0-1) ────────────────────────────────────────────────────

_NAVY       = colors.HexColor("#0B1F3A")
_DARK_CARD  = colors.HexColor("#0D1B2E")
_CYAN       = colors.HexColor("#00D4FF")
_VIOLET     = colors.HexColor("#6C63FF")
_MINT       = colors.HexColor("#00FFB3")
_AMBER      = colors.HexColor("#F59E0B")
_RED        = colors.HexColor("#FF4560")
_MUTED      = colors.HexColor("#7B92B2")
_TEXT       = colors.HexColor("#1A2A3A")
_WHITE      = colors.white
_LIGHT_BG   = colors.HexColor("#F4F8FC")
_BORDER     = colors.HexColor("#D0DCE8")


def _score_color(score: float, max_val: int = 10) -> object:
    pct = (score / max_val) * 100
    if pct >= 70:
        return _MINT
    elif pct >= 45:
        return _AMBER
    else:
        return _RED


def _rec_color(recommendation: str) -> object:
    rec = recommendation.lower()
    if "invest" in rec:
        return _MINT
    elif "consider" in rec:
        return _AMBER
    else:
        return _RED


# ── PAGE TEMPLATE ─────────────────────────────────────────────────────────────

class _PageTemplate:
    """Adds header/footer to every page."""

    def __init__(self, startup_name: str, date_str: str):
        self.startup_name = startup_name
        self.date_str = date_str

    def __call__(self, canvas_obj, doc):
        canvas_obj.saveState()
        w, h = A4

        # ── Top bar ───────────────────────────────────────────────────────────
        canvas_obj.setFillColor(_NAVY)
        canvas_obj.rect(0, h - 18*mm, w, 18*mm, fill=1, stroke=0)

        # Logo text
        canvas_obj.setFillColor(_WHITE)
        canvas_obj.setFont("Helvetica-Bold", 12)
        canvas_obj.drawString(15*mm, h - 11*mm, "InvestIQ AI")

        canvas_obj.setFillColor(_CYAN)
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.drawString(52*mm, h - 11*mm, "Investment Intelligence Platform")

        # Startup name on right
        canvas_obj.setFillColor(_MUTED)
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.drawRightString(w - 15*mm, h - 11*mm, self.startup_name)

        # ── Bottom bar ────────────────────────────────────────────────────────
        canvas_obj.setFillColor(_NAVY)
        canvas_obj.rect(0, 0, w, 12*mm, fill=1, stroke=0)

        canvas_obj.setFillColor(_MUTED)
        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.drawString(
            15*mm, 4.5*mm,
            f"Generated {self.date_str}  |  Powered by Groq · Gemini  |  investiq.ai"
        )

        # Page number
        canvas_obj.setFillColor(_MUTED)
        canvas_obj.drawRightString(w - 15*mm, 4.5*mm, f"Page {doc.page}")

        canvas_obj.restoreState()


# ── STYLES ─────────────────────────────────────────────────────────────────────

def _make_styles():
    base = getSampleStyleSheet()

    return {
        "section_heading": ParagraphStyle(
            "SectionHeading",
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=_NAVY,
            spaceAfter=6,
            spaceBefore=16,
        ),
        "label": ParagraphStyle(
            "Label",
            fontName="Helvetica-Bold",
            fontSize=7,
            textColor=_MUTED,
            spaceAfter=2,
            letterSpacing=1.5,
        ),
        "body": ParagraphStyle(
            "Body",
            fontName="Helvetica",
            fontSize=9.5,
            textColor=_TEXT,
            leading=15,
            spaceAfter=6,
        ),
        "verdict": ParagraphStyle(
            "Verdict",
            fontName="Helvetica-Oblique",
            fontSize=10,
            textColor=colors.HexColor("#2A4A6A"),
            leading=16,
            leftIndent=12,
            borderPad=6,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            fontName="Helvetica",
            fontSize=9,
            textColor=_TEXT,
            leading=14,
            leftIndent=14,
            bulletIndent=4,
            spaceAfter=3,
        ),
        "small_label": ParagraphStyle(
            "SmallLabel",
            fontName="Helvetica-Bold",
            fontSize=7,
            textColor=_MUTED,
            letterSpacing=1.2,
        ),
        "small_value": ParagraphStyle(
            "SmallValue",
            fontName="Helvetica",
            fontSize=9,
            textColor=_TEXT,
            leading=13,
        ),
        "disclaimer": ParagraphStyle(
            "Disclaimer",
            fontName="Helvetica-Oblique",
            fontSize=8,
            textColor=_MUTED,
            leading=12,
        ),
    }


# ── BUILDER ───────────────────────────────────────────────────────────────────

def generate_pdf(result: dict) -> bytes:
    """
    Generate a multi-page branded PDF report.

    Args:
        result: Assembled final result dict from pipeline.assemble_final_result()

    Returns:
        PDF as bytes (ready for st.download_button).
    """
    if not REPORTLAB_OK:
        raise ImportError("reportlab is not installed. Run: pip install reportlab")

    buffer = io.BytesIO()
    styles = _make_styles()
    now = datetime.now()
    date_str = now.strftime("%B %d, %Y  %H:%M UTC")
    startup_name = result.get("startup_name", "Unknown Startup")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18*mm,
        rightMargin=18*mm,
        topMargin=24*mm,
        bottomMargin=20*mm,
        title=f"InvestIQ AI — {startup_name}",
        author="InvestIQ AI",
    )

    page_cb = _PageTemplate(startup_name, date_str)
    story = []

    # ────────────────────────────────────────────────────────────────────────
    # PAGE 1 — COVER
    # ────────────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 20*mm))

    # Report type label
    story.append(Paragraph(
        "INVESTMENT INTELLIGENCE REPORT",
        ParagraphStyle("Cover1", fontName="Helvetica-Bold", fontSize=8,
                       textColor=_CYAN, letterSpacing=2.5, alignment=TA_CENTER)
    ))
    story.append(Spacer(1, 4*mm))

    # Startup name
    story.append(Paragraph(
        startup_name,
        ParagraphStyle("CoverTitle", fontName="Helvetica-Bold", fontSize=30,
                       textColor=_NAVY, alignment=TA_CENTER, leading=36)
    ))
    story.append(Spacer(1, 3*mm))

    # Industry + stage
    industry = result.get("industry", "")
    stage = result.get("funding_stage", "")
    if industry or stage:
        subtitle = "  ·  ".join(filter(None, [industry, stage]))
        story.append(Paragraph(
            subtitle,
            ParagraphStyle("CoverSub", fontName="Helvetica", fontSize=11,
                           textColor=_MUTED, alignment=TA_CENTER)
        ))

    story.append(Spacer(1, 10*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=_BORDER))
    story.append(Spacer(1, 8*mm))

    # Big score
    overall = result.get("overall_investment_score", 0)
    rec = result.get("final_recommendation", "Consider")
    conf = result.get("confidence_level", "Medium")
    rec_col = _rec_color(rec)

    story.append(Paragraph(
        "OVERALL INVESTMENT SCORE",
        ParagraphStyle("ScoreLabel", fontName="Helvetica-Bold", fontSize=8,
                       textColor=_MUTED, letterSpacing=2, alignment=TA_CENTER)
    ))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        f"{overall}",
        ParagraphStyle("BigScore", fontName="Helvetica-Bold", fontSize=64,
                       textColor=_NAVY, alignment=TA_CENTER, leading=70)
    ))
    story.append(Paragraph(
        "out of 100",
        ParagraphStyle("OutOf", fontName="Helvetica", fontSize=10,
                       textColor=_MUTED, alignment=TA_CENTER)
    ))
    story.append(Spacer(1, 6*mm))

    # Recommendation + confidence row
    cover_table = Table(
        [[
            Paragraph(rec.upper(), ParagraphStyle(
                "RecPill", fontName="Helvetica-Bold", fontSize=12,
                textColor=rec_col, alignment=TA_CENTER
            )),
            Paragraph(f"{conf.upper()} CONFIDENCE", ParagraphStyle(
                "ConfPill", fontName="Helvetica-Bold", fontSize=10,
                textColor=_CYAN, alignment=TA_CENTER
            )),
        ]],
        colWidths=["50%", "50%"],
    )
    cover_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINERIGHT", (0, 0), (0, 0), 1, _BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(cover_table)

    story.append(Spacer(1, 6*mm))

    # Verdict
    verdict = result.get("one_line_verdict", "")
    if verdict:
        story.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER))
        story.append(Spacer(1, 4*mm))
        story.append(Paragraph(f'"{verdict}"', styles["verdict"]))

    story.append(Spacer(1, 8*mm))

    # Date
    story.append(Paragraph(
        date_str,
        ParagraphStyle("Date", fontName="Helvetica", fontSize=8,
                       textColor=_MUTED, alignment=TA_CENTER)
    ))

    story.append(PageBreak())

    # ────────────────────────────────────────────────────────────────────────
    # PAGE 2 — EXECUTIVE SUMMARY
    # ────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("Executive Summary", styles["section_heading"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER))
    story.append(Spacer(1, 4*mm))

    reasoning = result.get("decision_reasoning", "")
    if reasoning:
        story.append(Paragraph(reasoning, styles["body"]))
    story.append(Spacer(1, 6*mm))

    # Startup details table
    details = [
        ["STARTUP", result.get("startup_name", "")],
        ["INDUSTRY", result.get("industry", "")],
        ["TARGET MARKET", result.get("target_market", "")],
        ["BUSINESS MODEL", result.get("business_model", "")],
        ["REVENUE MODEL", result.get("revenue_model", "")],
        ["FUNDING STAGE", result.get("funding_stage", "")],
        ["DESCRIPTION", result.get("description", "")],
    ]
    detail_table_data = []
    for label, value in details:
        if value:
            detail_table_data.append([
                Paragraph(label, styles["small_label"]),
                Paragraph(str(value), styles["small_value"]),
            ])

    if detail_table_data:
        dt = Table(detail_table_data, colWidths=[40*mm, None])
        dt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), _LIGHT_BG),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [_LIGHT_BG, _WHITE]),
        ]))
        story.append(dt)

    story.append(PageBreak())

    # ────────────────────────────────────────────────────────────────────────
    # PAGE 3 — SCORE BREAKDOWN
    # ────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("Score Breakdown", styles["section_heading"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER))
    story.append(Spacer(1, 4*mm))

    score_rows = [
        ["Dimension", "Score", "Key Insight"],
        ["Market Intelligence",
         f"{result.get('market_score', 5)}/10",
         result.get("market_key_insight", "")],
        ["Competitive Landscape",
         f"{result.get('competition_score', 5)}/10",
         result.get("competition_key_insight", "")],
        ["Financial Viability",
         f"{result.get('financial_score', 5)}/10",
         result.get("financial_key_insight", "")],
        ["Risk Assessment",
         f"{result.get('risk_score', 5)}/10",
         result.get("risk_key_insight", "")],
        ["Innovation Scout",
         f"{result.get('innovation_score', 5)}/10",
         result.get("innovation_key_insight", "")],
        ["OVERALL SCORE",
         f"{overall}/100",
         result.get("final_recommendation", "")],
    ]

    score_table_data = []
    for i, row in enumerate(score_rows):
        is_header = i == 0
        is_overall = i == len(score_rows) - 1
        score_text = row[1]

        # Parse score value for coloring
        try:
            raw = float(score_text.split("/")[0])
            denom = float(score_text.split("/")[1])
            col = _score_color(raw, int(denom))
        except Exception:
            col = _TEXT

        if is_header:
            row_data = [
                Paragraph(c, ParagraphStyle("H", fontName="Helvetica-Bold",
                           fontSize=8, textColor=_MUTED, letterSpacing=1.2))
                for c in row
            ]
        elif is_overall:
            row_data = [
                Paragraph(row[0], ParagraphStyle("OL", fontName="Helvetica-Bold",
                           fontSize=10, textColor=_NAVY)),
                Paragraph(row[1], ParagraphStyle("OS", fontName="Helvetica-Bold",
                           fontSize=12, textColor=col)),
                Paragraph(row[2], ParagraphStyle("OV", fontName="Helvetica-Bold",
                           fontSize=9, textColor=col)),
            ]
        else:
            row_data = [
                Paragraph(row[0], styles["body"]),
                Paragraph(row[1], ParagraphStyle("SC", fontName="Helvetica-Bold",
                           fontSize=11, textColor=col)),
                Paragraph(row[2], styles["body"]),
            ]
        score_table_data.append(row_data)

    st_tbl = Table(score_table_data, colWidths=[50*mm, 22*mm, None])
    st_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), _WHITE),
        ("BACKGROUND", (0, -1), (-1, -1), _LIGHT_BG),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [_WHITE, _LIGHT_BG]),
        ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(st_tbl)
    story.append(PageBreak())

    # ────────────────────────────────────────────────────────────────────────
    # PAGE 4 — DETAILED AGENT ANALYSES
    # ────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("Detailed Agent Analyses", styles["section_heading"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER))
    story.append(Spacer(1, 3*mm))

    agent_sections = [
        ("🔍 Market Intelligence",   "market_analysis"),
        ("⚔️ Competitive Landscape", "competition_analysis"),
        ("💰 Financial Viability",   "financial_analysis"),
        ("⚠️ Risk Assessment",       "risk_analysis"),
        ("💡 Innovation Scout",      "innovation_analysis"),
    ]

    for title, key in agent_sections:
        analysis = result.get(key, "")
        if analysis:
            story.append(Paragraph(title, ParagraphStyle(
                "AgentTitle", fontName="Helvetica-Bold", fontSize=10,
                textColor=_NAVY, spaceBefore=8, spaceAfter=3,
            )))
            story.append(Paragraph(analysis, styles["body"]))

    story.append(PageBreak())

    # ────────────────────────────────────────────────────────────────────────
    # PAGE 5 — DECISION SUMMARY
    # ────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("Decision Summary", styles["section_heading"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER))
    story.append(Spacer(1, 4*mm))

    # Strengths
    strengths = result.get("strengths", [])
    if strengths:
        story.append(Paragraph("STRENGTHS", ParagraphStyle(
            "SW", fontName="Helvetica-Bold", fontSize=8,
            textColor=_MINT, letterSpacing=1.5, spaceAfter=4,
        )))
        for s in strengths:
            if s:
                story.append(Paragraph(f"▸  {s}", styles["bullet"]))
        story.append(Spacer(1, 4*mm))

    # Weaknesses
    weaknesses = result.get("weaknesses", [])
    if weaknesses:
        story.append(Paragraph("WEAKNESSES", ParagraphStyle(
            "WW", fontName="Helvetica-Bold", fontSize=8,
            textColor=_RED, letterSpacing=1.5, spaceAfter=4,
        )))
        for w in weaknesses:
            if w:
                story.append(Paragraph(f"▸  {w}", styles["bullet"]))
        story.append(Spacer(1, 4*mm))

    # Actions
    actions = result.get("recommended_actions", [])
    if actions:
        story.append(Paragraph("RECOMMENDED ACTIONS", ParagraphStyle(
            "RA", fontName="Helvetica-Bold", fontSize=8,
            textColor=_VIOLET, letterSpacing=1.5, spaceAfter=4,
        )))
        for i, a in enumerate(actions, 1):
            if a:
                story.append(Paragraph(f"{i}.  {a}", styles["bullet"]))

    story.append(PageBreak())

    # ────────────────────────────────────────────────────────────────────────
    # PAGE 6 — DISCLAIMER
    # ────────────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 20*mm))
    story.append(Paragraph("Disclaimer", styles["section_heading"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "This report has been generated by InvestIQ AI, an automated multi-agent artificial intelligence system. "
        "The analysis, scores, and recommendations contained herein are produced by large language models "
        "(Groq Llama 3.3 70B, DeepSeek-R1, and Google Gemini 2.5 Flash) and are intended for informational "
        "and research purposes only. "
        "This report does NOT constitute financial, investment, legal, or professional advice of any kind. "
        "Past performance of any referenced markets or business models is not indicative of future results. "
        "All investment decisions should be made in consultation with qualified financial and legal professionals "
        "who have access to complete, verified information about the company in question. "
        "AI-generated analysis may contain errors, omissions, or outdated information. "
        "InvestIQ AI and its operators accept no liability for decisions made based on this report.",
        styles["disclaimer"],
    ))

    # Build PDF
    doc.build(story, onFirstPage=page_cb, onLaterPages=page_cb)
    return buffer.getvalue()


# ── STREAMLIT DOWNLOAD BUTTON ──────────────────────────────────────────────────

def render_pdf_download_button(result: dict) -> None:
    """
    Render the PDF export button in Streamlit.
    On click, generates and offers PDF for download.
    """
    if not REPORTLAB_OK:
        st.warning("PDF export requires `reportlab`. Add it to requirements.txt.")
        return

    startup_name = result.get("startup_name", "analysis")
    date_slug = datetime.now().strftime("%Y%m%d")
    filename = f"InvestIQ_{startup_name.replace(' ', '_')}_{date_slug}.pdf"

    try:
        pdf_bytes = generate_pdf(result)
        st.download_button(
            label="📄 Export PDF Report",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True,
        )
    except Exception as e:
        st.error(f"PDF generation failed: {e}")