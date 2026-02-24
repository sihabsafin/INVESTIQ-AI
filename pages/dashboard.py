"""
InvestIQ AI — User Dashboard
All 7 features:
  1. Welcome Hero Strip
  2. Portfolio Score Overview (charts)
  3. Recent Analyses (last 3)
  4. Quick Actions
  5. Top Performing Startup
  6. AI Usage Stats
  7. Shared Reports
"""

import streamlit as st
from datetime import datetime, timezone
from styles.theme import apply_theme
from auth.firebase_auth import (
    is_logged_in, render_auth_modal,
    get_current_uid, get_current_email,
)


# ── MAIN RENDER ────────────────────────────────────────────────────────────────

def render_dashboard():
    apply_theme()

    if not is_logged_in():
        st.markdown(
            '<div class="page-header">'
            '<h1>📊 Dashboard</h1>'
            '<p>Sign in to access your personal investment intelligence hub.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        render_auth_modal()
        return

    # Load all analyses once per session (cache)
    analyses = _load_analyses()

    _render_welcome(analyses)
    _divider()
    _render_quick_actions()
    _divider()
    _render_portfolio_overview(analyses)
    _divider()
    _render_recent_analyses(analyses)
    _divider()
    _render_top_startup(analyses)
    _divider()
    _render_ai_stats(analyses)
    _divider()
    _render_shared_reports(analyses)


# ── DATA LOADER ────────────────────────────────────────────────────────────────

def _load_analyses() -> list:
    uid = get_current_uid()
    cache_key = f"dashboard_cache_{uid}"

    if cache_key not in st.session_state:
        with st.spinner("Loading your data..."):
            from db.firestore import list_analyses
            data = list_analyses(uid, limit=100)
            st.session_state[cache_key] = data

    return st.session_state.get(cache_key, [])


def _invalidate_cache():
    uid = get_current_uid()
    cache_key = f"dashboard_cache_{uid}"
    st.session_state.pop(cache_key, None)


# ── FEATURE 1: WELCOME HERO ────────────────────────────────────────────────────

def _render_welcome(analyses: list):
    email = get_current_email() or ""
    name  = email.split("@")[0].capitalize() if email else "Investor"

    hour  = datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    total    = len(analyses)
    avg      = round(sum(a.get("overall_investment_score", 0) for a in analyses) / total) if total else 0
    si_count = sum(1 for a in analyses if "invest" in a.get("final_recommendation", "").lower())
    consider = sum(1 for a in analyses if "consider" in a.get("final_recommendation", "").lower())
    reject   = sum(1 for a in analyses if "reject"  in a.get("final_recommendation", "").lower())
    avg_col  = "#00FFB3" if avg >= 70 else "#F59E0B" if avg >= 45 else "#FF4560"

    col_refresh, _ = st.columns([1, 8])
    with col_refresh:
        if st.button("🔄", help="Refresh dashboard data"):
            _invalidate_cache()
            st.rerun()

    # Greeting block
    st.markdown(
        f'<div style="background:linear-gradient(135deg,rgba(0,212,255,0.06) 0%,'
        f'rgba(108,99,255,0.06) 100%);border:1px solid #1A2F4A;border-radius:16px;'
        f'padding:1.8rem 2rem;margin-bottom:0.5rem;">'

        f'<div style="font-size:0.65rem;color:#00D4FF;text-transform:uppercase;'
        f'letter-spacing:0.18em;font-weight:700;margin-bottom:0.4rem;">'
        f'PERSONAL DASHBOARD</div>'

        f'<div style="font-family:\'Space Grotesk\',sans-serif;font-size:1.8rem;'
        f'font-weight:800;color:#F0F6FF;margin-bottom:0.3rem;">'
        f'{greeting}, {name} 👋</div>'

        f'<div style="font-size:0.88rem;color:#7B92B2;">'
        f'Your investment intelligence hub — all your analyses, insights, and performance in one place.'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Stat pills row
    if total == 0:
        return

    s1, s2, s3, s4, s5 = st.columns(5)
    for col, label, val, color in [
        (s1, "Analyses",     str(total),       "#00D4FF"),
        (s2, "Avg Score",    f"{avg}/100",     avg_col),
        (s3, "Strong Invest",str(si_count),    "#00FFB3"),
        (s4, "Consider",     str(consider),    "#F59E0B"),
        (s5, "Reject",       str(reject),      "#FF4560"),
    ]:
        with col:
            st.markdown(
                f'<div style="background:#0D1B2E;border:1px solid #1A2F4A;'
                f'border-top:2px solid {color};border-radius:10px;'
                f'padding:0.9rem 0.8rem;text-align:center;">'
                f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:1.5rem;'
                f'font-weight:600;color:{color};">{val}</div>'
                f'<div style="font-size:0.63rem;color:#7B92B2;text-transform:uppercase;'
                f'letter-spacing:0.1em;margin-top:0.2rem;">{label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ── FEATURE 4: QUICK ACTIONS ───────────────────────────────────────────────────
# (Rendered before charts — higher up for UX)

def _render_quick_actions():
    st.markdown(
        '<div style="font-size:0.65rem;color:#3A4F6A;text-transform:uppercase;'
        'letter-spacing:0.18em;font-weight:600;margin-bottom:0.8rem;">QUICK ACTIONS</div>',
        unsafe_allow_html=True,
    )

    q1, q2, q3, q4 = st.columns(4)

    with q1:
        if st.button("🔍  New Analysis", use_container_width=True, type="primary"):
            st.session_state.current_page = "analyze"
            st.rerun()
    with q2:
        if st.button("📁  My Analyses", use_container_width=True):
            st.session_state.current_page = "history"
            st.rerun()
    with q3:
        if st.button("⚖️  Compare", use_container_width=True):
            st.session_state.current_page = "compare"
            st.rerun()
    with q4:
        if st.button("🏠  Home", use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()


# ── FEATURE 2: PORTFOLIO OVERVIEW ─────────────────────────────────────────────

def _render_portfolio_overview(analyses: list):
    if not analyses:
        return

    st.markdown(
        '<div style="font-size:0.65rem;color:#3A4F6A;text-transform:uppercase;'
        'letter-spacing:0.18em;font-weight:600;margin-bottom:1rem;">PORTFOLIO OVERVIEW</div>',
        unsafe_allow_html=True,
    )

    import plotly.graph_objects as go

    col_donut, col_industry, col_trend = st.columns(3)

    # ── Donut: Recommendation split ───────────────────────────────────────────
    with col_donut:
        si  = sum(1 for a in analyses if "invest"  in a.get("final_recommendation","").lower())
        con = sum(1 for a in analyses if "consider" in a.get("final_recommendation","").lower())
        rej = sum(1 for a in analyses if "reject"   in a.get("final_recommendation","").lower())

        if si + con + rej > 0:
            fig = go.Figure(go.Pie(
                labels=["Strong Invest", "Consider", "Reject"],
                values=[si, con, rej],
                hole=0.62,
                marker=dict(
                    colors=["#00FFB3", "#F59E0B", "#FF4560"],
                    line=dict(color="#070D1A", width=2),
                ),
                textinfo="none",
                hovertemplate="%{label}: %{value}<extra></extra>",
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=30, b=10, l=10, r=10),
                height=220,
                showlegend=True,
                legend=dict(
                    font=dict(color="#7B92B2", size=10),
                    bgcolor="rgba(0,0,0,0)",
                    orientation="h",
                    x=0.5, xanchor="center", y=-0.05,
                ),
                annotations=[dict(
                    text=f"<b>{len(analyses)}</b><br><span style='font-size:10px'>total</span>",
                    x=0.5, y=0.5, font=dict(size=14, color="#F0F6FF"),
                    showarrow=False,
                )],
            )
            st.markdown(
                '<div style="font-size:0.72rem;color:#7B92B2;text-align:center;'
                'margin-bottom:0.3rem;">Recommendation Split</div>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(fig, use_container_width=True,
                            config={"displayModeBar": False})

    # ── Bar: Industry breakdown ────────────────────────────────────────────────
    with col_industry:
        from collections import Counter
        industry_counts = Counter(
            a.get("industry", "Other") for a in analyses
        )
        industries = list(industry_counts.keys())[:6]
        counts     = [industry_counts[i] for i in industries]

        # Shorten long industry names
        short = [i.split("/")[0].strip()[:14] for i in industries]

        fig2 = go.Figure(go.Bar(
            x=counts,
            y=short,
            orientation="h",
            marker=dict(
                color=["#00D4FF", "#6C63FF", "#00FFB3", "#F59E0B", "#FF4560", "#B45FFF"],
                line=dict(width=0),
            ),
            hovertemplate="%{y}: %{x} analyses<extra></extra>",
        ))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=30, b=10, l=10, r=10),
            height=220,
            xaxis=dict(
                showgrid=True, gridcolor="#1A2F4A",
                tickfont=dict(color="#7B92B2", size=9),
                zeroline=False,
            ),
            yaxis=dict(
                tickfont=dict(color="#C8D8E8", size=9),
                autorange="reversed",
            ),
            font=dict(family="Space Grotesk"),
        )
        st.markdown(
            '<div style="font-size:0.72rem;color:#7B92B2;text-align:center;'
            'margin-bottom:0.3rem;">Industry Breakdown</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(fig2, use_container_width=True,
                        config={"displayModeBar": False})

    # ── Line: Score trend over time ────────────────────────────────────────────
    with col_trend:
        dated = []
        for a in analyses:
            try:
                dt = datetime.fromisoformat(
                    a.get("created_at", "").replace("Z", "+00:00")
                )
                dated.append((dt, a.get("overall_investment_score", 0)))
            except Exception:
                pass

        dated.sort(key=lambda x: x[0])

        if len(dated) >= 2:
            dates  = [d[0].strftime("%b %d") for d in dated]
            scores = [d[1] for d in dated]

            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=dates, y=scores,
                mode="lines+markers",
                line=dict(color="#00D4FF", width=2),
                marker=dict(color="#00D4FF", size=6),
                fill="tozeroy",
                fillcolor="rgba(0,212,255,0.06)",
                hovertemplate="%{x}: %{y}<extra></extra>",
            ))
            # Reference lines
            for val, col in [(70, "#00FFB3"), (45, "#F59E0B")]:
                fig3.add_hline(
                    y=val, line=dict(color=col, dash="dot", width=1),
                    annotation=dict(
                        text=f"{'Invest' if val==70 else 'Consider'}",
                        font=dict(color=col, size=8),
                        xref="paper", x=1.01,
                    ),
                )
            fig3.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=30, b=10, l=10, r=40),
                height=220,
                xaxis=dict(
                    showgrid=False,
                    tickfont=dict(color="#7B92B2", size=8),
                    zeroline=False,
                ),
                yaxis=dict(
                    range=[0, 105],
                    showgrid=True, gridcolor="#1A2F4A",
                    tickfont=dict(color="#7B92B2", size=8),
                    zeroline=False,
                ),
                font=dict(family="Space Grotesk"),
                showlegend=False,
            )
            st.markdown(
                '<div style="font-size:0.72rem;color:#7B92B2;text-align:center;'
                'margin-bottom:0.3rem;">Score Trend Over Time</div>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(fig3, use_container_width=True,
                            config={"displayModeBar": False})
        else:
            st.markdown(
                '<div style="height:220px;display:flex;align-items:center;'
                'justify-content:center;color:#3A4F6A;font-size:0.8rem;">'
                'Need 2+ analyses for trend chart</div>',
                unsafe_allow_html=True,
            )


