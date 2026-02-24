"""
InvestIQ AI — Analyze Page

Sections:
  A. Model Selector (provider + model dropdowns)
  B. Input Form (requires login)
  C. Agent Loading Animation (while pipeline runs)
  D. Full Results Dashboard
  E. Action Bar (Save, PDF, Share, New Analysis)
"""

import streamlit as st
from styles.theme import apply_theme
from auth.firebase_auth import is_logged_in, render_auth_modal, get_current_uid
from ai.agents import GROQ_MODELS, GEMINI_MODELS, DEFAULT_CONFIG


# ── FORM OPTIONS ───────────────────────────────────────────────────────────────

INDUSTRIES = [
    "AI / Machine Learning", "FinTech", "HealthTech", "EdTech",
    "E-Commerce", "SaaS / Enterprise Software", "CleanTech / GreenTech",
    "DeepTech", "Marketplace", "Consumer App", "BioTech", "SpaceTech",
    "AgriTech", "LegalTech", "PropTech", "Gaming", "Creator Economy", "Other",
]

BUSINESS_MODELS = [
    "B2B (Business to Business)", "B2C (Business to Consumer)", "B2B2C",
    "Marketplace / Platform", "D2C (Direct to Consumer)",
    "API / Developer Platform", "Franchise", "Other",
]

REVENUE_MODELS = [
    "SaaS Subscription", "Usage-Based / Metered", "Transaction Fee / Commission",
    "Freemium", "Licensing", "Advertising", "Hardware + Software",
    "Consulting / Services", "Other",
]

FUNDING_STAGES = [
    "Idea / Pre-Product", "Pre-Seed", "Seed",
    "Series A", "Series B+", "Bootstrapped / Revenue-Stage",
]


# ── MAIN RENDER ────────────────────────────────────────────────────────────────

def render_analyze():
    apply_theme()

    if st.session_state.get("view_analysis"):
        result = st.session_state.pop("view_analysis")
        _render_dashboard(result, from_history=True)
        return

    if st.session_state.get("analysis_complete") and st.session_state.get("analysis_result"):
        _render_dashboard(st.session_state["analysis_result"])
        return

    _render_form()


# ── MODEL SELECTOR ─────────────────────────────────────────────────────────────

