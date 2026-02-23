import streamlit as st

# ── PAGE CONFIG (must be first Streamlit call) ─────────────────────────────────
st.set_page_config(
    page_title="InvestIQ AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# ── IMPORTS ────────────────────────────────────────────────────────────────────
from styles.theme import apply_theme
from auth.firebase_auth import init_auth_state, is_logged_in, render_sidebar_user

# ── THEME ──────────────────────────────────────────────────────────────────────
apply_theme()

# ── AUTH STATE INIT ────────────────────────────────────────────────────────────
init_auth_state()

# ── SESSION STATE: CURRENT PAGE ────────────────────────────────────────────────
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"


# ── SIDEBAR NAV ────────────────────────────────────────────────────────────────
with st.sidebar:

    # Logo
    st.markdown("""
    <div style="padding:1rem 0 1.5rem 0;">
        <div style="
            font-family:'Space Grotesk',sans-serif;
            font-weight:700;
            font-size:1.4rem;
            color:#F0F6FF;
            letter-spacing:-0.02em;
        ">Invest<span style="
            background:linear-gradient(135deg,#00D4FF,#6C63FF);
            -webkit-background-clip:text;
            -webkit-text-fill-color:transparent;
        ">IQ</span> <span style="
            font-size:0.75rem;
            font-weight:500;
            color:#7B92B2;
            letter-spacing:0.15em;
            text-transform:uppercase;
        ">AI</span></div>
        <div style="
            font-size:0.7rem;
            color:#3A4F6A;
            letter-spacing:0.05em;
            margin-top:0.2rem;
        ">Investment Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr style="border-color:#1A2F4A; margin:0 0 1rem 0;">', unsafe_allow_html=True)

    # Navigation label
    st.markdown('<p style="color:#3A4F6A; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.12em; margin-bottom:0.5rem;">Navigation</p>', unsafe_allow_html=True)

    # Nav buttons
    if st.button("🏠  Home", use_container_width=True):
        st.session_state.current_page = "home"
        st.rerun()

    if st.button("🔍  Analyze Startup", use_container_width=True):
        st.session_state.current_page = "analyze"
        st.rerun()

    if is_logged_in():
        if st.button("📁  My Analyses", use_container_width=True):
            st.session_state.current_page = "history"
            st.rerun()

        if st.button("⚖️  Compare", use_container_width=True):
            st.session_state.current_page = "compare"
            st.rerun()

    st.markdown('<hr style="border-color:#1A2F4A; margin:1rem 0;">', unsafe_allow_html=True)

    # User info + logout
    if is_logged_in():
        render_sidebar_user(show_logout=True)
    else:
        st.markdown("""
        <div style="
            font-size:0.78rem;
            color:#7B92B2;
            background:#0D1B2E;
            border:1px solid #1A2F4A;
            border-radius:8px;
            padding:0.8rem;
            text-align:center;
        ">
            Sign in to save analyses,<br>compare startups & export PDFs
        </div>
        """, unsafe_allow_html=True)

    # Bottom branding
    st.markdown("""
    <div style="
        position:fixed;
        bottom:1.5rem;
        font-size:0.65rem;
        color:#3A4F6A;
        letter-spacing:0.05em;
    ">Powered by Groq · Gemini · Firebase</div>
    """, unsafe_allow_html=True)


# ── PAGE ROUTING ────────────────────────────────────────────────────────────────
page = st.session_state.current_page

# Handle shared link via URL query params
query_params = st.query_params
if "token" in query_params:
    page = "shared"

if page == "home":
    from pages.home import render_home
    render_home()

elif page == "analyze":
    from pages.analyze import render_analyze
    render_analyze()

elif page == "history":
    from pages.history import render_history
    render_history()

elif page == "compare":
    from pages.compare import render_compare
    render_compare()

elif page == "shared":
    from pages.shared import render_shared
    render_shared()

else:
    from pages.home import render_home
    render_home()