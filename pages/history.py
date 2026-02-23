"""
InvestIQ AI — History Page
Displays all saved analyses for the logged-in user.
Grid layout with score, recommendation, date, and actions.
"""

import streamlit as st
from styles.theme import apply_theme
from auth.firebase_auth import is_logged_in, render_auth_modal, get_current_uid


def render_history():
    apply_theme()

    st.markdown("""
    <div class="page-header">
        <h1>📁 My Analyses</h1>
        <p>All your saved investment analyses — click any card to view the full report.</p>
    </div>
    """, unsafe_allow_html=True)

    if not is_logged_in():
        render_auth_modal()
        return

    uid = get_current_uid()

    # ── Load analyses ──────────────────────────────────────────────────────────
    if "history_cache" not in st.session_state:
        st.session_state.history_cache = None
    if "history_loaded" not in st.session_state:
        st.session_state.history_loaded = False

    col_refresh, col_spacer = st.columns([1, 5])
    with col_refresh:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.history_cache = None
            st.session_state.history_loaded = False
            st.rerun()

    if not st.session_state.history_loaded:
        with st.spinner("Loading your analyses..."):
            from db.firestore import list_analyses
            analyses = list_analyses(uid, limit=50)
            st.session_state.history_cache = analyses
            st.session_state.history_loaded = True
    else:
        analyses = st.session_state.history_cache or []

    # ── Empty state ────────────────────────────────────────────────────────────
    if not analyses:
        st.markdown("""
        <div style="
            text-align:center;
            padding:4rem 2rem;
            background:#0D1B2E;
            border:1px dashed #1A2F4A;
            border-radius:14px;
            margin-top:1rem;
        ">
            <div style="font-size:2.5rem; margin-bottom:1rem;">📭</div>
            <div style="
                font-size:1.1rem;
                font-weight:700;
                color:#F0F6FF;
                margin-bottom:0.5rem;
                font-family:'Space Grotesk', sans-serif;
            ">No analyses yet</div>
            <div style="font-size:0.85rem; color:#7B92B2;">
                Run your first startup analysis to see it here.
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

    # ── Summary row ────────────────────────────────────────────────────────────
    total = len(analyses)
    avg_score = round(sum(a.get("overall_investment_score", 0) for a in analyses) / total) if total else 0
    invest_count = sum(1 for a in analyses if "invest" in a.get("final_recommendation", "").lower())

    c1, c2, c3 = st.columns(3)
    for col, label, value, color in [
        (c1, "Total Analyses", str(total), "#00D4FF"),
        (c2, "Avg Score", f"{avg_score}/100", _score_color(avg_score)),
        (c3, "Strong Invest", str(invest_count), "#00FFB3"),
    ]:
        with col:
            st.markdown(f"""
            <div style="
                background:#0D1B2E;
                border:1px solid #1A2F4A;
                border-radius:10px;
                padding:1rem;
                text-align:center;
                margin-bottom:1rem;
            ">
                <div style="
                    font-family:'JetBrains Mono', monospace;
                    font-size:1.8rem;
                    font-weight:500;
                    color:{color};
                ">{value}</div>
                <div style="
                    font-size:0.68rem;
                    color:#7B92B2;
                    text-transform:uppercase;
                    letter-spacing:0.1em;
                    margin-top:0.2rem;
                ">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div style="
        height:1px;
        background:linear-gradient(90deg,transparent,#1A2F4A,transparent);
        margin:0.5rem 0 1.5rem 0;
    "></div>
    """, unsafe_allow_html=True)

    # ── Analysis cards grid ────────────────────────────────────────────────────
    # Two columns
    col_a, col_b = st.columns(2)

    for idx, analysis in enumerate(analyses):
        col = col_a if idx % 2 == 0 else col_b
        with col:
            _render_analysis_card(analysis, uid, idx)

    # Re-render after delete
    if st.session_state.get("history_delete_triggered"):
        st.session_state.history_delete_triggered = False
        st.session_state.history_cache = None
        st.session_state.history_loaded = False
        st.rerun()


def _render_analysis_card(analysis: dict, uid: str, idx: int):
    """Render a single analysis summary card."""
    from components.gauge import get_score_color

    name = analysis.get("startup_name", "Unnamed Startup")
    score = analysis.get("overall_investment_score", 0)
    rec = analysis.get("final_recommendation", "")
    conf = analysis.get("confidence_level", "")
    industry = analysis.get("industry", "")
    stage = analysis.get("funding_stage", "")
    created = analysis.get("created_at", "")
    doc_id = analysis.get("doc_id") or analysis.get("_doc_id", "")
    is_public = analysis.get("is_public", False)

    # Format date
    date_display = ""
    if created:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            date_display = dt.strftime("%b %d, %Y")
        except Exception:
            date_display = created[:10]

    score_col = get_score_color(score)

    # Pill
    rec_lower = rec.lower()
    if "invest" in rec_lower:
        pill_bg = "rgba(0,255,179,0.10)"
        pill_border = "rgba(0,255,179,0.35)"
        pill_color = "#00FFB3"
        pill_icon = "🟢"
    elif "consider" in rec_lower:
        pill_bg = "rgba(245,158,11,0.10)"
        pill_border = "rgba(245,158,11,0.35)"
        pill_color = "#F59E0B"
        pill_icon = "🟡"
    else:
        pill_bg = "rgba(255,69,96,0.10)"
        pill_border = "rgba(255,69,96,0.35)"
        pill_color = "#FF4560"
        pill_icon = "🔴"

    public_badge = """
    <span style="
        background:rgba(108,99,255,0.12);
        color:#6C63FF;
        border:1px solid rgba(108,99,255,0.3);
        border-radius:4px;
        font-size:0.6rem;
        padding:0.1rem 0.4rem;
        text-transform:uppercase;
        letter-spacing:0.08em;
        margin-left:0.4rem;
    ">🔗 Public</span>
    """ if is_public else ""

    st.markdown(f"""
    <div style="
        background:#0D1B2E;
        border:1px solid #1A2F4A;
        border-radius:12px;
        padding:1.2rem 1.4rem;
        margin-bottom:0.8rem;
        transition:border-color 0.2s;
        position:relative;
        overflow:hidden;
    ">
        <!-- Top accent line -->
        <div style="
            position:absolute; top:0; left:0; right:0;
            height:2px;
            background:linear-gradient(90deg, transparent, {score_col}, transparent);
        "></div>

        <!-- Name + public badge -->
        <div style="
            display:flex;
            justify-content:space-between;
            align-items:flex-start;
            margin-bottom:0.5rem;
        ">
            <div style="
                font-size:1rem; font-weight:700;
                color:#F0F6FF;
                font-family:'Space Grotesk', sans-serif;
            ">{name}{public_badge}</div>
            <div style="
                font-family:'JetBrains Mono', monospace;
                font-size:1.4rem;
                font-weight:500;
                color:{score_col};
                line-height:1;
            ">{score}</div>
        </div>

        <!-- Meta -->
        <div style="
            font-size:0.75rem; color:#7B92B2;
            margin-bottom:0.7rem;
        ">{industry}{'  ·  ' + stage if stage else ''}{'  ·  ' + date_display if date_display else ''}</div>

        <!-- Recommendation pill -->
        <div style="
            display:inline-flex;
            align-items:center;
            gap:0.3rem;
            background:{pill_bg};
            color:{pill_color};
            border:1px solid {pill_border};
            border-radius:999px;
            padding:0.25rem 0.8rem;
            font-size:0.72rem;
            font-weight:700;
            text-transform:uppercase;
            letter-spacing:0.06em;
        ">{pill_icon} {rec}</div>

        {'<span style="font-size:0.7rem; color:#3A4F6A; margin-left:0.6rem;">' + conf + ' Confidence</span>' if conf else ''}
    </div>
    """, unsafe_allow_html=True)

    # Buttons under card
    btn_col1, btn_col2, btn_col3 = st.columns([2, 1, 1])
    with btn_col1:
        if st.button(f"📊 View Report", key=f"view_{idx}_{doc_id}", use_container_width=True):
            st.session_state["view_analysis"] = analysis
            st.session_state["current_page"] = "analyze"
            st.session_state.history_loaded = False
            st.rerun()

    with btn_col2:
        if st.button(f"⚖️ Compare", key=f"cmp_{idx}_{doc_id}", use_container_width=True):
            st.session_state["compare_preload"] = analysis
            st.session_state["current_page"] = "compare"
            st.rerun()

    with btn_col3:
        if st.button(f"🗑️ Delete", key=f"del_{idx}_{doc_id}", use_container_width=True):
            if doc_id:
                from db.firestore import delete_analysis
                ok = delete_analysis(get_current_uid(), doc_id)
                if ok:
                    st.session_state.history_delete_triggered = True
                    st.rerun()
                else:
                    st.error("Delete failed.")


def _score_color(score: float) -> str:
    if score >= 70:
        return "#00FFB3"
    elif score >= 45:
        return "#F59E0B"
    else:
        return "#FF4560"