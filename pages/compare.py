"""
InvestIQ AI — Compare Page
Side-by-side comparison of two saved analyses.
Includes overlay radar chart and winner table.
"""

import streamlit as st
from styles.theme import apply_theme
from auth.firebase_auth import is_logged_in, render_auth_modal, get_current_uid


def render_compare():
    apply_theme()

    st.markdown("""
    <div class="page-header">
        <h1>⚖️ Compare Startups</h1>
        <p>Select two saved analyses to compare them side by side.</p>
    </div>
    """, unsafe_allow_html=True)

    if not is_logged_in():
        render_auth_modal()
        return

    uid = get_current_uid()

    # ── Load saved analyses list ───────────────────────────────────────────────
    if "compare_analyses_cache" not in st.session_state:
        st.session_state.compare_analyses_cache = None

    if st.session_state.compare_analyses_cache is None:
        with st.spinner("Loading your analyses..."):
            from db.firestore import list_analyses
            all_analyses = list_analyses(uid, limit=50)
            st.session_state.compare_analyses_cache = all_analyses
    else:
        all_analyses = st.session_state.compare_analyses_cache

    # ── Need at least 2 ────────────────────────────────────────────────────────
    if len(all_analyses) < 2:
        st.markdown("""
        <div style="
            text-align:center;
            padding:4rem 2rem;
            background:#0D1B2E;
            border:1px dashed #1A2F4A;
            border-radius:14px;
            margin-top:1rem;
        ">
            <div style="font-size:2.5rem; margin-bottom:1rem;">📊</div>
            <div style="
                font-size:1.1rem; font-weight:700;
                color:#F0F6FF; margin-bottom:0.5rem;
                font-family:'Space Grotesk', sans-serif;
            ">Need at least 2 saved analyses</div>
            <div style="font-size:0.85rem; color:#7B92B2;">
                Save two startup analyses first, then come back to compare them.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        col_l, col_c, col_r = st.columns([1.5, 2, 1.5])
        with col_c:
            if st.button("🔍  Analyze a Startup →", use_container_width=True):
                st.session_state.current_page = "analyze"
                st.rerun()
        return

    # ── Build dropdown options ─────────────────────────────────────────────────
    options = {
        f"{a.get('startup_name', 'Unnamed')} — {a.get('overall_investment_score', 0)}/100 ({a.get('final_recommendation', '')})": i
        for i, a in enumerate(all_analyses)
    }
    option_labels = list(options.keys())

    # Pre-load from history page "Compare" button if set
    preload = st.session_state.pop("compare_preload", None)
    preload_name = preload.get("startup_name", "") if preload else ""
    preload_idx = next(
        (i for i, a in enumerate(all_analyses) if a.get("startup_name") == preload_name),
        0,
    )

    # ── Selector row ──────────────────────────────────────────────────────────
    col_a, col_vs, col_b = st.columns([5, 1, 5])

    with col_a:
        st.markdown("""
        <div style="
            font-size:0.65rem; color:#00D4FF;
            text-transform:uppercase; letter-spacing:0.15em;
            font-weight:700; margin-bottom:0.4rem;
        ">STARTUP A</div>
        """, unsafe_allow_html=True)
        sel_a = st.selectbox(
            "Startup A",
            option_labels,
            index=preload_idx,
            label_visibility="collapsed",
            key="compare_sel_a",
        )

    with col_vs:
        st.markdown("""
        <div style="
            text-align:center;
            padding-top:1.6rem;
            font-size:1rem;
            font-weight:700;
            color:#3A4F6A;
        ">VS</div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown("""
        <div style="
            font-size:0.65rem; color:#6C63FF;
            text-transform:uppercase; letter-spacing:0.15em;
            font-weight:700; margin-bottom:0.4rem;
        ">STARTUP B</div>
        """, unsafe_allow_html=True)
        # Default B to second option if A is first
        default_b = 1 if options[sel_a] == 0 else 0
        sel_b = st.selectbox(
            "Startup B",
            option_labels,
            index=default_b,
            label_visibility="collapsed",
            key="compare_sel_b",
        )

    idx_a = options[sel_a]
    idx_b = options[sel_b]

    if idx_a == idx_b:
        st.warning("Please select two different analyses to compare.")
        return

    result_a = all_analyses[idx_a]
    result_b = all_analyses[idx_b]
    name_a = result_a.get("startup_name", "Startup A")
    name_b = result_b.get("startup_name", "Startup B")

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── Header cards for each startup ─────────────────────────────────────────
    _render_compare_header(result_a, result_b, name_a, name_b)

    _divider()

    # ── Score comparison table ─────────────────────────────────────────────────
    st.markdown("""
    <div style="
        font-size:0.65rem; color:#3A4F6A;
        text-transform:uppercase; letter-spacing:0.18em;
        font-weight:600; margin-bottom:1rem;
    ">DIMENSION BREAKDOWN</div>
    """, unsafe_allow_html=True)

    from components.score_cards import render_comparison_table
    render_comparison_table(result_a, result_b, name_a, name_b)

    _divider()

    # ── Overlay Radar ─────────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        font-size:0.65rem; color:#3A4F6A;
        text-transform:uppercase; letter-spacing:0.18em;
        font-weight:600; margin-bottom:0.5rem; text-align:center;
    ">RADAR OVERLAY — BOTH STARTUPS</div>
    """, unsafe_allow_html=True)

    from components.radar import render_comparison_radar
    render_comparison_radar(result_a, result_b, name_a, name_b, height=440)

    _divider()

    # ── Strengths/Weaknesses side by side ──────────────────────────────────────
    st.markdown("""
    <div style="
        font-size:0.65rem; color:#3A4F6A;
        text-transform:uppercase; letter-spacing:0.18em;
        font-weight:600; margin-bottom:1rem;
    ">STRENGTHS & WEAKNESSES</div>
    """, unsafe_allow_html=True)

    col_sw_a, col_sw_b = st.columns(2)

    with col_sw_a:
        _render_sw_panel(result_a, name_a, "#00D4FF")
    with col_sw_b:
        _render_sw_panel(result_b, name_b, "#6C63FF")

    _divider()

    # ── Verdicts ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        font-size:0.65rem; color:#3A4F6A;
        text-transform:uppercase; letter-spacing:0.18em;
        font-weight:600; margin-bottom:1rem;
    ">COMMITTEE VERDICTS</div>
    """, unsafe_allow_html=True)

    col_v1, col_v2 = st.columns(2)
    for col, result, color in [(col_v1, result_a, "#00D4FF"), (col_v2, result_b, "#6C63FF")]:
        with col:
            verdict = result.get("one_line_verdict", "")
            reasoning = result.get("decision_reasoning", "")
            name = result.get("startup_name", "")
            if verdict or reasoning:
                st.markdown(f"""
                <div style="
                    background:#0D1B2E;
                    border:1px solid #1A2F4A;
                    border-left:3px solid {color};
                    border-radius:10px;
                    padding:1.2rem;
                ">
                    <div style="
                        font-size:0.65rem; color:{color};
                        text-transform:uppercase; letter-spacing:0.1em;
                        font-weight:700; margin-bottom:0.6rem;
                    ">{name}</div>
                    {f'<div style="font-size:0.88rem; color:#C8D8E8; font-style:italic; line-height:1.6; margin-bottom:0.8rem;">"{verdict}"</div>' if verdict else ''}
                    {f'<div style="font-size:0.82rem; color:#7B92B2; line-height:1.65;">{reasoning}</div>' if reasoning else ''}
                </div>
                """, unsafe_allow_html=True)


# ── HELPERS ────────────────────────────────────────────────────────────────────

def _render_compare_header(result_a, result_b, name_a, name_b):
    from components.gauge import get_score_color

    col_a, col_b = st.columns(2)

    for col, result, name, accent in [
        (col_a, result_a, name_a, "#00D4FF"),
        (col_b, result_b, name_b, "#6C63FF"),
    ]:
        score = result.get("overall_investment_score", 0)
        rec = result.get("final_recommendation", "")
        conf = result.get("confidence_level", "")
        industry = result.get("industry", "")
        stage = result.get("funding_stage", "")
        score_col = get_score_color(score)

        rec_lower = rec.lower()
        if "invest" in rec_lower:
            pill_col = "#00FFB3"
            pill_bg = "rgba(0,255,179,0.10)"
            pill_border = "rgba(0,255,179,0.35)"
            pill_icon = "🟢"
        elif "consider" in rec_lower:
            pill_col = "#F59E0B"
            pill_bg = "rgba(245,158,11,0.10)"
            pill_border = "rgba(245,158,11,0.35)"
            pill_icon = "🟡"
        else:
            pill_col = "#FF4560"
            pill_bg = "rgba(255,69,96,0.10)"
            pill_border = "rgba(255,69,96,0.35)"
            pill_icon = "🔴"

        with col:
            st.markdown(f"""
            <div style="
                background:#0D1B2E;
                border:1px solid #1A2F4A;
                border-top:3px solid {accent};
                border-radius:12px;
                padding:1.5rem;
                text-align:center;
            ">
                <div style="
                    font-size:0.65rem; color:{accent};
                    text-transform:uppercase; letter-spacing:0.15em;
                    font-weight:700; margin-bottom:0.4rem;
                ">{name_a if accent == '#00D4FF' else name_b}</div>
                <div style="
                    font-size:1rem; font-weight:700;
                    color:#F0F6FF;
                    font-family:'Space Grotesk', sans-serif;
                    margin-bottom:0.4rem;
                ">{name}</div>
                <div style="font-size:0.78rem; color:#7B92B2; margin-bottom:0.8rem;">
                    {industry}{'  ·  ' + stage if stage else ''}
                </div>
                <div style="
                    font-family:'JetBrains Mono', monospace;
                    font-size:3rem;
                    font-weight:500;
                    color:{score_col};
                    line-height:1;
                    margin-bottom:0.6rem;
                ">{score}</div>
                <div style="font-size:0.75rem; color:#7B92B2; margin-bottom:0.8rem;">out of 100</div>
                <div style="
                    display:inline-flex;
                    align-items:center;
                    gap:0.3rem;
                    background:{pill_bg};
                    color:{pill_col};
                    border:1px solid {pill_border};
                    border-radius:999px;
                    padding:0.3rem 0.9rem;
                    font-size:0.72rem;
                    font-weight:700;
                    text-transform:uppercase;
                    letter-spacing:0.06em;
                ">{pill_icon} {rec}</div>
                {'<div style="font-size:0.7rem; color:#3A4F6A; margin-top:0.4rem;">' + conf + ' Confidence</div>' if conf else ''}
            </div>
            """, unsafe_allow_html=True)


def _render_sw_panel(result: dict, name: str, accent: str):
    strengths = result.get("strengths", [])
    weaknesses = result.get("weaknesses", [])

    st.markdown(f"""
    <div style="
        background:#0D1B2E;
        border:1px solid #1A2F4A;
        border-top:2px solid {accent};
        border-radius:12px;
        padding:1.2rem;
    ">
        <div style="
            font-size:0.72rem; color:{accent};
            font-weight:700; margin-bottom:0.8rem;
            text-transform:uppercase; letter-spacing:0.1em;
        ">{name}</div>
    """, unsafe_allow_html=True)

    if strengths:
        st.markdown("""
        <div style="
            font-size:0.62rem; color:#00FFB3;
            text-transform:uppercase; letter-spacing:0.1em;
            font-weight:700; margin-bottom:0.4rem;
        ">✅ STRENGTHS</div>
        """, unsafe_allow_html=True)
        for s in strengths:
            if s:
                st.markdown(f"""
                <div style="
                    font-size:0.8rem; color:#C8D8E8;
                    line-height:1.5; margin-bottom:0.4rem;
                    padding-left:0.8rem;
                    border-left:2px solid rgba(0,255,179,0.3);
                ">▸ {s}</div>
                """, unsafe_allow_html=True)

    if weaknesses:
        st.markdown("""
        <div style="
            font-size:0.62rem; color:#FF4560;
            text-transform:uppercase; letter-spacing:0.1em;
            font-weight:700; margin:0.8rem 0 0.4rem 0;
        ">❌ WEAKNESSES</div>
        """, unsafe_allow_html=True)
        for w in weaknesses:
            if w:
                st.markdown(f"""
                <div style="
                    font-size:0.8rem; color:#C8D8E8;
                    line-height:1.5; margin-bottom:0.4rem;
                    padding-left:0.8rem;
                    border-left:2px solid rgba(255,69,96,0.3);
                ">▸ {w}</div>
                """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def _divider():
    st.markdown("""
    <div style="
        height:1px;
        background:linear-gradient(90deg,transparent,#1A2F4A,transparent);
        margin:1.8rem 0;
    "></div>
    """, unsafe_allow_html=True)
