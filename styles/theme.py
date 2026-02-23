import streamlit as st


def apply_theme():
    """Inject full InvestIQ AI dark theme CSS into every page."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── BASE ─────────────────────────────────────────── */
    html, body, [class*="css"], .stApp {
        font-family: 'Space Grotesk', sans-serif !important;
        background-color: #070D1A !important;
        color: #F0F6FF !important;
    }

    /* ── HIDE STREAMLIT UI CHROME ─────────────────────── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    .stDeployButton { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }

    /* ── MAIN CONTAINER ───────────────────────────────── */
    .main .block-container {
        padding: 2rem 2.5rem 4rem 2.5rem !important;
        max-width: 1200px !important;
    }

    /* ── SIDEBAR ──────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: #0D1B2E !important;
        border-right: 1px solid #1A2F4A !important;
    }
    [data-testid="stSidebar"] .stMarkdown p {
        color: #7B92B2 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: #1A2F4A !important;
        margin: 0.5rem 0 !important;
    }

    /* ── SIDEBAR NAV BUTTONS ──────────────────────────── */
    [data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        border: 1px solid transparent !important;
        color: #7B92B2 !important;
        width: 100% !important;
        text-align: left !important;
        padding: 0.6rem 1rem !important;
        border-radius: 8px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        background-image: none !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(0, 212, 255, 0.08) !important;
        border-color: #1A2F4A !important;
        color: #00D4FF !important;
    }

    /* ── GLOBAL BUTTONS ───────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, #00D4FF 0%, #6C63FF 100%) !important;
        color: #070D1A !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: 0.02em !important;
        transition: opacity 0.2s, transform 0.1s !important;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.2) !important;
    }
    .stButton > button:hover {
        opacity: 0.88 !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button:active {
        transform: translateY(0px) !important;
    }

    /* ── INPUTS ───────────────────────────────────────── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: #0D1B2E !important;
        border: 1px solid #1A2F4A !important;
        color: #F0F6FF !important;
        border-radius: 8px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        transition: border-color 0.2s !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #00D4FF !important;
        box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.15) !important;
    }
    .stTextInput label, .stTextArea label, .stSelectbox label {
        color: #7B92B2 !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
    }

    /* ── SELECTBOX ────────────────────────────────────── */
    .stSelectbox > div > div {
        background: #0D1B2E !important;
        border: 1px solid #1A2F4A !important;
        border-radius: 8px !important;
        color: #F0F6FF !important;
    }
    .stSelectbox > div > div:focus-within {
        border-color: #00D4FF !important;
    }

    /* ── EXPANDERS ────────────────────────────────────── */
    .streamlit-expanderHeader {
        background: #0D1B2E !important;
        border: 1px solid #1A2F4A !important;
        border-radius: 8px !important;
        color: #F0F6FF !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
    }
    .streamlit-expanderHeader:hover {
        border-color: #00D4FF !important;
        color: #00D4FF !important;
    }
    .streamlit-expanderContent {
        background: #0D1B2E !important;
        border: 1px solid #1A2F4A !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
    }

    /* ── DIVIDERS ─────────────────────────────────────── */
    hr {
        border-color: #1A2F4A !important;
        margin: 1.5rem 0 !important;
    }

    /* ── METRIC WIDGETS ───────────────────────────────── */
    [data-testid="metric-container"] {
        background: #0D1B2E !important;
        border: 1px solid #1A2F4A !important;
        border-radius: 12px !important;
        padding: 1rem 1.2rem !important;
    }
    [data-testid="metric-container"] label {
        color: #7B92B2 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #F0F6FF !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1.8rem !important;
        font-weight: 500 !important;
    }

    /* ── TOAST / SUCCESS ──────────────────────────────── */
    .stSuccess {
        background: rgba(0, 255, 179, 0.08) !important;
        border: 1px solid rgba(0, 255, 179, 0.3) !important;
        border-radius: 8px !important;
        color: #00FFB3 !important;
    }
    .stError {
        background: rgba(255, 69, 96, 0.08) !important;
        border: 1px solid rgba(255, 69, 96, 0.3) !important;
        border-radius: 8px !important;
        color: #FF4560 !important;
    }
    .stWarning {
        background: rgba(245, 158, 11, 0.08) !important;
        border: 1px solid rgba(245, 158, 11, 0.3) !important;
        border-radius: 8px !important;
        color: #F59E0B !important;
    }
    .stInfo {
        background: rgba(0, 212, 255, 0.08) !important;
        border: 1px solid rgba(0, 212, 255, 0.3) !important;
        border-radius: 8px !important;
        color: #00D4FF !important;
    }

    /* ── SPINNER ──────────────────────────────────────── */
    .stSpinner > div {
        border-top-color: #00D4FF !important;
    }

    /* ── SCROLLBAR ────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #070D1A; }
    ::-webkit-scrollbar-thumb { background: #1A2F4A; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #00D4FF; }

    /* ── CUSTOM CARD COMPONENT ────────────────────────── */
    .iq-card {
        background: #0D1B2E;
        border: 1px solid #1A2F4A;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: border-color 0.2s;
    }
    .iq-card:hover { border-color: rgba(0, 212, 255, 0.4); }

    /* ── SCORE CARDS ──────────────────────────────────── */
    .score-card {
        background: #0D1B2E;
        border: 1px solid #1A2F4A;
        border-radius: 12px;
        padding: 1.5rem 1rem;
        text-align: center;
        transition: all 0.2s ease;
        position: relative;
        overflow: hidden;
    }
    .score-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--accent, #00D4FF), transparent);
    }
    .score-card:hover {
        border-color: var(--accent, #00D4FF);
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 212, 255, 0.1);
    }
    .score-number {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.8rem;
        font-weight: 500;
        line-height: 1;
        margin: 0.4rem 0 0.2rem 0;
    }
    .score-label {
        font-size: 0.7rem;
        color: #7B92B2;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-weight: 600;
    }
    .score-sublabel {
        font-size: 0.75rem;
        color: #7B92B2;
        margin-top: 0.3rem;
    }

    /* ── RECOMMENDATION PILLS ─────────────────────────── */
    .pill-invest {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: rgba(0, 255, 179, 0.12);
        color: #00FFB3;
        border: 1px solid rgba(0, 255, 179, 0.4);
        border-radius: 999px;
        padding: 0.4rem 1.2rem;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .pill-consider {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: rgba(245, 158, 11, 0.12);
        color: #F59E0B;
        border: 1px solid rgba(245, 158, 11, 0.4);
        border-radius: 999px;
        padding: 0.4rem 1.2rem;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .pill-reject {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: rgba(255, 69, 96, 0.12);
        color: #FF4560;
        border: 1px solid rgba(255, 69, 96, 0.4);
        border-radius: 999px;
        padding: 0.4rem 1.2rem;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    /* ── CONFIDENCE BADGES ────────────────────────────── */
    .badge-high {
        display: inline-block;
        background: rgba(0, 212, 255, 0.1);
        color: #00D4FF;
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 6px;
        padding: 0.2rem 0.7rem;
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .badge-medium {
        display: inline-block;
        background: rgba(245, 158, 11, 0.1);
        color: #F59E0B;
        border: 1px solid rgba(245, 158, 11, 0.3);
        border-radius: 6px;
        padding: 0.2rem 0.7rem;
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .badge-low {
        display: inline-block;
        background: rgba(255, 69, 96, 0.1);
        color: #FF4560;
        border: 1px solid rgba(255, 69, 96, 0.3);
        border-radius: 6px;
        padding: 0.2rem 0.7rem;
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    /* ── AGENT LOADER ─────────────────────────────────── */
    .agent-row {
        background: #0D1B2E;
        border: 1px solid #1A2F4A;
        border-radius: 10px;
        padding: 0.9rem 1.2rem;
        margin: 0.4rem 0;
        display: flex;
        align-items: center;
        gap: 1rem;
        transition: all 0.3s ease;
    }
    .agent-row.active {
        border-color: #00D4FF;
        background: rgba(0, 212, 255, 0.06);
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.08);
    }
    .agent-row.complete {
        border-color: rgba(0, 255, 179, 0.4);
        background: rgba(0, 255, 179, 0.04);
    }
    .agent-row.pending {
        opacity: 0.4;
    }
    .agent-icon {
        font-size: 1.3rem;
        width: 2rem;
        text-align: center;
    }
    .agent-name {
        font-weight: 600;
        font-size: 0.9rem;
        color: #F0F6FF;
    }
    .agent-status {
        font-size: 0.78rem;
        color: #7B92B2;
        margin-top: 0.1rem;
    }
    .agent-check {
        margin-left: auto;
        color: #00FFB3;
        font-size: 1rem;
    }

    /* ── PAGE HEADER ──────────────────────────────────── */
    .page-header {
        margin-bottom: 2rem;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid #1A2F4A;
    }
    .page-header h1 {
        font-size: 1.8rem;
        font-weight: 700;
        color: #F0F6FF;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .page-header p {
        color: #7B92B2;
        margin: 0.3rem 0 0 0;
        font-size: 0.9rem;
    }

    /* ── VERDICT TEXT ─────────────────────────────────── */
    .verdict-text {
        font-style: italic;
        color: #7B92B2;
        font-size: 0.95rem;
        line-height: 1.6;
        border-left: 2px solid #1A2F4A;
        padding-left: 1rem;
        margin: 0.8rem 0;
    }

    /* ── ANALYSIS CARD ────────────────────────────────── */
    .analysis-item-card {
        background: #0D1B2E;
        border: 1px solid #1A2F4A;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 0.8rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .analysis-item-card:hover {
        border-color: #00D4FF;
        transform: translateY(-1px);
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.08);
    }
    .analysis-startup-name {
        font-size: 1.05rem;
        font-weight: 600;
        color: #F0F6FF;
    }
    .analysis-meta {
        font-size: 0.78rem;
        color: #7B92B2;
        margin-top: 0.2rem;
    }

    /* ── LOGO ─────────────────────────────────────────── */
    .logo-text {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 1.3rem;
        letter-spacing: -0.02em;
        color: #F0F6FF;
    }
    .logo-text span {
        background: linear-gradient(135deg, #00D4FF, #6C63FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* ── GLOW DIVIDER ─────────────────────────────────── */
    .glow-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #00D4FF, transparent);
        margin: 2rem 0;
        opacity: 0.4;
    }

    /* ── STAT HIGHLIGHT ───────────────────────────────── */
    .stat-highlight {
        font-family: 'JetBrains Mono', monospace;
        color: #00D4FF;
        font-size: 0.9rem;
    }

    </style>
    """, unsafe_allow_html=True)


