"""
InvestIQ AI — Home / Landing Page
"""

import streamlit as st
from styles.theme import apply_theme


DEMO_RESULT = {
    "startup_name": "MediMatch AI",
    "industry": "HealthTech",
    "funding_stage": "Pre-Seed",
    "overall_investment_score": 78,
    "final_recommendation": "Strong Invest",
    "confidence_level": "High",
    "one_line_verdict": "Rare combination of massive market and genuine AI differentiation in a space ripe for disruption.",
    "market_score": 9,
    "competition_score": 6,
    "financial_score": 7,
    "risk_score": 7,
    "innovation_score": 9,
    "market_key_insight": "Clinical trial matching is a $4.2B problem — 80% of trials fail due to poor patient recruitment.",
    "competition_key_insight": "No scaled AI-native player dominates; incumbents are legacy software with weak ML layers.",
    "financial_key_insight": "SaaS model with high LTV and natural upsell path to pharma enterprise contracts.",
    "risk_key_insight": "Regulatory pathway for patient data handling is the primary execution risk.",
    "innovation_key_insight": "NLP-driven eligibility matching across 50,000+ active trials is a genuine technical moat.",
    "market_size_signal": "Large",
    "timing_assessment": "Right Time",
    "market_growth": "High Growth",
    "competitive_intensity": "Medium",
    "moat_assessment": "Moderate",
    "big_tech_risk": "Low",
    "revenue_model_quality": "Excellent",
    "scalability": "High",
    "margin_potential": "High",
    "capital_efficiency": "Efficient",
    "primary_risk": "HIPAA/GDPR compliance complexity may slow enterprise sales cycles significantly.",
    "risk_level": "Medium",
    "execution_risk": "Medium",
    "regulatory_risk": "High",
    "innovation_type": "Category Creator",
    "defensibility": "Strong",
    "unfair_advantage_signal": "Strong",
    "market_analysis": "The clinical trial recruitment market is severely underserved, with 80% of trials delayed due to patient matching inefficiencies. AI-native solutions are timing-perfect as EHR adoption reaches critical mass and pharma companies face increasing pressure on trial timelines and costs.",
    "competition_analysis": "Legacy players like Medidata and Veeva hold enterprise contracts but offer no AI-native matching. Startups in this space remain fragmented. MediMatch's focus on NLP eligibility matching creates a defensible technical wedge that incumbents cannot replicate quickly.",
    "financial_analysis": "The SaaS model targeting pharma sponsors and CROs offers exceptional unit economics — high ACV contracts, low churn, and natural expansion into additional trial phases. Gross margins should exceed 75% at scale.",
    "risk_analysis": "The primary risk is regulatory: handling PHI under HIPAA while scaling across jurisdictions requires significant legal overhead. Enterprise sales cycles in healthcare are long (9-18 months), demanding strong runway management.",
    "innovation_analysis": "The NLP eligibility matching engine trained on trial protocol language is a genuine technical innovation. The data flywheel — more matches generate better models — creates compounding defensibility that grows with each trial completed.",
    "decision_reasoning": "MediMatch AI addresses a critical, validated pain point in a multi-billion dollar market with demonstrable urgency. The technical differentiation is genuine and defensible through a data moat. Financial model is high-quality SaaS with natural enterprise expansion. Risk profile is manageable with proper regulatory preparation. Innovation score reflects category-creating potential in a space where AI adoption is still nascent. Committee recommends investment with a structured milestone around HIPAA compliance certification.",
    "strengths": [
        "Massive, validated market with quantifiable pain — 80% trial failure rate creates undeniable ROI case.",
        "Genuine technical moat via NLP matching engine with compounding data flywheel.",
        "High-quality SaaS revenue model with enterprise pharma as natural customer base.",
    ],
    "weaknesses": [
        "Regulatory complexity (HIPAA, IRB requirements) may significantly delay enterprise contracts.",
        "Long B2B sales cycles in pharma require substantial runway — 18+ months to first major deal.",
        "Moat depends on data accumulation speed — early network effects must be accelerated.",
    ],
    "recommended_actions": [
        "Prioritize HIPAA Business Associate Agreement certification before enterprise outreach.",
        "Establish 3 pilot agreements with mid-size CROs to build the data flywheel quickly.",
        "Structure the round to provide 24+ months runway to absorb pharma sales cycle length.",
    ],
    "agent_confidences": {
        "market": 9, "competition": 8, "financial": 8, "risk": 7, "innovation": 9
    },
}