def _render_model_selector() -> dict:
    """Renders the AI model config panel. Returns model_config dict."""

    st.markdown("""
    <div style="
        background:#0D1B2E;
        border:1px solid #1A2F4A;
        border-left:3px solid #00D4FF;
        border-radius:12px;
        padding:0.9rem 1.4rem 0.5rem 1.4rem;
        margin-bottom:1.1rem;
    ">
        <div style="
            font-size:0.62rem;
            color:#00D4FF;
            text-transform:uppercase;
            letter-spacing:0.18em;
            font-weight:700;
            margin-bottom:0.7rem;
        ">🤖 AI MODEL CONFIGURATION</div>
    </div>
    """, unsafe_allow_html=True)

    col_prov, col_model, col_synth = st.columns([1, 1.8, 1.4])

    with col_prov:
        st.markdown('<div style="font-size:0.68rem;color:#7B92B2;text-transform:uppercase;'
                    'letter-spacing:0.1em;font-weight:600;margin-bottom:0.3rem;">Provider</div>',
                    unsafe_allow_html=True)
        provider = st.selectbox(
            "Provider", ["groq", "gemini"],
            index=0,
            format_func=lambda x: "⚡ Groq" if x == "groq" else "🔵 Gemini",
            label_visibility="collapsed",
            key="sel_provider",
        )

    with col_model:
        st.markdown('<div style="font-size:0.68rem;color:#7B92B2;text-transform:uppercase;'
                    'letter-spacing:0.1em;font-weight:600;margin-bottom:0.3rem;">'
                    'Model — Agents 1–5</div>', unsafe_allow_html=True)
        if provider == "groq":
            groq_keys = list(GROQ_MODELS.keys())
            sel_groq = st.selectbox(
                "Groq Model", groq_keys, index=0,
                format_func=lambda x: GROQ_MODELS[x],
                label_visibility="collapsed", key="sel_groq",
            )
            sel_gemini = list(GEMINI_MODELS.keys())[0]
        else:
            gemini_keys = list(GEMINI_MODELS.keys())
            sel_gemini = st.selectbox(
                "Gemini Model", gemini_keys, index=0,
                format_func=lambda x: GEMINI_MODELS[x],
                label_visibility="collapsed", key="sel_gemini",
            )
            sel_groq = list(GROQ_MODELS.keys())[0]

    with col_synth:
        st.markdown('<div style="font-size:0.68rem;color:#7B92B2;text-transform:uppercase;'
                    'letter-spacing:0.1em;font-weight:600;margin-bottom:0.3rem;">'
                    'Synthesizer — Agent 6</div>', unsafe_allow_html=True)
        synthesizer = st.selectbox(
            "Synthesizer", ["gemini", "groq"],
            index=0,
            format_func=lambda x: "🔵 Gemini (Best)" if x == "gemini" else "⚡ Groq (Faster)",
            label_visibility="collapsed", key="sel_synth",
        )

    # Summary chips
    if provider == "groq":
        a_label = GROQ_MODELS.get(sel_groq, sel_groq).split("·")[0].strip().replace("⚡", "").strip()
        risk_chip = "Agent 4 Risk: DeepSeek R1 (auto)"
    else:
        a_label = GEMINI_MODELS.get(sel_gemini, sel_gemini).split("·")[0].strip().replace("⚡", "").strip()
        risk_chip = f"Agent 4 Risk: {a_label}"

    synth_chip = (
        GEMINI_MODELS.get(sel_gemini, sel_gemini).split("·")[0].strip().replace("⚡", "").strip()
        if synthesizer == "gemini"
        else GROQ_MODELS.get(sel_groq, sel_groq).split("·")[0].strip().replace("⚡", "").strip()
    )

    st.markdown(f"""
    <div style="display:flex;gap:0.5rem;flex-wrap:wrap;margin:0.5rem 0 0.3rem 0;">
        <span style="background:rgba(0,212,255,0.08);border:1px solid rgba(0,212,255,0.2);
            border-radius:5px;padding:0.15rem 0.6rem;font-size:0.66rem;color:#00D4FF;">
            ⚡ Agents 1–5: {a_label}</span>
        <span style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.2);
            border-radius:5px;padding:0.15rem 0.6rem;font-size:0.66rem;color:#F59E0B;">
            🧠 {risk_chip}</span>
        <span style="background:rgba(108,99,255,0.08);border:1px solid rgba(108,99,255,0.2);
            border-radius:5px;padding:0.15rem 0.6rem;font-size:0.66rem;color:#6C63FF;">
            🏛️ Synthesizer: {synth_chip}</span>
    </div>
    """, unsafe_allow_html=True)

    return {
        "provider":     provider,
        "groq_model":   sel_groq,
        "gemini_model": sel_gemini,
        "synthesizer":  synthesizer,
    }


# ── INPUT FORM ─────────────────────────────────────────────────────────────────

