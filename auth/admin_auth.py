"""
InvestIQ AI — Admin Role-Based Access Control

Admin UIDs are stored in secrets.toml under [admin] section:
  [admin]
  uids = ["uid1", "uid2"]

This is the single source of truth for admin access.
No Firestore writes needed — purely config-based, zero attack surface.
"""

import streamlit as st
from auth.firebase_auth import is_logged_in, get_current_uid, get_current_email


# ── ROLE CHECK ────────────────────────────────────────────────────────────────

def get_admin_uids() -> list:
    """Return list of admin UIDs from secrets.toml."""
    try:
        raw = st.secrets.get("admin", {}).get("uids", [])
        if isinstance(raw, str):
            return [raw.strip()]
        return [u.strip() for u in raw if u.strip()]
    except Exception:
        return []


def is_admin() -> bool:
    """Return True if the currently logged-in user is an admin."""
    if not is_logged_in():
        return False
    uid = get_current_uid()
    return uid in get_admin_uids()


def require_admin() -> bool:
    """
    Render an access-denied screen and return False if not admin.
    Returns True if user is authorized.
    """
    if not is_logged_in():
        _render_not_logged_in()
        return False
    if not is_admin():
        _render_access_denied()
        return False
    return True


# ── BLOCKED SCREENS ───────────────────────────────────────────────────────────

def _render_not_logged_in():
    st.markdown(
        '<div style="text-align:center;padding:5rem 2rem;">'
        '<div style="font-size:3rem;margin-bottom:1rem;">🔒</div>'
        '<div style="font-family:\'Space Grotesk\',sans-serif;font-size:1.4rem;'
        'font-weight:700;color:#F0F6FF;margin-bottom:0.5rem;">Sign In Required</div>'
        '<div style="font-size:0.88rem;color:#7B92B2;">'
        'Please sign in to access the admin dashboard.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    from auth.firebase_auth import render_auth_modal
    render_auth_modal()


def _render_access_denied():
    email = get_current_email() or "unknown"
    st.markdown(
        '<div style="text-align:center;padding:5rem 2rem;">'
        '<div style="font-size:3rem;margin-bottom:1rem;">🚫</div>'
        '<div style="font-family:\'Space Grotesk\',sans-serif;font-size:1.4rem;'
        'font-weight:700;color:#FF4560;margin-bottom:0.5rem;">Access Denied</div>'
        f'<div style="font-size:0.88rem;color:#7B92B2;margin-bottom:1rem;">'
        f'<b style="color:#F0F6FF;">{email}</b> does not have admin privileges.</div>'
        '<div style="background:rgba(255,69,96,0.08);border:1px solid rgba(255,69,96,0.25);'
        'border-radius:10px;padding:1rem 1.5rem;max-width:400px;margin:0 auto;'
        'font-size:0.8rem;color:#7B92B2;">'
        'To grant access, add your UID to <code style="color:#00D4FF;">secrets.toml</code>:<br><br>'
        '<code style="color:#00FFB3;">[admin]<br>uids = ["your-firebase-uid"]</code>'
        '</div></div>',
        unsafe_allow_html=True,
    )
