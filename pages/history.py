"""
InvestIQ AI — History Page
Displays all saved analyses for the logged-in user.
"""

import streamlit as st
from styles.theme import apply_theme
from auth.firebase_auth import is_logged_in, render_auth_modal, get_current_uid


def render_history():
    apply_theme()

    st.markdown(
        '<div class="page-header">'
        '<h1>📁 My Analyses</h1>'
        '<p>All your saved investment analyses — click any card to view the full report.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    if not is_logged_in():
        render_auth_modal()
        return

    uid = get_current_uid()

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
        st.markdown(
            '<div style="text-align:center;padding:4rem 2rem;background:#0D1B2E;'
            'border:1px dashed #1A2F4A;border-radius:14px;margin-top:1rem;">'
            '<div style="font-size:2.5rem;margin-bottom:1rem;">📭</div>'
            '<div style="font-size:1.1rem;font-weight:700;color:#F0F6FF;'
            'margin-bottom:0.5rem;font-family:\'Space Grotesk\',sans-serif;">No analyses yet</div>'
            '<div style="font-size:0.85rem;color:#7B92B2;">'
            'Run your first startup analysis to see it here.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        col_l, col_c, col_r = st.columns([1.5, 2, 1.5])
        with col_c:
            if st.button("🔍  Analyze a Startup →", use_container_width=True):
                st.session_state.current_page = "analyze"
                st.rerun()
        return

    # ── Summary stats ──────────────────────────────────────────────────────────
    total = len(analyses)
    avg_score = round(
        sum(a.get("overall_investment_score", 0) for a in analyses) / total
    ) if total else 0
    invest_count = sum(
        1 for a in analyses
        if "invest" in a.get("final_recommendation", "").lower()
    )

    c1, c2, c3 = st.columns(3)
    for col, label, value, color in [
        (c1, "Total Analyses", str(total),           "#00D4FF"),
        (c2, "Avg Score",      f"{avg_score}/100",   _score_color(avg_score)),
        (c3, "Strong Invest",  str(invest_count),     "#00FFB3"),
    ]:
        with col:
            st.markdown(
                f'<div style="background:#0D1B2E;border:1px solid #1A2F4A;'
                f'border-radius:10px;padding:1rem;text-align:center;margin-bottom:1rem;">'
                f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:1.8rem;'
                f'font-weight:500;color:{color};">{value}</div>'
                f'<div style="font-size:0.68rem;color:#7B92B2;text-transform:uppercase;'
                f'letter-spacing:0.1em;margin-top:0.2rem;">{label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div style="height:1px;'
        'background:linear-gradient(90deg,transparent,#1A2F4A,transparent);'
        'margin:0.5rem 0 1.5rem 0;"></div>',
        unsafe_allow_html=True,
    )

    # ── Cards grid ─────────────────────────────────────────────────────────────
    col_a, col_b = st.columns(2)
    for idx, analysis in enumerate(analyses):
        col = col_a if idx % 2 == 0 else col_b
        with col:
            _render_analysis_card(analysis, uid, idx)

    if st.session_state.get("history_delete_triggered"):
        st.session_state.history_delete_triggered = False
        st.session_state.history_cache = None
        st.session_state.history_loaded = False
        st.rerun()


# ── CARD ───────────────────────────────────────────────────────────────────────

def _render_analysis_card(analysis: dict, uid: str, idx: int):
    from components.gauge import get_score_color

    name      = analysis.get("startup_name", "Unnamed Startup")
    score     = analysis.get("overall_investment_score", 0)
    rec       = analysis.get("final_recommendation", "")
    conf      = analysis.get("confidence_level", "")
    industry  = analysis.get("industry", "")
    stage     = analysis.get("funding_stage", "")
    created   = analysis.get("created_at", "")
    doc_id    = analysis.get("doc_id") or analysis.get("_doc_id", "")
    is_public = analysis.get("is_public", False)

    # Date
    date_display = ""
    if created:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            date_display = dt.strftime("%b %d, %Y")
        except Exception:
            date_display = created[:10]

    score_col = get_score_color(score)

    # Recommendation pill colours
    rec_lower = rec.lower()
    if "invest" in rec_lower:
        pill_bg, pill_border, pill_color, pill_icon = (
            "rgba(0,255,179,0.10)", "rgba(0,255,179,0.35)", "#00FFB3", "🟢")
    elif "consider" in rec_lower:
        pill_bg, pill_border, pill_color, pill_icon = (
            "rgba(245,158,11,0.10)", "rgba(245,158,11,0.35)", "#F59E0B", "🟡")
    else:
        pill_bg, pill_border, pill_color, pill_icon = (
            "rgba(255,69,96,0.10)", "rgba(255,69,96,0.35)", "#FF4560", "🔴")

    # Public badge (no HTML comments)
    public_badge = (
        '<span style="background:rgba(108,99,255,0.12);color:#6C63FF;'
        'border:1px solid rgba(108,99,255,0.3);border-radius:4px;'
        'font-size:0.6rem;padding:0.1rem 0.4rem;text-transform:uppercase;'
        'letter-spacing:0.08em;margin-left:0.4rem;">🔗 Public</span>'
        if is_public else ""
    )

    # Meta line
    meta_parts = [p for p in [industry, stage, date_display] if p]
    meta_str = "  ·  ".join(meta_parts)

    # Confidence suffix
    conf_html = (
        f'<span style="font-size:0.7rem;color:#3A4F6A;margin-left:0.6rem;">'
        f'{conf} Confidence</span>'
        if conf else ""
    )

    # Top accent bar (no comments — just the element)
    accent = (
        f'<div style="position:absolute;top:0;left:0;right:0;height:2px;'
        f'background:linear-gradient(90deg,transparent,{score_col},transparent);"></div>'
    )

    st.markdown(
        f'<div style="background:#0D1B2E;border:1px solid #1A2F4A;border-radius:12px;'
        f'padding:1.2rem 1.4rem;margin-bottom:0.8rem;position:relative;overflow:hidden;">'
        + accent
        + f'<div style="display:flex;justify-content:space-between;align-items:flex-start;'
        f'margin-bottom:0.5rem;">'
        f'<div style="font-size:1rem;font-weight:700;color:#F0F6FF;'
        f'font-family:\'Space Grotesk\',sans-serif;">{name}{public_badge}</div>'
        f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:1.4rem;'
        f'font-weight:500;color:{score_col};line-height:1;">{score}</div>'
        f'</div>'
        f'<div style="font-size:0.75rem;color:#7B92B2;margin-bottom:0.7rem;">{meta_str}</div>'
        f'<div style="display:inline-flex;align-items:center;gap:0.3rem;'
        f'background:{pill_bg};color:{pill_color};border:1px solid {pill_border};'
        f'border-radius:999px;padding:0.25rem 0.8rem;font-size:0.72rem;font-weight:700;'
        f'text-transform:uppercase;letter-spacing:0.06em;">{pill_icon} {rec}</div>'
        + conf_html
        + '</div>',
        unsafe_allow_html=True,
    )

    # Action buttons
    btn1, btn2, btn3 = st.columns([2, 1, 1])
    with btn1:
        if st.button("📊 View Report", key=f"view_{idx}_{doc_id}",
                     use_container_width=True):
            st.session_state["view_analysis"] = analysis
            st.session_state["current_page"] = "analyze"
            st.session_state.history_loaded = False
            st.rerun()
    with btn2:
        if st.button("⚖️ Compare", key=f"cmp_{idx}_{doc_id}",
                     use_container_width=True):
            st.session_state["compare_preload"] = analysis
            st.session_state["current_page"] = "compare"
            st.rerun()
    with btn3:
        if st.button("🗑️ Delete", key=f"del_{idx}_{doc_id}",
                     use_container_width=True):
            if doc_id:
                from db.firestore import delete_analysis
                ok = delete_analysis(get_current_uid(), doc_id)
                if ok:
                    st.session_state.history_delete_triggered = True
                    st.rerun()
                else:
                    st.error("Delete failed.")


# ── HELPERS ────────────────────────────────────────────────────────────────────

def _score_color(score: float) -> str:
    if score >= 70:
        return "#00FFB3"
    elif score >= 45:
        return "#F59E0B"
    return "#FF4560"