def _render_form():
    st.markdown("""
    <div class="page-header">
        <h1>🔍 Analyze a Startup</h1>
        <p>Fill in the details below — 6 AI agents will evaluate the investment opportunity.</p>
    </div>
    """, unsafe_allow_html=True)

    if not is_logged_in():
        st.markdown("""
        <div style="background:rgba(0,212,255,0.06);border:1px solid rgba(0,212,255,0.25);
            border-radius:10px;padding:1rem 1.2rem;margin-bottom:1.5rem;
            font-size:0.88rem;color:#7B92B2;">
            🔒 Sign in to run analyses, save results, and export PDF reports.
            You can view the demo on the <b style="color:#00D4FF;">Home</b> page without signing in.
        </div>
        """, unsafe_allow_html=True)
        render_auth_modal()
        return

    # Model selector lives OUTSIDE the form so dropdowns respond instantly
    model_config = _render_model_selector()

    st.markdown("""
    <div style="height:1px;background:linear-gradient(90deg,transparent,#1A2F4A,transparent);
        margin:0.8rem 0 1rem 0;"></div>
    """, unsafe_allow_html=True)

    # ── FORM ──────────────────────────────────────────────────────────────────
    with st.form("analysis_form", clear_on_submit=False):

        col1, col2 = st.columns([1.2, 1])
        with col1:
            startup_name = st.text_input(
                "Startup Name", placeholder="e.g. MediMatch AI",
                help="The name of the startup or idea you want to evaluate.",
            )
        with col2:
            industry = st.selectbox("Industry", INDUSTRIES)

        description = st.text_area(
            "Startup Description",
            placeholder=(
                "Describe what the startup does, what problem it solves, "
                "who the customer is, and what makes it different. "
                "More detail = better analysis. (min 50 characters)"
            ),
            height=130, max_chars=800,
        )

        char_count = len(description)
        char_color = "#00FFB3" if char_count >= 100 else "#F59E0B" if char_count >= 50 else "#FF4560"
        st.markdown(f"""
        <div style="text-align:right;font-size:0.72rem;color:{char_color};
            margin-top:-0.8rem;margin-bottom:0.5rem;">{char_count}/800</div>
        """, unsafe_allow_html=True)

        col3, col4 = st.columns(2)
        with col3:
            target_market = st.text_input(
                "Target Market",
                placeholder="e.g. Pharma companies & CROs in the US and EU",
            )
        with col4:
            business_model = st.selectbox("Business Model", BUSINESS_MODELS)

        col5, col6 = st.columns(2)
        with col5:
            revenue_model = st.selectbox("Revenue Model", REVENUE_MODELS)
        with col6:
            funding_stage = st.selectbox("Funding Stage", FUNDING_STAGES)

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        submitted = st.form_submit_button(
            "🚀  Run Investment Analysis →",
            use_container_width=True, type="primary",
        )

    # ── VALIDATION + PIPELINE ─────────────────────────────────────────────────
    if submitted:
        errors = []
        if not startup_name.strip():
            errors.append("Startup Name is required.")
        if len(description.strip()) < 50:
            errors.append("Description must be at least 50 characters.")
        if not target_market.strip():
            errors.append("Target Market is required.")

        if errors:
            for err in errors:
                st.error(err)
        else:
            startup_data = {
                "startup_name":   startup_name.strip(),
                "description":    description.strip(),
                "industry":       industry,
                "target_market":  target_market.strip(),
                "business_model": business_model,
                "revenue_model":  revenue_model,
                "funding_stage":  funding_stage,
            }
            st.session_state["model_config"] = model_config

            from components.agent_loader import run_pipeline_with_loader
            result = run_pipeline_with_loader(startup_data, model_config=model_config)

            st.session_state["analysis_result"] = result
            st.session_state["analysis_complete"] = True
            st.session_state["analysis_saved"] = False
            st.rerun()


# ── RESULTS DASHBOARD ──────────────────────────────────────────────────────────

