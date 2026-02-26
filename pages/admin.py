"""
InvestIQ AI — Admin Dashboard
All 8 features with role-based access control.

Features:
  1. Platform KPIs
  2. Activity Feed
  3. User Management Table
  4. Platform Analytics (4 charts)
  5. Model Usage Stats
  6. Top Analyses Platform-Wide
  7. System Health
  8. Content Moderation
"""

import streamlit as st
from datetime import datetime, timezone
from styles.theme import apply_theme
from auth.admin_auth import require_admin, get_admin_uids
from auth.firebase_auth import get_current_email, get_current_uid


# ── MAIN ──────────────────────────────────────────────────────────────────────

def render_admin():
    apply_theme()

    # Role-based gate — stops rendering if not admin
    if not require_admin():
        return

    # ── Admin header bar ──────────────────────────────────────────────────────
    email = get_current_email() or ""
    st.markdown(
        '<div style="background:linear-gradient(135deg,rgba(255,69,96,0.08) 0%,'
        'rgba(108,99,255,0.08) 100%);border:1px solid rgba(255,69,96,0.2);'
        'border-radius:14px;padding:1.2rem 1.8rem;margin-bottom:0.5rem;'
        'display:flex;align-items:center;justify-content:space-between;">'
        '<div>'
        '<div style="font-size:0.6rem;color:#FF4560;text-transform:uppercase;'
        'letter-spacing:0.2em;font-weight:700;margin-bottom:0.3rem;">'
        '🔐 ADMIN CONTROL PANEL</div>'
        '<div style="font-family:\'Space Grotesk\',sans-serif;font-size:1.5rem;'
        'font-weight:800;color:#F0F6FF;">InvestIQ Platform Dashboard</div>'
        '</div>'
        f'<div style="text-align:right;">'
        f'<div style="font-size:0.7rem;color:#7B92B2;">Signed in as</div>'
        f'<div style="font-size:0.82rem;color:#FF4560;font-weight:600;">{email}</div>'
        f'<div style="font-size:0.65rem;color:#3A4F6A;margin-top:0.2rem;">'
        f'UID: {get_current_uid()}</div>'
        f'</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Auto-refresh every 60 seconds ────────────────────────────────────────
    import time as _time
    if "admin_last_refresh" not in st.session_state:
        st.session_state["admin_last_refresh"] = _time.time()
    elapsed = _time.time() - st.session_state.get("admin_last_refresh", 0)
    if elapsed > 60:
        st.session_state.pop("admin_cache", None)
        st.session_state["admin_last_refresh"] = _time.time()

    # Load data
    analyses = _load_admin_data()

    from db.admin_firestore import compute_platform_stats
    stats = compute_platform_stats(analyses)

    # Refresh button + last updated
    import time as _time
    col_ref, col_ts, _ = st.columns([1, 2, 6])
    with col_ref:
        if st.button("🔄 Refresh", help="Reload all platform data"):
            st.session_state.pop("admin_cache", None)
            st.session_state["admin_last_refresh"] = _time.time()
            st.rerun()
    with col_ts:
        last = st.session_state.get("admin_last_refresh", 0)
        if last:
            secs_ago = int(_time.time() - last)
            if secs_ago < 60:
                ts_str = f"{secs_ago}s ago"
            else:
                ts_str = f"{secs_ago // 60}m ago"
            st.markdown(
                f'<div style="font-size:0.68rem;color:#3A4F6A;padding-top:0.6rem;">'
                f'Last updated: {ts_str} &nbsp;·&nbsp; '
                f'Auto-refreshes every 60s</div>',
                unsafe_allow_html=True,
            )

    _divider()

    # ── Features ──────────────────────────────────────────────────────────────
    _render_kpis(stats)
    _divider()
    _render_activity_feed(analyses)
    _divider()
    _render_platform_analytics(analyses, stats)
    _divider()
    _render_model_stats(analyses)
    _divider()
    _render_top_analyses(analyses)
    _divider()
    _render_user_table(analyses)
    _divider()
    _render_system_health(stats)
    _divider()
    _render_moderation(analyses)


# ── DATA LOADER ─────────────────────────────────────────────────────────────────

def _load_admin_data() -> list:
    if "admin_cache" not in st.session_state:
        with st.spinner("Fetching platform data from Firestore..."):
            from db.admin_firestore import fetch_all_analyses
            data = fetch_all_analyses(limit=500)
            st.session_state["admin_cache"] = data

    data      = st.session_state.get("admin_cache", [])
    admin_uid = get_current_uid() or ""
    uids_in   = set(a.get("_uid","") or a.get("uid","") for a in data if a.get("_uid") or a.get("uid"))
    total     = len(data)
    is_multi  = len(uids_in) > 1 or (len(uids_in)==1 and admin_uid not in uids_in)

    if total == 0:
        st.warning("**No data loaded yet.** Click the button below to register your account instantly.")
        if st.button("⚡ Bootstrap Admin Registry Now", type="primary"):
            _bootstrap_admin_registry()
            st.session_state.pop("admin_cache", None)
            st.rerun()
        with st.expander("ℹ️ Why is this happening?"):
            st.markdown(
                "Profile docs are written on login starting from this code version. "
                "The Bootstrap button writes your profile doc right now — no sign-out needed. "
                "Future users register automatically on their next login."
            )
    elif not is_multi:
        st.warning(
            f"Showing your own {total} analyses only. "
            "Other users will appear automatically after they next log in."
        )
    else:
        st.success(f"✅ {total} analyses loaded from {len(uids_in)} users")

    return data



def _bootstrap_admin_registry():
    """Write /users/{uid} and /platform_stats/{uid} right now using the current session."""
    from auth.firebase_auth import get_current_uid, get_current_email, get_id_token
    uid   = get_current_uid() or ""
    email = get_current_email() or ""
    token = get_id_token() or ""

    if not uid or not token:
        st.error("Not logged in.")
        return

    import requests, json
    from datetime import datetime, timezone
    project = st.secrets["firebase"]["projectId"]
    base    = (
        f"https://firestore.googleapis.com/v1"
        f"/projects/{project}/databases/(default)/documents"
    )
    hdrs    = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    now_iso = datetime.now(timezone.utc).isoformat()

    def tv(v):
        if isinstance(v, bool): return {"booleanValue": v}
        if isinstance(v, int):  return {"integerValue": str(v)}
        if isinstance(v, str):  return {"stringValue": v}
        return {"stringValue": str(v)}

    # Write /users/{uid}
    r1 = requests.patch(
        f"{base}/users/{uid}", headers=hdrs, timeout=8,
        data=json.dumps({"fields": {
            "uid": tv(uid), "email": tv(email),
            "joined_at": tv(now_iso), "last_login": tv(now_iso), "active": tv(True),
        }}),
    )

    # Write /platform_stats/{uid}
    r2 = requests.patch(
        f"{base}/platform_stats/{uid}", headers=hdrs, timeout=8,
        data=json.dumps({"fields": {
            "uid": tv(uid), "email": tv(email),
            "last_login": tv(now_iso), "total_analyses": tv(0),
        }}),
    )

    if r1.status_code == 200 and r2.status_code == 200:
        st.success(
            f"✅ Registered successfully! "
            f"Now click **🔄 Refresh** to load all your analyses."
        )
    else:
        # Show specific error to diagnose rules issue
        st.error(
            f"/users write: HTTP {r1.status_code} — "
            f"/platform_stats write: HTTP {r2.status_code}\n\n"
            f"If you see 403, your Firestore rules need:\n"
            f"  match /users/{{userId}} {{ allow write: if request.auth.uid == userId; }}\n"
            f"  match /platform_stats/{{userId}} {{ allow write: if request.auth.uid == userId; }}"
        )


# ── FEATURE 1: PLATFORM KPIs ──────────────────────────────────────────────────

def _render_kpis(stats: dict):
    _section_label("📊 PLATFORM KPIs")

    kpis = [
        ("👥", "Unique Users",    str(stats["unique_users"]),   "#00D4FF"),
        ("📋", "Total Analyses",  str(stats["total"]),           "#6C63FF"),
        ("📅", "Today",           str(stats["today"]),           "#F59E0B"),
        ("📆", "This Week",       str(stats["this_week"]),       "#B45FFF"),
        ("📈", "Avg Score",       f"{stats['avg_score']}/100",  _score_col(stats["avg_score"])),
        ("🟢", "Strong Invest",   str(stats["strong_invest"]),   "#00FFB3"),
        ("🟡", "Consider",        str(stats["consider"]),        "#F59E0B"),
        ("🔴", "Reject",          str(stats["reject"]),          "#FF4560"),
    ]

    cols = st.columns(8)
    for col, (icon, label, val, color) in zip(cols, kpis):
        with col:
            st.markdown(
                f'<div style="background:#0D1B2E;border:1px solid #1A2F4A;'
                f'border-top:2px solid {color};border-radius:10px;'
                f'padding:0.9rem 0.6rem;text-align:center;">'
                f'<div style="font-size:1.1rem;margin-bottom:0.3rem;">{icon}</div>'
                f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:1.3rem;'
                f'font-weight:600;color:{color};line-height:1.1;">{val}</div>'
                f'<div style="font-size:0.6rem;color:#7B92B2;text-transform:uppercase;'
                f'letter-spacing:0.08em;margin-top:0.2rem;">{label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Quick rate indicators
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    total = stats["total"]
    if total > 0:
        invest_pct = round(stats["strong_invest"] / total * 100)
        rej_pct    = round(stats["reject"]        / total * 100)
        pub_pct    = round(stats["public_count"]  / total * 100)
        m1, m2, m3 = st.columns(3)
        for col, label, val, color in [
            (m1, "Strong Invest Rate",   f"{invest_pct}%", "#00FFB3"),
            (m2, "Reject Rate",          f"{rej_pct}%",    "#FF4560"),
            (m3, "Public Share Rate",    f"{pub_pct}%",    "#6C63FF"),
        ]:
            with col:
                st.markdown(
                    f'<div style="background:#0D1B2E;border:1px solid #1A2F4A;'
                    f'border-radius:8px;padding:0.6rem 1rem;display:flex;'
                    f'align-items:center;justify-content:space-between;">'
                    f'<span style="font-size:0.75rem;color:#7B92B2;">{label}</span>'
                    f'<span style="font-family:\'JetBrains Mono\',monospace;'
                    f'font-size:1rem;font-weight:600;color:{color};">{val}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )


# ── FEATURE 2: ACTIVITY FEED ──────────────────────────────────────────────────

def _render_activity_feed(analyses: list):
    _section_label("⚡ RECENT ACTIVITY FEED")

    recent = analyses[:12]

    if not recent:
        _empty("No analyses recorded yet.")
        return

    for a in recent:
        name  = a.get("startup_name", "Unknown")
        score = a.get("overall_investment_score", 0)
        rec   = a.get("final_recommendation", "")
        uid   = a.get("_uid") or a.get("uid","unknown")
        email = a.get("user_email","")
        ind   = a.get("industry","")
        created = a.get("created_at","")
        is_pub = a.get("is_public", False)

        date_str = ""
        try:
            dt = datetime.fromisoformat(created.replace("Z","+00:00"))
            now = datetime.now(timezone.utc)
            diff = now - dt
            if diff.seconds < 3600 and diff.days == 0:
                date_str = f"{diff.seconds // 60}m ago"
            elif diff.days == 0:
                date_str = f"{diff.seconds // 3600}h ago"
            elif diff.days < 7:
                date_str = f"{diff.days}d ago"
            else:
                date_str = dt.strftime("%b %d")
        except Exception:
            pass

        score_c = _score_col(score)
        rec_lower = rec.lower()
        if "invest" in rec_lower:
            pill_bg, pill_col, pill_border = "rgba(0,255,179,0.10)","#00FFB3","rgba(0,255,179,0.3)"
        elif "consider" in rec_lower:
            pill_bg, pill_col, pill_border = "rgba(245,158,11,0.10)","#F59E0B","rgba(245,158,11,0.3)"
        else:
            pill_bg, pill_col, pill_border = "rgba(255,69,96,0.10)","#FF4560","rgba(255,69,96,0.3)"

        pub_badge = (
            '<span style="background:rgba(108,99,255,0.12);color:#6C63FF;'
            'border:1px solid rgba(108,99,255,0.3);border-radius:3px;'
            'font-size:0.58rem;padding:0.06rem 0.35rem;margin-left:0.4rem;">PUBLIC</span>'
            if is_pub else ""
        )

        uid_short = uid[:8] + "..." if len(uid) > 8 else uid
        user_display = email if email else f"UID:{uid_short}"

        st.markdown(
            f'<div style="background:#0D1B2E;border:1px solid #1A2F4A;border-radius:10px;'
            f'padding:0.7rem 1.1rem;margin-bottom:0.4rem;'
            f'display:flex;align-items:center;gap:1rem;flex-wrap:wrap;">'
            # score bubble
            f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:1.2rem;'
            f'font-weight:700;color:{score_c};min-width:2.5rem;text-align:center;">{score}</div>'
            # startup info
            f'<div style="flex:1;min-width:120px;">'
            f'<div style="font-size:0.88rem;font-weight:700;color:#F0F6FF;">'
            f'{name}{pub_badge}</div>'
            f'<div style="font-size:0.68rem;color:#7B92B2;">{ind}</div>'
            f'</div>'
            # recommendation pill
            f'<div style="display:inline-flex;align-items:center;background:{pill_bg};'
            f'color:{pill_col};border:1px solid {pill_border};border-radius:999px;'
            f'padding:0.18rem 0.65rem;font-size:0.65rem;font-weight:700;'
            f'text-transform:uppercase;">{rec}</div>'
            # user
            f'<div style="font-size:0.68rem;color:#3A4F6A;min-width:140px;text-align:right;">'
            f'{user_display}</div>'
            # time
            f'<div style="font-size:0.68rem;color:#3A4F6A;min-width:50px;text-align:right;">'
            f'{date_str}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── FEATURE 4: PLATFORM ANALYTICS ────────────────────────────────────────────

def _render_platform_analytics(analyses: list, stats: dict):
    _section_label("📈 PLATFORM ANALYTICS")

    if not analyses:
        _empty("No data to display.")
        return

    import plotly.graph_objects as go
    from collections import Counter

    col1, col2 = st.columns(2)

    # ── Chart 1: Analyses per day ─────────────────────────────────────────────
    with col1:
        from db.admin_firestore import get_daily_counts
        dates, values = get_daily_counts(analyses, days=30)
        fig = go.Figure(go.Bar(
            x=dates, y=values,
            marker=dict(
                color=values,
                colorscale=[[0,"#1A2F4A"],[1,"#00D4FF"]],
                line=dict(width=0),
            ),
            hovertemplate="%{x}: %{y} analyses<extra></extra>",
        ))
        fig.update_layout(**_chart_layout("Analyses per Day — Last 30 Days", height=260))
        fig.update_xaxis(tickangle=-45, tickfont=dict(size=8))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── Chart 2: Score distribution histogram ─────────────────────────────────
    with col2:
        scores = [a.get("overall_investment_score", 0) for a in analyses]
        import plotly.figure_factory as ff
        try:
            fig2 = go.Figure(go.Histogram(
                x=scores, nbinsx=20,
                marker=dict(color="#6C63FF", line=dict(color="#070D1A", width=1)),
                hovertemplate="Score %{x}: %{y} analyses<extra></extra>",
            ))
            fig2.add_vline(x=70, line=dict(color="#00FFB3", dash="dot", width=1.5),
                           annotation=dict(text="Invest", font=dict(color="#00FFB3", size=9)))
            fig2.add_vline(x=45, line=dict(color="#F59E0B", dash="dot", width=1.5),
                           annotation=dict(text="Consider", font=dict(color="#F59E0B", size=9)))
            fig2.update_layout(**_chart_layout("Score Distribution (Platform-Wide)", height=260))
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        except Exception:
            st.info("Score distribution unavailable.")

    col3, col4 = st.columns(2)

    # ── Chart 3: Industry popularity ──────────────────────────────────────────
    with col3:
        ind_counts = Counter(a.get("industry","Other") for a in analyses)
        top_ind    = ind_counts.most_common(8)
        labels     = [i[0].split("/")[0].strip()[:16] for i in top_ind]
        vals       = [i[1] for i in top_ind]
        colors     = ["#00D4FF","#6C63FF","#00FFB3","#F59E0B","#FF4560",
                      "#B45FFF","#FF6B35","#00B4D8"]

        fig3 = go.Figure(go.Pie(
            labels=labels, values=vals,
            hole=0.5,
            marker=dict(colors=colors[:len(labels)],
                        line=dict(color="#070D1A", width=2)),
            textinfo="none",
            hovertemplate="%{label}: %{value} analyses (%{percent})<extra></extra>",
        ))
        fig3.update_layout(**_chart_layout("Industry Popularity", height=260))
        fig3.update_layout(
            legend=dict(
                font=dict(color="#7B92B2", size=9),
                bgcolor="rgba(0,0,0,0)",
                orientation="v", x=1.02,
            )
        )
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    # ── Chart 4: Recommendation breakdown ─────────────────────────────────────
    with col4:
        rec_data = [
            ("Strong Invest", stats["strong_invest"], "#00FFB3"),
            ("Consider",      stats["consider"],      "#F59E0B"),
            ("Reject",        stats["reject"],         "#FF4560"),
        ]
        fig4 = go.Figure(go.Bar(
            x=[r[0] for r in rec_data],
            y=[r[1] for r in rec_data],
            marker=dict(
                color=[r[2] for r in rec_data],
                line=dict(width=0),
            ),
            text=[str(r[1]) for r in rec_data],
            textposition="outside",
            textfont=dict(color="#F0F6FF", size=11),
            hovertemplate="%{x}: %{y}<extra></extra>",
        ))
        fig4.update_layout(**_chart_layout("Recommendation Breakdown", height=260))
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})


# ── FEATURE 5: MODEL USAGE STATS ─────────────────────────────────────────────

def _render_model_stats(analyses: list):
    _section_label("🤖 MODEL USAGE STATS")

    if not analyses:
        _empty("No model usage data.")
        return

    total = len(analyses)
    st.markdown(
        f'<div style="font-size:0.8rem;color:#7B92B2;margin-bottom:1rem;">'
        f'Derived from {total} analyses — model field stored at save time.</div>',
        unsafe_allow_html=True,
    )

    # Since model_config isn't stored in Firestore yet (stored in session),
    # show what we can derive + note
    col1, col2, col3, col4 = st.columns(4)

    avg_per_user = round(total / max(len(set(
        a.get("_uid") or a.get("uid","") for a in analyses
    )), 1), 1)

    total_agent_calls = total * 6
    avg_score_all = round(sum(a.get("overall_investment_score",0) for a in analyses)/total) if total else 0

    # Score quality tiers
    elite = sum(1 for a in analyses if a.get("overall_investment_score",0) >= 80)
    good  = sum(1 for a in analyses if 60 <= a.get("overall_investment_score",0) < 80)
    weak  = sum(1 for a in analyses if a.get("overall_investment_score",0) < 60)

    for col, icon, label, val, color, sub in [
        (col1, "⚡", "Total Agent Calls",  f"{total_agent_calls:,}", "#00D4FF",
         f"{total} analyses × 6 agents"),
        (col2, "📊", "Avg Analyses/User",  str(avg_per_user),         "#6C63FF",
         "across all users"),
        (col3, "🏆", "Elite (80+ Score)",  str(elite),               "#00FFB3",
         f"{round(elite/total*100) if total else 0}% of analyses"),
        (col4, "📉", "Platform Avg Score", f"{avg_score_all}/100",    _score_col(avg_score_all),
         "weighted average"),
    ]:
        with col:
            st.markdown(
                f'<div style="background:#0D1B2E;border:1px solid #1A2F4A;'
                f'border-left:3px solid {color};border-radius:10px;padding:1rem 1.1rem;">'
                f'<div style="font-size:1.3rem;margin-bottom:0.3rem;">{icon}</div>'
                f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:1.4rem;'
                f'font-weight:600;color:{color};margin-bottom:0.2rem;">{val}</div>'
                f'<div style="font-size:0.72rem;font-weight:600;color:#F0F6FF;'
                f'margin-bottom:0.15rem;">{label}</div>'
                f'<div style="font-size:0.63rem;color:#3A4F6A;">{sub}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Score quality bar
    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
    if total > 0:
        elite_pct = round(elite / total * 100)
        good_pct  = round(good  / total * 100)
        weak_pct  = round(weak  / total * 100)

        st.markdown(
            '<div style="background:#0D1B2E;border:1px solid #1A2F4A;'
            'border-radius:10px;padding:1rem 1.4rem;">'
            '<div style="font-size:0.65rem;color:#3A4F6A;text-transform:uppercase;'
            'letter-spacing:0.12em;margin-bottom:0.7rem;">ANALYSIS QUALITY BREAKDOWN</div>'
            '<div style="display:flex;height:20px;border-radius:4px;overflow:hidden;'
            'margin-bottom:0.5rem;">'
            f'<div style="width:{elite_pct}%;background:#00FFB3;" title="Elite: {elite}"></div>'
            f'<div style="width:{good_pct}%;background:#F59E0B;" title="Good: {good}"></div>'
            f'<div style="width:{weak_pct}%;background:#FF4560;" title="Weak: {weak}"></div>'
            '</div>'
            '<div style="display:flex;gap:1.5rem;">'
            f'<span style="font-size:0.7rem;color:#00FFB3;">■ Elite 80+ ({elite_pct}%)</span>'
            f'<span style="font-size:0.7rem;color:#F59E0B;">■ Good 60-79 ({good_pct}%)</span>'
            f'<span style="font-size:0.7rem;color:#FF4560;">■ Below 60 ({weak_pct}%)</span>'
            '</div></div>',
            unsafe_allow_html=True,
        )


# ── FEATURE 6: TOP ANALYSES PLATFORM-WIDE ────────────────────────────────────

def _render_top_analyses(analyses: list):
    _section_label("🏆 TOP ANALYSES — PLATFORM-WIDE")

    if not analyses:
        _empty("No analyses yet.")
        return

    top = sorted(analyses, key=lambda a: a.get("overall_investment_score",0), reverse=True)[:5]

    st.markdown(
        '<div style="font-size:0.8rem;color:#7B92B2;margin-bottom:1rem;">'
        'Highest-scored startup analyses across all users.</div>',
        unsafe_allow_html=True,
    )

    for rank, a in enumerate(top, 1):
        name  = a.get("startup_name","Unknown")
        score = a.get("overall_investment_score",0)
        rec   = a.get("final_recommendation","")
        ind   = a.get("industry","")
        uid   = a.get("_uid") or a.get("uid","")
        email = a.get("user_email","")
        verdict = a.get("one_line_verdict","")
        score_c  = _score_col(score)
        rank_col = ["#FFD700","#C0C0C0","#CD7F32","#B45FFF","#00D4FF"][rank-1]

        st.markdown(
            f'<div style="background:#0D1B2E;border:1px solid #1A2F4A;'
            f'border-left:3px solid {rank_col};border-radius:12px;'
            f'padding:1rem 1.4rem;margin-bottom:0.6rem;'
            f'display:flex;align-items:center;gap:1.2rem;">'
            f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:1.6rem;'
            f'font-weight:700;color:{rank_col};min-width:1.8rem;text-align:center;">#{rank}</div>'
            f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:2rem;'
            f'font-weight:700;color:{score_c};min-width:3rem;text-align:center;">{score}</div>'
            f'<div style="flex:1;">'
            f'<div style="font-size:0.95rem;font-weight:700;color:#F0F6FF;">{name}</div>'
            f'<div style="font-size:0.72rem;color:#7B92B2;">'
            f'{ind} &nbsp;·&nbsp; <span style="color:#3A4F6A;">'
            f'{email or uid[:12]}</span></div>'
            + (f'<div style="font-size:0.75rem;color:#C8D8E8;font-style:italic;margin-top:0.3rem;">'
               f'&ldquo;{verdict[:120]}{"..." if len(verdict)>120 else ""}&rdquo;</div>'
               if verdict else "")
            + f'</div>'
            f'<div style="font-size:0.78rem;font-weight:700;color:{score_c};'
            f'text-transform:uppercase;">{rec}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── FEATURE 3: USER MANAGEMENT TABLE ─────────────────────────────────────────

def _render_user_table(analyses: list):
    _section_label("👥 USER MANAGEMENT")

    if not analyses:
        _empty("No users found.")
        return

    from db.admin_firestore import get_user_table
    users = get_user_table(analyses)

    st.markdown(
        f'<div style="font-size:0.8rem;color:#7B92B2;margin-bottom:1rem;">'
        f'{len(users)} registered users on platform. '
        f'Admin UIDs: {", ".join(get_admin_uids()) or "None set"}</div>',
        unsafe_allow_html=True,
    )

    # Search
    search = st.text_input(
        "🔍 Search user", placeholder="Email or UID...",
        label_visibility="collapsed", key="admin_user_search"
    )

    filtered = users
    if search:
        s = search.lower()
        filtered = [u for u in users if s in u["email"].lower() or s in u["uid"].lower()]

    # Table header
    st.markdown(
        '<div style="display:flex;gap:0;padding:0.4rem 0.8rem;'
        'background:#0D1B2E;border:1px solid #1A2F4A;border-radius:8px 8px 0 0;">'
        '<span style="font-size:0.62rem;color:#3A4F6A;text-transform:uppercase;'
        'letter-spacing:0.1em;font-weight:600;flex:2;">User</span>'
        '<span style="font-size:0.62rem;color:#3A4F6A;text-transform:uppercase;'
        'letter-spacing:0.1em;font-weight:600;flex:1;text-align:center;">Analyses</span>'
        '<span style="font-size:0.62rem;color:#3A4F6A;text-transform:uppercase;'
        'letter-spacing:0.1em;font-weight:600;flex:1;text-align:center;">Avg Score</span>'
        '<span style="font-size:0.62rem;color:#3A4F6A;text-transform:uppercase;'
        'letter-spacing:0.1em;font-weight:600;flex:1;text-align:center;">Invest</span>'
        '<span style="font-size:0.62rem;color:#3A4F6A;text-transform:uppercase;'
        'letter-spacing:0.1em;font-weight:600;flex:1.5;text-align:right;">Last Active</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    for u in filtered[:30]:
        uid        = u["uid"]
        email      = u["email"] or f"UID:{uid[:12]}..."
        total      = u["total"]
        avg        = u["avg_score"]
        si         = u["strong_invest"]
        last       = u.get("last_active","")
        avg_c      = _score_col(avg)
        is_adm     = uid in get_admin_uids()

        last_str = ""
        try:
            dt = datetime.fromisoformat(last.replace("Z","+00:00"))
            last_str = dt.strftime("%b %d, %Y")
        except Exception:
            pass

        admin_badge = (
            '<span style="background:rgba(255,69,96,0.15);color:#FF4560;'
            'border:1px solid rgba(255,69,96,0.3);border-radius:3px;'
            'font-size:0.55rem;padding:0.05rem 0.3rem;margin-left:0.4rem;">ADMIN</span>'
            if is_adm else ""
        )

        st.markdown(
            f'<div style="display:flex;align-items:center;gap:0;padding:0.55rem 0.8rem;'
            f'background:#070D1A;border:1px solid #1A2F4A;border-top:none;">'
            f'<div style="flex:2;">'
            f'<div style="font-size:0.82rem;color:#F0F6FF;font-weight:600;">'
            f'{email}{admin_badge}</div>'
            f'<div style="font-size:0.65rem;color:#3A4F6A;">{uid[:16]}...</div>'
            f'</div>'
            f'<div style="flex:1;text-align:center;font-family:\'JetBrains Mono\',monospace;'
            f'font-size:0.9rem;color:#00D4FF;font-weight:600;">{total}</div>'
            f'<div style="flex:1;text-align:center;font-family:\'JetBrains Mono\',monospace;'
            f'font-size:0.9rem;color:{avg_c};font-weight:600;">{avg}</div>'
            f'<div style="flex:1;text-align:center;font-family:\'JetBrains Mono\',monospace;'
            f'font-size:0.9rem;color:#00FFB3;font-weight:600;">{si}</div>'
            f'<div style="flex:1.5;text-align:right;font-size:0.72rem;color:#7B92B2;">'
            f'{last_str}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Close table
    st.markdown(
        '<div style="border:1px solid #1A2F4A;border-top:none;'
        'border-radius:0 0 8px 8px;height:4px;background:#0D1B2E;"></div>',
        unsafe_allow_html=True,
    )

    if len(filtered) > 30:
        st.caption(f"Showing 30 of {len(filtered)} users")


# ── FEATURE 7: SYSTEM HEALTH ──────────────────────────────────────────────────

def _render_system_health(stats: dict):
    _section_label("🛡️ SYSTEM HEALTH")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(
            '<div style="font-size:0.72rem;color:#7B92B2;margin-bottom:0.8rem;">'
            'Click to check live API status.</div>',
            unsafe_allow_html=True,
        )
        if st.button("🔍 Check API Health", use_container_width=True):
            with st.spinner("Pinging APIs..."):
                from db.admin_firestore import check_api_health
                health = check_api_health()
                st.session_state["admin_health"] = health

        health = st.session_state.get("admin_health")
        if health:
            for service, status in health.items():
                color = "#00FFB3" if "Online" in status else "#FF4560"
                st.markdown(
                    f'<div style="background:#0D1B2E;border:1px solid #1A2F4A;'
                    f'border-radius:8px;padding:0.6rem 0.9rem;margin-bottom:0.4rem;'
                    f'display:flex;justify-content:space-between;align-items:center;">'
                    f'<span style="font-size:0.78rem;color:#F0F6FF;font-weight:600;">'
                    f'{service.upper()}</span>'
                    f'<span style="font-size:0.75rem;color:{color};">{status}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    with col2:
        total = stats.get("total", 0)
        st.markdown(
            '<div style="background:#0D1B2E;border:1px solid #1A2F4A;'
            'border-radius:12px;padding:1.2rem 1.4rem;">'
            '<div style="font-size:0.65rem;color:#3A4F6A;text-transform:uppercase;'
            'letter-spacing:0.12em;margin-bottom:0.8rem;">PLATFORM METRICS</div>'
            + _health_row("Total Analyses Processed", f"{total:,}", "#00D4FF")
            + _health_row("Estimated Agent API Calls", f"{total * 6:,}", "#6C63FF")
            + _health_row("Shared Public Reports", f"{stats.get('public_count',0)}", "#F59E0B")
            + _health_row("Platform Database", "Firestore REST API", "#00FFB3")
            + _health_row("Auth Provider", "Firebase Auth (Email/Password)", "#00FFB3")
            + _health_row("Hosting", "Streamlit Community Cloud", "#7B92B2")
            + '</div>',
            unsafe_allow_html=True,
        )


def _health_row(label: str, val: str, color: str) -> str:
    return (
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'padding:0.35rem 0;border-bottom:1px solid #1A2F4A;">'
        f'<span style="font-size:0.75rem;color:#7B92B2;">{label}</span>'
        f'<span style="font-size:0.75rem;color:{color};font-weight:600;">{val}</span>'
        f'</div>'
    )


# ── FEATURE 8: CONTENT MODERATION ────────────────────────────────────────────

def _render_moderation(analyses: list):
    _section_label("🚨 CONTENT MODERATION")

    public_analyses = [a for a in analyses if a.get("is_public")]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f'<div style="font-size:0.8rem;color:#7B92B2;margin-bottom:0.8rem;">'
            f'{len(public_analyses)} public reports — click Revoke to make private.</div>',
            unsafe_allow_html=True,
        )

        if not public_analyses:
            _empty("No public reports.")
        else:
            for a in public_analyses[:10]:
                name   = a.get("startup_name","Unknown")
                score  = a.get("overall_investment_score",0)
                uid    = a.get("_uid") or a.get("uid","")
                doc_id = a.get("_doc_id") or a.get("doc_id","")
                email  = a.get("user_email","")
                score_c = _score_col(score)

                c_info, c_btn = st.columns([3, 1])
                with c_info:
                    st.markdown(
                        f'<div style="background:#0D1B2E;border:1px solid rgba(108,99,255,0.3);'
                        f'border-radius:8px;padding:0.6rem 0.9rem;margin-bottom:0.3rem;">'
                        f'<div style="font-size:0.85rem;font-weight:700;color:#F0F6FF;">'
                        f'{name}</div>'
                        f'<div style="font-size:0.68rem;color:#7B92B2;">'
                        f'Score: <span style="color:{score_c};">{score}</span>'
                        f' &nbsp;·&nbsp; {email or uid[:14]}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with c_btn:
                    if doc_id and uid:
                        if st.button("🔒 Revoke",
                                     key=f"revoke_{doc_id}",
                                     use_container_width=True):
                            from db.admin_firestore import revoke_public_access
                            ok = revoke_public_access(uid, doc_id)
                            if ok:
                                st.success("Revoked")
                                st.session_state.pop("admin_cache", None)
                                st.rerun()
                            else:
                                st.error("Failed")

    with col2:
        st.markdown(
            '<div style="font-size:0.8rem;color:#7B92B2;margin-bottom:0.8rem;">'
            'Flagged: analyses with unusually high scores on minimal input.</div>',
            unsafe_allow_html=True,
        )

        # Flag analyses where score >= 85 but description is short (potentially gamed)
        flagged = [
            a for a in analyses
            if a.get("overall_investment_score", 0) >= 85
            and len(a.get("description", "") or "") < 120
        ]

        if not flagged:
            st.markdown(
                '<div style="background:#0D1B2E;border:1px dashed #1A2F4A;'
                'border-radius:8px;padding:1.2rem;text-align:center;">'
                '<div style="color:#00FFB3;font-size:0.85rem;">✅ No flagged content</div>'
                '<div style="color:#3A4F6A;font-size:0.72rem;margin-top:0.3rem;">'
                'All high-scoring analyses appear legitimate.</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            st.warning(f"⚠️ {len(flagged)} potentially suspicious analyses")
            for a in flagged[:5]:
                name   = a.get("startup_name","Unknown")
                score  = a.get("overall_investment_score",0)
                desc   = a.get("description","")[:60]
                uid    = a.get("_uid") or a.get("uid","")
                doc_id = a.get("_doc_id") or a.get("doc_id","")

                fc, fb = st.columns([3, 1])
                with fc:
                    st.markdown(
                        f'<div style="background:rgba(255,69,96,0.05);'
                        f'border:1px solid rgba(255,69,96,0.2);border-radius:8px;'
                        f'padding:0.6rem 0.9rem;margin-bottom:0.3rem;">'
                        f'<div style="font-size:0.82rem;font-weight:700;color:#F0F6FF;">'
                        f'{name} — Score: <span style="color:#FF4560;">{score}</span></div>'
                        f'<div style="font-size:0.67rem;color:#7B92B2;">"{desc}..."</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with fb:
                    if doc_id and uid:
                        if st.button("🗑️ Delete",
                                     key=f"flag_del_{doc_id}",
                                     use_container_width=True):
                            from db.admin_firestore import admin_delete_analysis
                            ok = admin_delete_analysis(uid, doc_id)
                            if ok:
                                st.success("Deleted")
                                st.session_state.pop("admin_cache", None)
                                st.rerun()


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _section_label(text: str):
    st.markdown(
        f'<div style="font-size:0.65rem;color:#3A4F6A;text-transform:uppercase;'
        f'letter-spacing:0.18em;font-weight:600;margin-bottom:1rem;">{text}</div>',
        unsafe_allow_html=True,
    )


def _empty(msg: str):
    st.markdown(
        f'<div style="background:#0D1B2E;border:1px dashed #1A2F4A;border-radius:8px;'
        f'padding:1.2rem;text-align:center;font-size:0.82rem;color:#3A4F6A;">{msg}</div>',
        unsafe_allow_html=True,
    )


def _chart_layout(title: str, height: int = 280) -> dict:
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=35, b=15, l=10, r=10),
        height=height,
        title=dict(
            text=title,
            font=dict(color="#7B92B2", size=11, family="Space Grotesk"),
            x=0,
        ),
        font=dict(family="Space Grotesk", color="#7B92B2"),
        xaxis=dict(showgrid=False, zeroline=False,
                   tickfont=dict(color="#7B92B2", size=9)),
        yaxis=dict(showgrid=True, gridcolor="#1A2F4A", zeroline=False,
                   tickfont=dict(color="#7B92B2", size=9)),
        showlegend=False,
    )


def _score_col(score: float) -> str:
    if score >= 70: return "#00FFB3"
    if score >= 45: return "#F59E0B"
    return "#FF4560"


def _divider():
    st.markdown(
        '<div style="height:1px;'
        'background:linear-gradient(90deg,transparent,#1A2F4A,transparent);'
        'margin:1.8rem 0;"></div>',
        unsafe_allow_html=True,
    )
