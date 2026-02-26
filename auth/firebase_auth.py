import streamlit as st
import pyrebase
from typing import Optional


# ── FIREBASE INIT ──────────────────────────────────────────────────────────────

def get_firebase():
    """Initialize and return Firebase app."""
    config = {
        "apiKey": st.secrets["firebase"]["apiKey"],
        "authDomain": st.secrets["firebase"]["authDomain"],
        "projectId": st.secrets["firebase"]["projectId"],
        "storageBucket": st.secrets["firebase"]["storageBucket"],
        "messagingSenderId": st.secrets["firebase"]["messagingSenderId"],
        "appId": st.secrets["firebase"]["appId"],
        "databaseURL": st.secrets["firebase"].get("databaseURL", ""),
    }
    firebase = pyrebase.initialize_app(config)
    return firebase


def get_auth():
    """Return Firebase Auth instance."""
    return get_firebase().auth()


# ── SESSION STATE HELPERS ──────────────────────────────────────────────────────

def init_auth_state():
    """Initialize auth-related session state keys."""
    if "user" not in st.session_state:
        st.session_state.user = None
    if "id_token" not in st.session_state:
        st.session_state.id_token = None
    if "user_email" not in st.session_state:
        st.session_state.user_email = None
    if "user_uid" not in st.session_state:
        st.session_state.user_uid = None
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"  # "login" or "signup"


def is_logged_in() -> bool:
    """Check if a user is currently logged in."""
    return st.session_state.get("user") is not None


def get_current_uid() -> Optional[str]:
    """Return current user's Firebase UID."""
    return st.session_state.get("user_uid")


def get_current_email() -> Optional[str]:
    """Return current user's email."""
    return st.session_state.get("user_email")


def get_id_token() -> Optional[str]:
    """Return current user's ID token."""
    return st.session_state.get("id_token")


# ── AUTH ACTIONS ───────────────────────────────────────────────────────────────

def login_with_email(email: str, password: str) -> dict:
    """
    Attempt email/password login.
    Returns: {"success": bool, "message": str}
    """
    try:
        auth = get_auth()
        user = auth.sign_in_with_email_and_password(email, password)
        _set_session(user)
        return {"success": True, "message": "Login successful."}
    except Exception as e:
        error_msg = _parse_firebase_error(str(e))
        return {"success": False, "message": error_msg}


def signup_with_email(email: str, password: str) -> dict:
    """
    Create new account with email/password.
    Returns: {"success": bool, "message": str}
    """
    try:
        auth = get_auth()
        user = auth.create_user_with_email_and_password(email, password)
        _set_session(user)
        return {"success": True, "message": "Account created successfully."}
    except Exception as e:
        error_msg = _parse_firebase_error(str(e))
        return {"success": False, "message": error_msg}


def logout():
    """Clear all session state and log out."""
    st.session_state.user = None
    st.session_state.id_token = None
    st.session_state.user_email = None
    st.session_state.user_uid = None
    # Clear any cached analysis data
    for key in ["last_analysis", "analysis_result", "current_page"]:
        if key in st.session_state:
            del st.session_state[key]


def refresh_token() -> bool:
    """
    Attempt to refresh user's ID token.
    Returns True if successful.
    """
    try:
        auth = get_auth()
        refresh = st.session_state.get("user", {}).get("refreshToken")
        if not refresh:
            return False
        user = auth.refresh(refresh)
        st.session_state.id_token = user["idToken"]
        st.session_state.user["idToken"] = user["idToken"]
        return True
    except Exception:
        return False


# ── PRIVATE HELPERS ────────────────────────────────────────────────────────────

def _set_session(user: dict):
    """Store Firebase user data in session state."""
    st.session_state.user      = user
    st.session_state.id_token  = user.get("idToken")
    st.session_state.user_email = user.get("email")
    st.session_state.user_uid  = user.get("localId")
    # Register user in admin-visible registry immediately on login/signup
    try:
        _register_user_in_registry(
            uid=user.get("localId",""),
            email=user.get("email",""),
            token=user.get("idToken",""),
        )
    except Exception:
        pass  # Never block login if registry write fails