def _render_dashboard(result: dict, from_history: bool = False):
    from components.gauge import render_score_hero
    from components.radar import render_radar, render_score_bar_chart
    from components.score_cards import (
        render_four_score_cards, render_innovation_card,
        render_strengths_weaknesses, render_recommended_actions,
        render_executive_summary, render_agent_deep_dive,
    )

    startup_name = result.get("startup_name", "Startup")
    cfg = st.session_state.get("model_config", DEFAULT_CONFIG)

    # Build model tag for header
    if cfg.get("provider") == "groq":
        m_label = GROQ_MODELS.get(cfg.get("groq_model", ""), "").split("·")[0].replace("⚡","").strip()
        model_tag = f"⚡ Groq · {m_label}"
    else:
        m_label = GEMINI_MODELS.get(cfg.get("gemini_model", ""), "").split("·")[0].replace("⚡","").strip()
        model_tag = f"🔵 Gemini · {m_label}"

    st.markdown(f"""
    <div class="page-header">
        <h1>📊 {startup_name}</h1>
        <p>
            {result.get('industry', '')}
            {'  ·  ' + result.get('funding_stage','') if result.get('funding_stage') else ''}
            {'  ·  ' + result.get('business_model','') if result.get('business_model') else ''}
            <span style="margin-left:0.6rem;background:rgba(0,212,255,0.08);
                border:1px solid rgba(0,212,255,0.2);border-radius:5px;
                padding:0.1rem 0.5rem;font-size:0.68rem;color:#00D4FF;">{model_tag}</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_gauge, col_right = st.columns([1.2, 1])
    with col_gauge:
        render_score_hero(result)
    with col_right:
        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
        render_innovation_card(result)
        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
        render_score_bar_chart(result, height=220)

    _divider()
    render_four_score_cards(result)
    _divider()

    col_radar, col_sw = st.columns([1, 1.2])
    with col_radar:
        st.markdown("""
        <div style="font-size:0.65rem;color:#3A4F6A;text-transform:uppercase;
            letter-spacing:0.15em;font-weight:600;margin-bottom:0.5rem;text-align:center;">
        5-DIMENSION RADAR</div>
        """, unsafe_allow_html=True)
        render_radar(result)
    with col_sw:
        render_strengths_weaknesses(result)

    _divider()
    render_recommended_actions(result)
    _divider()
    render_executive_summary(result)
    _divider()

    st.markdown("""
    <div style="font-size:0.65rem;color:#3A4F6A;text-transform:uppercase;
        letter-spacing:0.18em;font-weight:600;margin-bottom:0.8rem;">
    AGENT DEEP DIVE — FULL ANALYSES</div>
    """, unsafe_allow_html=True)
    render_agent_deep_dive(result)
    _divider()
    _render_action_bar(result, from_history)


# ── ACTION BAR ────────────────────────────────────────────────────────────────

def _render_action_bar(result: dict, from_history: bool = False):
    from components.pdf_export import render_pdf_download_button
    from db.firestore import save_analysis, make_analysis_public

    st.markdown("""
    <div style="background:#0D1B2E;border:1px solid #1A2F4A;border-radius:12px;
        padding:1.2rem 1.5rem;margin-top:0.5rem;">
        <div style="font-size:0.65rem;color:#3A4F6A;text-transform:uppercase;
            letter-spacing:0.15em;font-weight:600;margin-bottom:1rem;">ACTIONS</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if is_logged_in() and not from_history:
            already_saved = st.session_state.get("analysis_saved", False)
            saved_id = st.session_state.get("saved_doc_id")
            if already_saved and saved_id:
                st.markdown("""<div style="text-align:center;font-size:0.8rem;
                    color:#00FFB3;padding:0.5rem;">✅ Saved</div>""",
                    unsafe_allow_html=True)
            else:
                if st.button("💾  Save Analysis", use_container_width=True):
                    uid = get_current_uid()
                    with st.spinner("Saving..."):
                        doc_id = save_analysis(uid, result)
                    if doc_id:
                        st.session_state["analysis_saved"] = True
                        st.session_state["saved_doc_id"] = doc_id
                        st.success("Saved!")
                        st.rerun()
                    else:
                        st.error("Save failed. Check Firestore rules.")
        else:
            st.markdown("""<div style="text-align:center;font-size:0.75rem;
                color:#3A4F6A;padding:0.5rem;">Sign in to save</div>""",
                unsafe_allow_html=True)

    with col2:
        render_pdf_download_button(result)

    with col3:
        if is_logged_in():
            saved_id = st.session_state.get("saved_doc_id")
            if saved_id:
                if st.button("🔗  Share Link", use_container_width=True):
                    uid = get_current_uid()
                    with st.spinner("Generating link..."):
                        public_token = make_analysis_public(uid, saved_id)
                    if public_token:
                        base = st.secrets.get("app", {}).get("base_url", "")
                        st.session_state["share_url"] = f"{base}?token={public_token}"
                        st.rerun()
                    else:
                        st.error("Could not generate share link.")
                share_url = st.session_state.get("share_url", "")
                if share_url:
                    st.code(share_url, language=None)
            else:
                st.markdown("""<div style="text-align:center;font-size:0.75rem;
                    color:#3A4F6A;padding:0.5rem;">Save first to share</div>""",
                    unsafe_allow_html=True)
        else:
            st.markdown("""<div style="text-align:center;font-size:0.75rem;
                color:#3A4F6A;padding:0.5rem;">Sign in to share</div>""",
                unsafe_allow_html=True)

    with col4:
        if st.button("🔄  New Analysis", use_container_width=True):
            for key in ["analysis_result", "analysis_complete",
                        "analysis_saved", "saved_doc_id", "share_url", "model_config"]:
                st.session_state.pop(key, None)
            st.rerun()

    errors = result.get("pipeline_errors", [])
    if errors:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        with st.expander("⚠️ Pipeline Warnings", expanded=False):
            for err in errors:
                st.markdown(f"""<div style="font-size:0.78rem;color:#F59E0B;padding:0.3rem 0;">
                    Agent <b>{err.get('agent')}</b>: {err.get('error','')[:150]}</div>""",
                    unsafe_allow_html=True)


# ── HELPERS ────────────────────────────────────────────────────────────────────

def _divider():
    st.markdown("""
    <div style="height:1px;
        background:linear-gradient(90deg,transparent,#1A2F4A,transparent);
        margin:1.8rem 0;"></div>
    """, unsafe_allow_html=True)