def render_home():
    apply_theme()
    _render_hero()
    _divider()
    _render_demo()
    _divider()
    _render_how_it_works()
    _divider()
    _render_agents_showcase()
    _render_footer()


# ── HERO ───────────────────────────────────────────────────────────────────────

def _render_hero():
    # Badge
    st.markdown(
        '<div style="text-align:center;padding:3rem 1rem 0.5rem 1rem;">'
        '<div style="display:inline-block;background:rgba(0,212,255,0.08);'
        'border:1px solid rgba(0,212,255,0.25);border-radius:999px;'
        'padding:0.3rem 1rem;font-size:0.7rem;color:#00D4FF;'
        'text-transform:uppercase;letter-spacing:0.18em;font-weight:700;">'
        'Multi-Agent AI &nbsp;·&nbsp; Investment Intelligence'
        '</div></div>',
        unsafe_allow_html=True,
    )

    # Headline
    st.markdown(
        '<div style="text-align:center;padding:0.8rem 1rem 0 1rem;">'
        '<h1 style="font-family:\'Space Grotesk\',sans-serif;font-size:3rem;'
        'font-weight:800;color:#F0F6FF;line-height:1.15;letter-spacing:-0.03em;margin:0;">'
        'Investment Decisions<br>'
        '<span style="background:linear-gradient(135deg,#00D4FF 0%,#6C63FF 100%);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">'
        'Backed by AI Intelligence</span></h1>'
        '<p style="font-size:1rem;color:#7B92B2;max-width:540px;'
        'margin:1rem auto 1.5rem auto;line-height:1.7;">'
        '6 specialist AI agents analyze every startup across market, competition, '
        'financials, risk, and innovation — delivering structured, explainable '
        'investment scores in under 60 seconds.'
        '</p></div>',
        unsafe_allow_html=True,
    )

    # CTA button
    col_l, col_c, col_r = st.columns([1.5, 2, 1.5])
    with col_c:
        if st.button("🔍  Analyze a Startup →", use_container_width=True, type="primary"):
            st.session_state.current_page = "analyze"
            st.rerun()

    # Stats row — four separate columns so no flex issues
    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
    s1, s2, s3, s4 = st.columns(4)

    for col, value, label, color in [
        (s1, "6",    "AI Agents",     "#00D4FF"),
        (s2, "<60s", "Analysis Time", "#00FFB3"),
        (s3, "100%", "Free Forever",  "#6C63FF"),
        (s4, "PDF",  "Export Ready",  "#F59E0B"),
    ]:
        with col:
            st.markdown(
                f'<div style="text-align:center;padding:0.5rem 0;">'
                f'<div style="font-family:\'Space Grotesk\',sans-serif;font-size:1.6rem;'
                f'font-weight:700;color:{color};">{value}</div>'
                f'<div style="font-size:0.7rem;color:#3A4F6A;text-transform:uppercase;'
                f'letter-spacing:0.1em;margin-top:0.2rem;">{label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ── DEMO DASHBOARD ─────────────────────────────────────────────────────────────

def _render_demo():
    st.markdown(
        '<div style="text-align:center;margin-bottom:1.5rem;">'
        '<div style="font-size:0.62rem;color:#3A4F6A;text-transform:uppercase;'
        'letter-spacing:0.18em;font-weight:600;margin-bottom:0.4rem;">'
        'LIVE DEMO — NO SIGN IN REQUIRED</div>'
        '<div style="font-size:1.3rem;font-weight:700;color:#F0F6FF;'
        'font-family:\'Space Grotesk\',sans-serif;">See a real analysis output</div>'
        '<div style="font-size:0.85rem;color:#7B92B2;margin-top:0.3rem;">'
        'MediMatch AI &nbsp;·&nbsp; HealthTech &nbsp;·&nbsp; Pre-Seed</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    from components.gauge import render_score_hero
    from components.score_cards import (
        render_four_score_cards,
        render_strengths_weaknesses,
        render_executive_summary,
    )
    from components.radar import render_radar

    st.markdown(
        '<div style="background:#0D1B2E;border:1px solid #1A2F4A;'
        'border-radius:16px;padding:2rem 1.5rem 1.5rem 1.5rem;">',
        unsafe_allow_html=True,
    )

    render_score_hero(DEMO_RESULT)
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    render_four_score_cards(DEMO_RESULT)
    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

    col_radar, col_sw = st.columns([1, 1.2])
    with col_radar:
        st.markdown(
            '<div style="font-size:0.62rem;color:#3A4F6A;text-transform:uppercase;'
            'letter-spacing:0.15em;font-weight:600;margin-bottom:0.3rem;text-align:center;">'
            '5-DIMENSION RADAR</div>',
            unsafe_allow_html=True,
        )
        render_radar(DEMO_RESULT, height=320)
    with col_sw:
        render_strengths_weaknesses(DEMO_RESULT)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    render_executive_summary(DEMO_RESULT)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    col_l, col_c, col_r = st.columns([1.5, 2, 1.5])
    with col_c:
        if st.button("Analyze Your Own Startup →", use_container_width=True):
            st.session_state.current_page = "analyze"
            st.rerun()


# ── HOW IT WORKS ──────────────────────────────────────────────────────────────

def _render_how_it_works():
    st.markdown(
        '<div style="text-align:center;margin-bottom:1.8rem;">'
        '<div style="font-size:0.62rem;color:#3A4F6A;text-transform:uppercase;'
        'letter-spacing:0.18em;font-weight:600;margin-bottom:0.4rem;">HOW IT WORKS</div>'
        '<div style="font-size:1.4rem;font-weight:700;color:#F0F6FF;'
        'font-family:\'Space Grotesk\',sans-serif;">Three steps. Under 60 seconds.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    steps = [
        ("01", "📝", "Describe the Startup",
         "Enter the startup name, description, industry, business model, and funding stage. Takes 60 seconds.",
         "#00D4FF"),
        ("02", "🤖", "6 Agents Analyze",
         "Market, Competition, Financial, Risk, and Innovation agents run in sequence. The Investment Committee synthesizes the verdict.",
         "#6C63FF"),
        ("03", "📊", "Get Your Score",
         "Receive a structured dashboard with scores, charts, reasoning, and a PDF report you can share.",
         "#00FFB3"),
    ]
    for col, (num, icon, title, desc, color) in zip([col1, col2, col3], steps):
        with col:
            st.markdown(
                f'<div style="background:#0D1B2E;border:1px solid #1A2F4A;'
                f'border-top:2px solid {color};border-radius:14px;'
                f'padding:1.8rem 1.4rem;text-align:center;">'
                f'<div style="font-size:0.65rem;color:{color};letter-spacing:0.12em;'
                f'font-weight:700;margin-bottom:0.8rem;">STEP {num}</div>'
                f'<div style="font-size:2rem;margin-bottom:0.8rem;">{icon}</div>'
                f'<div style="font-size:0.98rem;font-weight:700;color:#F0F6FF;'
                f'font-family:\'Space Grotesk\',sans-serif;margin-bottom:0.6rem;">{title}</div>'
                f'<div style="font-size:0.82rem;color:#7B92B2;line-height:1.6;">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ── AGENT SHOWCASE ─────────────────────────────────────────────────────────────

def _render_agents_showcase():
    st.markdown(
        '<div style="text-align:center;margin-bottom:1.8rem;">'
        '<div style="font-size:0.62rem;color:#3A4F6A;text-transform:uppercase;'
        'letter-spacing:0.18em;font-weight:600;margin-bottom:0.4rem;">'
        'THE INTELLIGENCE LAYER</div>'
        '<div style="font-size:1.4rem;font-weight:700;color:#F0F6FF;'
        'font-family:\'Space Grotesk\',sans-serif;">Meet the 6 Specialist Agents</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    agents = [
        ("🔍", "Market Intelligence",    "llama-3.3-70b · Groq",
         "Evaluates market size, timing, demand signals, and growth trajectory.", "#00D4FF"),
        ("⚔️", "Competitive Landscape",  "llama-3.3-70b · Groq",
         "Maps competitors, moats, differentiation strength, and Big Tech risk.", "#6C63FF"),
        ("💰", "Financial Viability",    "llama-3.3-70b · Groq",
         "Assesses revenue model, unit economics, scalability, and margins.", "#00FFB3"),
        ("⚠️", "Risk Assessment",        "deepseek-r1 · Groq",
         "Deep reasoning on execution, regulatory, market, and macro risks.", "#F59E0B"),
        ("💡", "Innovation Scout",       "llama-3.3-70b · Groq",
         "Scores novelty, defensibility, and unfair advantage potential.", "#B45FFF"),
        ("🏛️", "Investment Committee",   "Gemini 2.5 Flash",
         "Synthesizes all 5 agents into a final weighted investment decision.", "#FF6B35"),
    ]

    col_a, col_b = st.columns(2)
    for i, (icon, name, model, desc, color) in enumerate(agents):
        col = col_a if i % 2 == 0 else col_b
        with col:
            st.markdown(
                f'<div style="background:#0D1B2E;border:1px solid #1A2F4A;'
                f'border-left:3px solid {color};border-radius:10px;'
                f'padding:1rem 1.2rem;margin-bottom:0.8rem;'
                f'display:flex;gap:1rem;align-items:flex-start;">'
                f'<div style="font-size:1.4rem;flex-shrink:0;">{icon}</div>'
                f'<div>'
                f'<div style="font-size:0.92rem;font-weight:700;color:#F0F6FF;'
                f'font-family:\'Space Grotesk\',sans-serif;margin-bottom:0.15rem;">{name}</div>'
                f'<div style="font-size:0.63rem;color:{color};text-transform:uppercase;'
                f'letter-spacing:0.08em;margin-bottom:0.3rem;">{model}</div>'
                f'<div style="font-size:0.8rem;color:#7B92B2;line-height:1.5;">{desc}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )


# ── FOOTER ─────────────────────────────────────────────────────────────────────

def _render_footer():
    st.markdown(
        '<div style="text-align:center;padding:3rem 1rem 1rem 1rem;'
        'border-top:1px solid #1A2F4A;margin-top:2rem;">'
        '<div style="font-family:\'Space Grotesk\',sans-serif;font-weight:700;'
        'font-size:1.2rem;color:#F0F6FF;margin-bottom:0.5rem;">'
        'Invest<span style="background:linear-gradient(135deg,#00D4FF,#6C63FF);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">IQ</span> AI'
        '</div>'
        '<div style="font-size:0.78rem;color:#3A4F6A;">'
        'Powered by Groq &nbsp;·&nbsp; Gemini 2.5 &nbsp;·&nbsp; Firebase &nbsp;·&nbsp; Streamlit'
        '</div>'
        '<div style="font-size:0.72rem;color:#1A2F4A;margin-top:0.5rem;">'
        'AI-generated analysis is for informational purposes only. Not financial advice.'
        '</div></div>',
        unsafe_allow_html=True,
    )


def _divider():
    st.markdown(
        '<div style="height:1px;'
        'background:linear-gradient(90deg,transparent,#1A2F4A,transparent);'
        'margin:2.5rem 0;"></div>',
        unsafe_allow_html=True,
    )