def _register_user_in_registry(uid: str, email: str, token: str):
    """
    Write /users/{uid} profile doc + /platform_stats/{uid} doc.
    This makes the user discoverable by the admin dashboard immediately
    after login — even before they save any analysis.
    """
    if not uid or not token:
        return

    import requests, json
    from datetime import datetime, timezone

    project = st.secrets["firebase"]["projectId"]
    base    = f"https://firestore.googleapis.com/v1/projects/{project}/databases/(default)/documents"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    now_iso = datetime.now(timezone.utc).isoformat()

    def to_val(v):
        if v is None:          return {"nullValue": None}
        if isinstance(v, bool):return {"booleanValue": v}
        if isinstance(v, int): return {"integerValue": str(v)}
        if isinstance(v, str): return {"stringValue": v}
        return {"stringValue": str(v)}

    # 1. Write /users/{uid} — creates the parent doc so admin can enumerate /users
    user_doc = {"fields": {
        "uid":        to_val(uid),
        "email":      to_val(email),
        "joined_at":  to_val(now_iso),
        "last_login": to_val(now_iso),
        "active":     to_val(True),
    }}
    try:
        requests.patch(
            f"{base}/users/{uid}",
            headers=headers,
            data=json.dumps(user_doc),
            params={"updateMask.fieldPaths": ["uid","email","last_login","active"]},
            timeout=6,
        )
    except Exception:
        pass

    # 2. Write /platform_stats/{uid} — admin stats registry
    stats_doc = {"fields": {
        "uid":            to_val(uid),
        "email":          to_val(email),
        "last_login":     to_val(now_iso),
        "total_analyses": to_val(0),
    }}
    try:
        # Only set total_analyses if not already set (don't overwrite existing count)
        requests.patch(
            f"{base}/platform_stats/{uid}",
            headers=headers,
            data=json.dumps(stats_doc),
            params={"updateMask.fieldPaths": ["uid","email","last_login"]},
            timeout=6,
        )
    except Exception:
        pass


def _parse_firebase_error(error_str: str) -> str:
    """Convert Firebase error strings to human-readable messages."""
    error_map = {
        "EMAIL_NOT_FOUND": "No account found with this email.",
        "INVALID_PASSWORD": "Incorrect password. Please try again.",
        "USER_DISABLED": "This account has been disabled.",
        "EMAIL_EXISTS": "An account with this email already exists.",
        "WEAK_PASSWORD": "Password must be at least 6 characters.",
        "INVALID_EMAIL": "Please enter a valid email address.",
        "TOO_MANY_ATTEMPTS_TRY_LATER": "Too many attempts. Please try again later.",
        "INVALID_LOGIN_CREDENTIALS": "Invalid email or password.",
    }
    for key, msg in error_map.items():
        if key in error_str:
            return msg
    return "Authentication failed. Please try again."


# ── UI COMPONENTS ──────────────────────────────────────────────────────────────

