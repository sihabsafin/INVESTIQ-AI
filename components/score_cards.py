"""
InvestIQ AI — Score Cards Component
Four individual agent score cards + executive summary card + strengths/weaknesses panels.
"""

import streamlit as st
from components.gauge import get_score_color


# ── HELPER ────────────────────────────────────────────────────────────────────

def _score_to_label(score: float, max_val: int = 10) -> str:
    pct = (score / max_val) * 100
    if pct >= 80:
        return "Excellent"
    elif pct >= 65:
        return "Strong"
    elif pct >= 50:
        return "Moderate"
    elif pct >= 35:
        return "Weak"
    else:
        return "Poor"


def _risk_score_label(score: float) -> str:
    """Risk score is inverted: 10 = low risk."""
    if score >= 8:
        return "Low Risk"
    elif score >= 6:
        return "Moderate"
    elif score >= 4:
        return "High Risk"
    else:
        return "Critical"


# ── FOUR MAIN SCORE CARDS ─────────────────────────────────────────────────────

def render_four_score_cards(result: dict) -> None:
    """
    Render the 4-column row of agent score cards:
    Market | Competition | Financial | Risk

    Args:
        result: Assembled final result dict.
    """
    col1, col2, col3, col4 = st.columns(4)

    cards = [
        {
            "col": col1,
            "icon": "🔍",
            "label": "MARKET",
            "score": result.get("market_score", 5),
            "sublabel": result.get("market_size_signal", ""),
            "insight": result.get("market_key_insight", ""),
            "accent": "#00D4FF",
        },
        {
            "col": col2,
            "icon": "⚔️",
            "label": "COMPETITION",
            "score": result.get("competition_score", 5),
            "sublabel": result.get("moat_assessment", ""),
            "insight": result.get("competition_key_insight", ""),
            "accent": "#6C63FF",
        },
        {
            "col": col3,
            "icon": "💰",
            "label": "FINANCIAL",
            "score": result.get("financial_score", 5),
            "sublabel": result.get("revenue_model_quality", ""),
            "insight": result.get("financial_key_insight", ""),
            "accent": "#00FFB3",
        },
        {
            "col": col4,
            "icon": "⚠️",
            "label": "RISK",
            "score": result.get("risk_score", 5),
            "sublabel": _risk_score_label(result.get("risk_score", 5)),
            "insight": result.get("risk_key_insight", ""),
            "accent": "#F59E0B",
        },
    ]

    for card in cards:
        score = card["score"]
        color = get_score_color((score / 10) * 100)
        label_text = (
            _risk_score_label(score)
            if card["label"] == "RISK"
            else _score_to_label(score)
        )
        sublabel = card.get("sublabel", "") or label_text

        with card["col"]:
            st.markdown(f"""
            <div class="score-card" style="--accent:{card['accent']}">
                <div style="font-size:1.4rem; margin-bottom:0.3rem;">{card['icon']}</div>
                <div class="score-label">{card['label']}</div>
                <div class="score-number" style="color:{color};">
                    {score}<span style="font-size:1.2rem; color:#3A4F6A;">/10</span>
                </div>
                <div style="
                    display:inline-block;
                    background:rgba(255,255,255,0.04);
                    border:1px solid #1A2F4A;
                    border-radius:4px;
                    padding:0.15rem 0.5rem;
                    font-size:0.68rem;
                    color:#7B92B2;
                    text-transform:uppercase;
                    letter-spacing:0.08em;
                    margin-top:0.3rem;
                ">{sublabel}</div>
            </div>
            """, unsafe_allow_html=True)


def render_innovation_card(result: dict) -> None:
    """
    Render the Innovation score card (5th dimension, standalone).
    """
    score = result.get("innovation_score", 5)
    color = get_score_color((score / 10) * 100)
    innovation_type = result.get("innovation_type", "")
    insight = result.get("innovation_key_insight", "")

    st.markdown(f"""
    <div class="score-card" style="--accent:#B45FFF;">
        <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.5rem;">
            <span style="font-size:1.3rem;">💡</span>
            <span class="score-label">INNOVATION</span>
        </div>
        <div style="display:flex; align-items:baseline; gap:0.4rem; margin-bottom:0.4rem;">
            <span class="score-number" style="color:{color};">{score}</span>
            <span style="color:#3A4F6A; font-size:1rem;">/10</span>
        </div>
        {f'<div style="font-size:0.72rem; color:#7B92B2; margin-bottom:0.3rem;">{innovation_type}</div>' if innovation_type else ''}
        {f'<div style="font-size:0.78rem; color:#7B92B2; font-style:italic; line-height:1.4;">{insight}</div>' if insight else ''}
    </div>
    """, unsafe_allow_html=True)