# ── FEATURE 3: RECENT ANALYSES ─────────────────────────────────────────────────

def _render_recent_analyses(analyses: list):
    if not analyses:
        return

    recent = analyses[:3]

    st.markdown(
        '<div style="display:flex;justify-content:space-between;align-items:center;'
        'margin-bottom:0.8rem;">'
        '<div style="font-size:0.65rem;color:#3A4F6A;text-transform:uppercase;'
        'letter-spacing:0.18em;font-weight:600;">RECENT ANALYSES</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(len(recent))
    for col, a in zip(cols, recent):
        with col:
            _mini_analysis_card(a)

    # View All button
    st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
    col_l, col_c, col_r = st.columns([2, 1.5, 2])
    with col_c:
        if st.button("View All Analyses →", use_container_width=True):
            st.session_state.current_page = "history"
            st.rerun()


def _mini_analysis_card(a: dict):
    from components.gauge import get_score_color

    name  = a.get("startup_name", "Unnamed")
    score = a.get("overall_investment_score", 0)
    rec   = a.get("final_recommendation", "")
    ind   = a.get("industry", "")
    created = a.get("created_at", "")
    score_col = get_score_color(score)

    date_str = ""
    if created:
        try:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            date_str = dt.strftime("%b %d, %Y")
        except Exception:
            pass

    rec_lower = rec.lower()
    if "invest" in rec_lower:
        pill_bg, pill_col, pill_border = ("rgba(0,255,179,0.10)","#00FFB3","rgba(0,255,179,0.35)")
        icon = "🟢"
    elif "consider" in rec_lower:
        pill_bg, pill_col, pill_border = ("rgba(245,158,11,0.10)","#F59E0B","rgba(245,158,11,0.35)")
        icon = "🟡"
    else:
        pill_bg, pill_col, pill_border = ("rgba(255,69,96,0.10)","#FF4560","rgba(255,69,96,0.35)")
        icon = "🔴"

    accent = (
        f'<div style="position:absolute;top:0;left:0;right:0;height:2px;'
        f'background:linear-gradient(90deg,transparent,{score_col},transparent);"></div>'
    )

    st.markdown(
        f'<div style="background:#0D1B2E;border:1px solid #1A2F4A;border-radius:12px;'
        f'padding:1.1rem;position:relative;overflow:hidden;height:100%;">'
        + accent
        + f'<div style="font-size:0.92rem;font-weight:700;color:#F0F6FF;'
        f'font-family:\'Space Grotesk\',sans-serif;margin-bottom:0.2rem;">{name}</div>'
        f'<div style="font-size:0.72rem;color:#7B92B2;margin-bottom:0.7rem;">'
        f'{ind}{"  ·  " + date_str if date_str else ""}</div>'
        f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:2rem;'
        f'font-weight:600;color:{score_col};line-height:1;margin-bottom:0.6rem;">{score}</div>'
        f'<div style="display:inline-flex;align-items:center;gap:0.3rem;'
        f'background:{pill_bg};color:{pill_col};border:1px solid {pill_border};'
        f'border-radius:999px;padding:0.2rem 0.7rem;font-size:0.68rem;font-weight:700;'
        f'text-transform:uppercase;letter-spacing:0.06em;">{icon} {rec}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── FEATURE 5: TOP PERFORMING STARTUP ─────────────────────────────────────────

def _render_top_startup(analyses: list):
    if not analyses:
        return

    top = max(analyses, key=lambda a: a.get("overall_investment_score", 0))
    score = top.get("overall_investment_score", 0)

    if score == 0:
        return

    from components.gauge import get_score_color, render_mini_gauge
    from components.score_cards import render_strengths_weaknesses

    st.markdown(
        '<div style="font-size:0.65rem;color:#3A4F6A;text-transform:uppercase;'
        'letter-spacing:0.18em;font-weight:600;margin-bottom:1rem;">TOP PERFORMING STARTUP</div>',
        unsafe_allow_html=True,
    )

    score_col = get_score_color(score)
    name  = top.get("startup_name", "Unknown")
    ind   = top.get("industry", "")
    stage = top.get("funding_stage", "")
    rec   = top.get("final_recommendation", "")
    verdict = top.get("one_line_verdict", "")

    col_info, col_scores, col_sw = st.columns([1.2, 1.5, 1.5])

    with col_info:
        st.markdown(
            f'<div style="background:#0D1B2E;border:1px solid #1A2F4A;'
            f'border-top:3px solid {score_col};border-radius:12px;padding:1.4rem;height:100%;">'
            f'<div style="font-size:0.62rem;color:{score_col};text-transform:uppercase;'
            f'letter-spacing:0.12em;font-weight:700;margin-bottom:0.5rem;">🏆 Best Score</div>'
            f'<div style="font-family:\'Space Grotesk\',sans-serif;font-size:1.15rem;'
            f'font-weight:800;color:#F0F6FF;margin-bottom:0.3rem;">{name}</div>'
            f'<div style="font-size:0.75rem;color:#7B92B2;margin-bottom:1rem;">'
            f'{ind}{"  ·  "+stage if stage else ""}</div>'
            f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:3rem;'
            f'font-weight:600;color:{score_col};line-height:1;margin-bottom:0.5rem;">{score}</div>'
            f'<div style="font-size:0.75rem;color:#7B92B2;">out of 100</div>'
            + (f'<div style="font-size:0.8rem;color:#C8D8E8;font-style:italic;'
               f'margin-top:0.8rem;line-height:1.5;border-left:2px solid {score_col};'
               f'padding-left:0.6rem;">&ldquo;{verdict}&rdquo;</div>' if verdict else "")
            + '</div>',
            unsafe_allow_html=True,
        )

    with col_scores:
        st.markdown(
            '<div style="font-size:0.68rem;color:#7B92B2;margin-bottom:0.5rem;'
            'text-align:center;">DIMENSION SCORES</div>',
            unsafe_allow_html=True,
        )
        dims = [
            ("Market",      top.get("market_score", 0)),
            ("Competition", top.get("competition_score", 0)),
            ("Financial",   top.get("financial_score", 0)),
            ("Risk",        top.get("risk_score", 0)),
            ("Innovation",  top.get("innovation_score", 0)),
        ]
        for label, val in dims:
            bar_col = get_score_color(val * 10)
            pct     = int(val * 10)
            st.markdown(
                f'<div style="margin-bottom:0.5rem;">'
                f'<div style="display:flex;justify-content:space-between;'
                f'font-size:0.7rem;color:#7B92B2;margin-bottom:0.2rem;">'
                f'<span>{label}</span>'
                f'<span style="color:{bar_col};font-weight:600;">{val}/10</span>'
                f'</div>'
                f'<div style="background:#1A2F4A;border-radius:3px;height:5px;">'
                f'<div style="background:{bar_col};width:{pct}%;height:5px;'
                f'border-radius:3px;"></div></div></div>',
                unsafe_allow_html=True,
            )

    with col_sw:
        render_strengths_weaknesses(top)


# ── FEATURE 6: AI USAGE STATS ─────────────────────────────────────────────────

def _render_ai_stats(analyses: list):
    if not analyses:
        return

    st.markdown(
        '<div style="font-size:0.65rem;color:#3A4F6A;text-transform:uppercase;'
        'letter-spacing:0.18em;font-weight:600;margin-bottom:1rem;">AI USAGE STATS</div>',
        unsafe_allow_html=True,
    )

    total = len(analyses)

    # Industry frequency
    from collections import Counter
    ind_counter = Counter(a.get("industry","Other") for a in analyses)
    fav_industry = ind_counter.most_common(1)[0][0] if ind_counter else "N/A"
    fav_industry_short = fav_industry.split("/")[0].strip()[:20]

    # Month stats
    now = datetime.now(timezone.utc)
    this_month = sum(
        1 for a in analyses
        if _parse_month(a.get("created_at","")) == (now.year, now.month)
    )
    last_month_year  = now.year if now.month > 1 else now.year - 1
    last_month_month = now.month - 1 if now.month > 1 else 12
    last_month = sum(
        1 for a in analyses
        if _parse_month(a.get("created_at","")) == (last_month_year, last_month_month)
    )

    # Agent calls = total * 6
    agent_calls = total * 6

    # Avg score improvement: compare first half vs second half
    if total >= 4:
        mid      = total // 2
        sorted_a = sorted(analyses, key=lambda x: x.get("created_at",""))
        avg_old  = round(sum(a.get("overall_investment_score",0) for a in sorted_a[:mid]) / mid)
        avg_new  = round(sum(a.get("overall_investment_score",0) for a in sorted_a[mid:]) / (total - mid))
        improvement = avg_new - avg_old
        imp_str  = f"+{improvement}" if improvement >= 0 else str(improvement)
        imp_col  = "#00FFB3" if improvement >= 0 else "#FF4560"
    else:
        imp_str = "N/A"
        imp_col = "#7B92B2"

    month_delta = this_month - last_month
    month_str   = f"+{month_delta}" if month_delta >= 0 else str(month_delta)
    month_col   = "#00FFB3" if month_delta >= 0 else "#FF4560"

    stats = [
        ("🤖", "Total Agent Calls",      str(agent_calls),      "#00D4FF",
         f"{total} analyses × 6 agents"),
        ("🏭", "Favourite Industry",      fav_industry_short,    "#6C63FF",
         f"{ind_counter.most_common(1)[0][1]} analyses" if ind_counter else ""),
        ("📅", "This Month",             str(this_month),        "#F59E0B",
         f"{month_str} vs last month"),
        ("📈", "Score Improvement",       imp_str,               imp_col,
         "first half vs second half"),
    ]

    cols = st.columns(4)
    for col, (icon, label, val, color, sub) in zip(cols, stats):
        with col:
            st.markdown(
                f'<div style="background:#0D1B2E;border:1px solid #1A2F4A;'
                f'border-left:3px solid {color};border-radius:10px;padding:1rem 1.1rem;">'
                f'<div style="font-size:1.3rem;margin-bottom:0.4rem;">{icon}</div>'
                f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:1.4rem;'
                f'font-weight:600;color:{color};line-height:1.1;margin-bottom:0.3rem;">{val}</div>'
                f'<div style="font-size:0.7rem;font-weight:600;color:#F0F6FF;'
                f'margin-bottom:0.2rem;">{label}</div>'
                f'<div style="font-size:0.65rem;color:#3A4F6A;">{sub}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ── FEATURE 7: SHARED REPORTS ─────────────────────────────────────────────────

def _render_shared_reports(analyses: list):
    public = [a for a in analyses if a.get("is_public")]

    st.markdown(
        '<div style="font-size:0.65rem;color:#3A4F6A;text-transform:uppercase;'
        'letter-spacing:0.18em;font-weight:600;margin-bottom:1rem;">SHARED REPORTS</div>',
        unsafe_allow_html=True,
    )

    if not public:
        st.markdown(
            '<div style="background:#0D1B2E;border:1px dashed #1A2F4A;border-radius:10px;'
            'padding:1.5rem;text-align:center;">'
            '<div style="font-size:1.5rem;margin-bottom:0.5rem;">🔗</div>'
            '<div style="font-size:0.85rem;color:#7B92B2;">'
            'No public reports yet. Save an analysis and click Share Link to create one.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    base_url = st.secrets.get("app", {}).get("base_url", "")

    st.markdown(
        f'<div style="font-size:0.8rem;color:#7B92B2;margin-bottom:0.8rem;">'
        f'{len(public)} public report{"s" if len(public) != 1 else ""} — '
        f'anyone with the link can view these without signing in.</div>',
        unsafe_allow_html=True,
    )

    for a in public[:5]:  # show max 5
        from components.gauge import get_score_color
        name      = a.get("startup_name", "Unnamed")
        score     = a.get("overall_investment_score", 0)
        token     = a.get("public_token", "")
        score_col = get_score_color(score)
        share_url = f"{base_url}?token={token}" if token else ""

        st.markdown(
            f'<div style="background:#0D1B2E;border:1px solid #1A2F4A;border-radius:10px;'
            f'padding:0.9rem 1.2rem;margin-bottom:0.6rem;'
            f'display:flex;align-items:center;justify-content:space-between;gap:1rem;">'
            f'<div style="display:flex;align-items:center;gap:0.8rem;">'
            f'<span style="font-size:1rem;">🔗</span>'
            f'<div>'
            f'<div style="font-size:0.88rem;font-weight:700;color:#F0F6FF;">{name}</div>'
            f'<div style="font-size:0.7rem;color:#7B92B2;">Score: '
            f'<span style="color:{score_col};font-weight:600;">{score}/100</span></div>'
            f'</div></div>'
            f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.65rem;'
            f'color:#3A4F6A;word-break:break-all;max-width:300px;">'
            f'{share_url[:60] + "..." if len(share_url) > 60 else share_url}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if share_url:
            col_copy, _ = st.columns([1, 4])
            with col_copy:
                st.code(share_url, language=None)


# ── HELPERS ────────────────────────────────────────────────────────────────────

def _parse_month(created_at: str):
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        return (dt.year, dt.month)
    except Exception:
        return (0, 0)


def _divider():
    st.markdown(
        '<div style="height:1px;'
        'background:linear-gradient(90deg,transparent,#1A2F4A,transparent);'
        'margin:1.8rem 0;"></div>',
        unsafe_allow_html=True,
    )