def render_auth_modal():
    """
    Render the full login/signup form.
    Call this when a protected page needs authentication.
    """
    st.markdown("""
    <div style="
        max-width: 440px;
        margin: 3rem auto;
        background: #0D1B2E;
        border: 1px solid #1A2F4A;
        border-radius: 16px;
        padding: 2.5rem;
    ">
        <div style="text-align:center; margin-bottom:2rem;">
            <div style="
                font-family:'Space Grotesk',sans-serif;
                font-weight:700;
                font-size:1.6rem;
                color:#F0F6FF;
                letter-spacing:-0.02em;
                margin-bottom:0.4rem;
            ">Invest<span style="
                background:linear-gradient(135deg,#00D4FF,#6C63FF);
                -webkit-background-clip:text;
                -webkit-text-fill-color:transparent;
            ">IQ</span> AI</div>
            <div style="color:#7B92B2; font-size:0.85rem;">
                Investment Intelligence Platform
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Toggle between login and signup
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Sign In", use_container_width=True,
                     type="primary" if st.session_state.auth_mode == "login" else "secondary"):
            st.session_state.auth_mode = "login"
            st.rerun()
    with col2:
        if st.button("Create Account", use_container_width=True,
                     type="primary" if st.session_state.auth_mode == "signup" else "secondary"):
            st.session_state.auth_mode = "signup"
            st.rerun()

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    if st.session_state.auth_mode == "login":
        _render_login_form()
    else:
        _render_signup_form()


def _render_login_form():
    """Render email/password login form."""
    with st.form("login_form", clear_on_submit=False):
        st.markdown("""
        <p style='color:#7B92B2; font-size:0.8rem; font-weight:600;
           text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.3rem;'>
           Email Address
        </p>
        """, unsafe_allow_html=True)
        email = st.text_input(
            "Email",
            placeholder="you@example.com",
            label_visibility="collapsed"
        )

        st.markdown("""
        <p style='color:#7B92B2; font-size:0.8rem; font-weight:600;
           text-transform:uppercase; letter-spacing:0.08em;
           margin-bottom:0.3rem; margin-top:0.8rem;'>
           Password
        </p>
        """, unsafe_allow_html=True)
        password = st.text_input(
            "Password",
            type="password",
            placeholder="••••••••",
            label_visibility="collapsed"
        )

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Sign In →", use_container_width=True)

        if submitted:
            if not email or not password:
                st.error("Please enter your email and password.")
            else:
                with st.spinner("Signing in..."):
                    result = login_with_email(email, password)
                if result["success"]:
                    st.success("Welcome back!")
                    st.rerun()
                else:
                    st.error(result["message"])


def _render_signup_form():
    """Render email/password signup form."""
    with st.form("signup_form", clear_on_submit=False):
        st.markdown("""
        <p style='color:#7B92B2; font-size:0.8rem; font-weight:600;
           text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.3rem;'>
           Email Address
        </p>
        """, unsafe_allow_html=True)
        email = st.text_input(
            "Email",
            placeholder="you@example.com",
            label_visibility="collapsed"
        )

        st.markdown("""
        <p style='color:#7B92B2; font-size:0.8rem; font-weight:600;
           text-transform:uppercase; letter-spacing:0.08em;
           margin-bottom:0.3rem; margin-top:0.8rem;'>
           Password
        </p>
        """, unsafe_allow_html=True)
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Min. 6 characters",
            label_visibility="collapsed"
        )

        st.markdown("""
        <p style='color:#7B92B2; font-size:0.8rem; font-weight:600;
           text-transform:uppercase; letter-spacing:0.08em;
           margin-bottom:0.3rem; margin-top:0.8rem;'>
           Confirm Password
        </p>
        """, unsafe_allow_html=True)
        confirm = st.text_input(
            "Confirm",
            type="password",
            placeholder="Re-enter password",
            label_visibility="collapsed"
        )

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Create Account →", use_container_width=True)

        if submitted:
            if not email or not password or not confirm:
                st.error("Please fill in all fields.")
            elif password != confirm:
                st.error("Passwords do not match.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                with st.spinner("Creating your account..."):
                    result = signup_with_email(email, password)
                if result["success"]:
                    st.success("Account created! Welcome to InvestIQ AI.")
                    st.rerun()
                else:
                    st.error(result["message"])


def render_sidebar_user(show_logout: bool = True):
    """
    Render user info + logout button in sidebar.
    Call this from the sidebar section of any page.
    """
    if not is_logged_in():
        return

    email = get_current_email() or "User"
    short_email = email[:22] + "..." if len(email) > 25 else email

    st.sidebar.markdown(f"""
    <div style="
        background: #102035;
        border: 1px solid #1A2F4A;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
    ">
        <div style="
            font-size:0.65rem;
            color:#7B92B2;
            text-transform:uppercase;
            letter-spacing:0.1em;
            margin-bottom:0.2rem;
        ">Signed in as</div>
        <div style="
            font-size:0.85rem;
            font-weight:600;
            color:#F0F6FF;
            word-break:break-all;
        ">{short_email}</div>
    </div>
    """, unsafe_allow_html=True)

    if show_logout:
        if st.sidebar.button("↩ Sign Out", use_container_width=True):
            logout()
            st.rerun()