# ── EXECUTIVE SUMMARY CARD ────────────────────────────────────────────────────

def render_executive_summary(result: dict) -> None:
    """
    Render the full-width executive summary / decision reasoning card.
    """
    reasoning = result.get("decision_reasoning", "")
    if not reasoning:
        return

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #0D1B2E 0%, #102035 100%);
        border: 1px solid #1A2F4A;
        border-left: 3px solid #00D4FF;
        border-radius: 12px;
        padding: 1.5rem 1.8rem;
        margin: 0.5rem 0;
    ">
        <div style="
            font-size:0.65rem;
            color:#00D4FF;
            text-transform:uppercase;
            letter-spacing:0.15em;
            font-weight:700;
            margin-bottom:0.8rem;
        ">🏛️ INVESTMENT COMMITTEE DECISION</div>
        <div style="
            font-size:0.95rem;
            color:#C8D8E8;
            line-height:1.75;
            font-weight:400;
        ">{reasoning}</div>
    </div>
    """, unsafe_allow_html=True)


# ── STRENGTHS & WEAKNESSES ────────────────────────────────────────────────────

def render_strengths_weaknesses(result: dict) -> None:
    """
    Render strengths and weaknesses in a two-column layout.
    """
    strengths = result.get("strengths", [])
    weaknesses = result.get("weaknesses", [])

    col_s, col_w = st.columns(2)

    with col_s:
        st.markdown("""
        <div style="
            background:#0D1B2E;
            border:1px solid rgba(0,255,179,0.25);
            border-top:2px solid #00FFB3;
            border-radius:12px;
            padding:1.2rem 1.4rem;
        ">
            <div style="
                font-size:0.65rem;
                color:#00FFB3;
                text-transform:uppercase;
                letter-spacing:0.15em;
                font-weight:700;
                margin-bottom:1rem;
            ">✅ STRENGTHS</div>
        """, unsafe_allow_html=True)

        for s in strengths:
            if s:
                st.markdown(f"""
                <div style="
                    display:flex;
                    gap:0.6rem;
                    margin-bottom:0.7rem;
                    align-items:flex-start;
                ">
                    <span style="color:#00FFB3; font-size:0.85rem; margin-top:0.05rem;">▸</span>
                    <span style="font-size:0.85rem; color:#C8D8E8; line-height:1.5;">{s}</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with col_w:
        st.markdown("""
        <div style="
            background:#0D1B2E;
            border:1px solid rgba(255,69,96,0.25);
            border-top:2px solid #FF4560;
            border-radius:12px;
            padding:1.2rem 1.4rem;
        ">
            <div style="
                font-size:0.65rem;
                color:#FF4560;
                text-transform:uppercase;
                letter-spacing:0.15em;
                font-weight:700;
                margin-bottom:1rem;
            ">❌ WEAKNESSES</div>
        """, unsafe_allow_html=True)

        for w in weaknesses:
            if w:
                st.markdown(f"""
                <div style="
                    display:flex;
                    gap:0.6rem;
                    margin-bottom:0.7rem;
                    align-items:flex-start;
                ">
                    <span style="color:#FF4560; font-size:0.85rem; margin-top:0.05rem;">▸</span>
                    <span style="font-size:0.85rem; color:#C8D8E8; line-height:1.5;">{w}</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


# ── RECOMMENDED ACTIONS ───────────────────────────────────────────────────────

def render_recommended_actions(result: dict) -> None:
    """Render recommended actions as numbered cards."""
    actions = result.get("recommended_actions", [])
    if not actions:
        return

    st.markdown("""
    <div style="
        font-size:0.65rem;
        color:#6C63FF;
        text-transform:uppercase;
        letter-spacing:0.15em;
        font-weight:700;
        margin-bottom:0.8rem;
    ">📋 RECOMMENDED ACTIONS</div>
    """, unsafe_allow_html=True)

    for i, action in enumerate(actions, 1):
        if action:
            st.markdown(f"""
            <div style="
                background:#0D1B2E;
                border:1px solid #1A2F4A;
                border-left:3px solid #6C63FF;
                border-radius:8px;
                padding:0.9rem 1.2rem;
                margin-bottom:0.5rem;
                display:flex;
                gap:0.8rem;
                align-items:flex-start;
            ">
                <span style="
                    background:rgba(108,99,255,0.15);
                    color:#6C63FF;
                    font-size:0.75rem;
                    font-weight:700;
                    width:1.6rem;
                    height:1.6rem;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    border-radius:50%;
                    flex-shrink:0;
                    margin-top:0.05rem;
                ">{i}</span>
                <span style="font-size:0.87rem; color:#C8D8E8; line-height:1.5;">{action}</span>
            </div>
            """, unsafe_allow_html=True)


# ── AGENT DEEP DIVE ───────────────────────────────────────────────────────────

def render_agent_deep_dive(result: dict) -> None:
    """
    Render collapsible expander sections for each agent's full analysis.
    """
    agents = [
        {
            "icon": "🔍",
            "title": "Market Intelligence Analysis",
            "analysis": result.get("market_analysis", ""),
            "fields": [
                ("Market Size", result.get("market_size_signal", "")),
                ("Timing", result.get("timing_assessment", "")),
                ("Growth", result.get("market_growth", "")),
                ("Key Insight", result.get("market_key_insight", "")),
            ],
            "score": result.get("market_score", 5),
            "model": "llama-3.3-70b · Groq",
        },
        {
            "icon": "⚔️",
            "title": "Competitive Landscape Analysis",
            "analysis": result.get("competition_analysis", ""),
            "fields": [
                ("Intensity", result.get("competitive_intensity", "")),
                ("Moat", result.get("moat_assessment", "")),
                ("Big Tech Risk", result.get("big_tech_risk", "")),
                ("Key Insight", result.get("competition_key_insight", "")),
            ],
            "score": result.get("competition_score", 5),
            "model": "llama-3.3-70b · Groq",
        },
        {
            "icon": "💰",
            "title": "Financial Viability Analysis",
            "analysis": result.get("financial_analysis", ""),
            "fields": [
                ("Model Quality", result.get("revenue_model_quality", "")),
                ("Scalability", result.get("scalability", "")),
                ("Margins", result.get("margin_potential", "")),
                ("Capital Efficiency", result.get("capital_efficiency", "")),
            ],
            "score": result.get("financial_score", 5),
            "model": "llama-3.3-70b · Groq",
        },
        {
            "icon": "⚠️",
            "title": "Risk Assessment",
            "analysis": result.get("risk_analysis", ""),
            "fields": [
                ("Risk Level", result.get("risk_level", "")),
                ("Execution Risk", result.get("execution_risk", "")),
                ("Regulatory Risk", result.get("regulatory_risk", "")),
                ("Primary Risk", result.get("primary_risk", "")),
            ],
            "score": result.get("risk_score", 5),
            "model": "deepseek-r1 · Groq",
        },
        {
            "icon": "💡",
            "title": "Innovation Scout Analysis",
            "analysis": result.get("innovation_analysis", ""),
            "fields": [
                ("Type", result.get("innovation_type", "")),
                ("Defensibility", result.get("defensibility", "")),
                ("Unfair Advantage", result.get("unfair_advantage_signal", "")),
                ("Key Insight", result.get("innovation_key_insight", "")),
            ],
            "score": result.get("innovation_score", 5),
            "model": "llama-3.3-70b · Groq",
        },
    ]

    from components.gauge import get_score_color

    for agent in agents:
        score = agent["score"]
        color = get_score_color((score / 10) * 100)

        with st.expander(
            f"{agent['icon']}  {agent['title']}  —  {score}/10",
            expanded=False
        ):
            # Model tag + analysis
            st.markdown(f"""
            <div style="
                font-size:0.65rem;
                color:#3A4F6A;
                text-transform:uppercase;
                letter-spacing:0.1em;
                margin-bottom:0.8rem;
            ">Model: {agent['model']}</div>
            <div style="
                font-size:0.9rem;
                color:#C8D8E8;
                line-height:1.7;
                margin-bottom:1rem;
                padding:1rem;
                background:rgba(0,0,0,0.2);
                border-radius:8px;
                border-left:2px solid {color};
            ">{agent['analysis']}</div>
            """, unsafe_allow_html=True)

            # Sub-fields grid
            fields = [(k, v) for k, v in agent["fields"] if v]
            if fields:
                cols = st.columns(min(len(fields), 2))
                for idx, (label, value) in enumerate(fields):
                    with cols[idx % 2]:
                        st.markdown(f"""
                        <div style="
                            background:#0D1B2E;
                            border:1px solid #1A2F4A;
                            border-radius:8px;
                            padding:0.7rem 0.9rem;
                            margin-bottom:0.5rem;
                        ">
                            <div style="
                                font-size:0.63rem;
                                color:#3A4F6A;
                                text-transform:uppercase;
                                letter-spacing:0.1em;
                                margin-bottom:0.2rem;
                            ">{label}</div>
                            <div style="
                                font-size:0.85rem;
                                color:#F0F6FF;
                                font-weight:500;
                            ">{value}</div>
                        </div>
                        """, unsafe_allow_html=True)


# ── COMPARISON TABLE ──────────────────────────────────────────────────────────

def render_comparison_table(result_a: dict, result_b: dict,
                             name_a: str = "Startup A",
                             name_b: str = "Startup B") -> None:
    """
    Render side-by-side comparison table for two startups.
    """
    from components.gauge import get_score_color

    dimensions = [
        ("🔍 Market",      "market_score"),
        ("⚔️ Competition", "competition_score"),
        ("💰 Financial",   "financial_score"),
        ("⚠️ Risk",        "risk_score"),
        ("💡 Innovation",  "innovation_score"),
        ("🏆 OVERALL",     "overall_investment_score"),
    ]

    # Header
    st.markdown(f"""
    <div style="
        display:grid;
        grid-template-columns:1fr 1fr 1fr 80px;
        gap:0.5rem;
        margin-bottom:0.5rem;
        padding:0.6rem 1rem;
    ">
        <div style="font-size:0.65rem; color:#3A4F6A; text-transform:uppercase; letter-spacing:0.1em;">Dimension</div>
        <div style="font-size:0.65rem; color:#00D4FF; text-transform:uppercase; letter-spacing:0.1em; text-align:center;">{name_a}</div>
        <div style="font-size:0.65rem; color:#6C63FF; text-transform:uppercase; letter-spacing:0.1em; text-align:center;">{name_b}</div>
        <div style="font-size:0.65rem; color:#3A4F6A; text-transform:uppercase; letter-spacing:0.1em; text-align:center;">Winner</div>
    </div>
    """, unsafe_allow_html=True)

    for label, key in dimensions:
        is_overall = key == "overall_investment_score"
        max_val = 100 if is_overall else 10
        suffix = "" if is_overall else "/10"

        score_a = result_a.get(key, 0)
        score_b = result_b.get(key, 0)

        norm_a = score_a if is_overall else (score_a / 10) * 100
        norm_b = score_b if is_overall else (score_b / 10) * 100

        color_a = get_score_color(norm_a)
        color_b = get_score_color(norm_b)

        if score_a > score_b:
            winner = f'<span style="color:#00D4FF; font-weight:700;">A ✓</span>'
        elif score_b > score_a:
            winner = f'<span style="color:#6C63FF; font-weight:700;">B ✓</span>'
        else:
            winner = f'<span style="color:#7B92B2;">Tie</span>'

        row_bg = "#102035" if is_overall else "#0D1B2E"
        border = "border:1px solid #00D4FF;" if is_overall else "border:1px solid #1A2F4A;"

        st.markdown(f"""
        <div style="
            display:grid;
            grid-template-columns:1fr 1fr 1fr 80px;
            gap:0.5rem;
            margin-bottom:0.4rem;
            padding:0.75rem 1rem;
            background:{row_bg};
            {border}
            border-radius:8px;
            align-items:center;
        ">
            <div style="font-size:0.88rem; color:#F0F6FF; font-weight:{'700' if is_overall else '400'};">
                {label}
            </div>
            <div style="text-align:center; font-size:1rem; font-weight:700; color:{color_a}; font-family:'Space Grotesk';">
                {score_a}{suffix}
            </div>
            <div style="text-align:center; font-size:1rem; font-weight:700; color:{color_b}; font-family:'Space Grotesk';">
                {score_b}{suffix}
            </div>
            <div style="text-align:center; font-size:0.85rem;">{winner}</div>
        </div>
        """, unsafe_allow_html=True)