def render_logo(size: str = "normal"):
    """Render the InvestIQ AI logo."""
    if size == "large":
        st.markdown("""
        <div style="text-align:center; margin-bottom:1rem;">
            <span style="
                font-family:'Space Grotesk',sans-serif;
                font-weight:700;
                font-size:2.2rem;
                letter-spacing:-0.03em;
                color:#F0F6FF;
            ">Invest<span style="
                background:linear-gradient(135deg,#00D4FF,#6C63FF);
                -webkit-background-clip:text;
                -webkit-text-fill-color:transparent;
            ">IQ</span> <span style="
                font-size:1.1rem;
                font-weight:400;
                color:#7B92B2;
                letter-spacing:0.1em;
                text-transform:uppercase;
            ">AI</span></span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="logo-text">Invest<span>IQ</span> AI</div>
        """, unsafe_allow_html=True)


def render_pill(recommendation: str):
    """Render color-coded recommendation pill."""
    rec = recommendation.lower()
    if "strong invest" in rec or "invest" in rec:
        st.markdown(f'<span class="pill-invest">🟢 {recommendation}</span>', unsafe_allow_html=True)
    elif "consider" in rec:
        st.markdown(f'<span class="pill-consider">🟡 {recommendation}</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="pill-reject">🔴 {recommendation}</span>', unsafe_allow_html=True)


def render_confidence_badge(level: str):
    """Render confidence level badge."""
    level_lower = level.lower()
    if level_lower == "high":
        st.markdown(f'<span class="badge-high">⬆ {level} Confidence</span>', unsafe_allow_html=True)
    elif level_lower == "medium":
        st.markdown(f'<span class="badge-medium">➡ {level} Confidence</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="badge-low">⬇ {level} Confidence</span>', unsafe_allow_html=True)


def get_score_color(score: float, out_of: int = 10) -> str:
    """Return color hex based on score value."""
    normalized = (score / out_of) * 100
    if normalized >= 70:
        return "#00FFB3"
    elif normalized >= 45:
        return "#F59E0B"
    else:
        return "#FF4560"


def render_section_header(title: str, subtitle: str = ""):
    """Render a styled section header."""
    html = f'<div class="page-header"><h1>{title}</h1>'
    if subtitle:
        html += f'<p>{subtitle}</p>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)