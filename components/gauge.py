"""
InvestIQ AI — Score Gauge Component
Large animated Plotly gauge for the overall investment score (0-100).
"""

import plotly.graph_objects as go
import streamlit as st


def get_score_color(score: float) -> str:
    """Return the primary color for a given score."""
    if score >= 70:
        return "#00FFB3"
    elif score >= 45:
        return "#F59E0B"
    else:
        return "#FF4560"


def get_score_glow(score: float) -> str:
    """Return glow/shadow color for a given score."""
    if score >= 70:
        return "rgba(0, 255, 179, 0.35)"
    elif score >= 45:
        return "rgba(245, 158, 11, 0.35)"
    else:
        return "rgba(255, 69, 96, 0.35)"


def render_gauge(score: int, height: int = 320) -> None:
    """
    Render the main investment score gauge.

    Args:
        score:  Overall investment score 0-100.
        height: Chart height in pixels.
    """
    color = get_score_color(score)

    # ── Step background zones ──────────────────────────────────────────────────
    steps = [
        {"range": [0, 44],  "color": "rgba(255,69,96,0.06)"},
        {"range": [44, 70], "color": "rgba(245,158,11,0.06)"},
        {"range": [70, 100],"color": "rgba(0,255,179,0.06)"},
    ]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        number={
            "font": {
                "size": 68,
                "color": color,
                "family": "Space Grotesk, sans-serif",
            },
            "suffix": "",
        },
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": "#1A2F4A",
                "tickfont": {"color": "#3A4F6A", "size": 10, "family": "Space Grotesk"},
                "nticks": 6,
            },
            "bar": {
                "color": color,
                "thickness": 0.22,
            },
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "bordercolor": "rgba(0,0,0,0)",
            "steps": steps,
            "threshold": {
                "line": {"color": color, "width": 3},
                "thickness": 0.82,
                "value": score,
            },
        },
    ))

    # Zone labels below gauge
    fig.add_annotation(
        x=0.12, y=0.08, text="REJECT",
        showarrow=False,
        font={"size": 9, "color": "#FF4560", "family": "Space Grotesk"},
    )
    fig.add_annotation(
        x=0.5, y=0.0, text="CONSIDER",
        showarrow=False,
        font={"size": 9, "color": "#F59E0B", "family": "Space Grotesk"},
    )
    fig.add_annotation(
        x=0.88, y=0.08, text="INVEST",
        showarrow=False,
        font={"size": 9, "color": "#00FFB3", "family": "Space Grotesk"},
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#F0F6FF", "family": "Space Grotesk"},
        height=height,
        margin=dict(t=30, b=10, l=20, r=20),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_mini_gauge(score: float, max_val: int = 10,
                      label: str = "", height: int = 160) -> None:
    """
    Render a compact mini gauge for individual agent scores (0-10).

    Args:
        score:   Score value.
        max_val: Maximum value (10 for agent scores).
        label:   Label text below.
        height:  Chart height.
    """
    normalized = (score / max_val) * 100
    color = get_score_color(normalized)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        number={
            "font": {
                "size": 32,
                "color": color,
                "family": "Space Grotesk",
            },
            "suffix": f"/{max_val}",
        },
        gauge={
            "axis": {
                "range": [0, max_val],
                "visible": False,
            },
            "bar": {"color": color, "thickness": 0.3},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, max_val * 0.44], "color": "rgba(255,69,96,0.06)"},
                {"range": [max_val * 0.44, max_val * 0.70], "color": "rgba(245,158,11,0.06)"},
                {"range": [max_val * 0.70, max_val], "color": "rgba(0,255,179,0.06)"},
            ],
        },
    ))

    if label:
        fig.add_annotation(
            x=0.5, y=-0.15, text=label,
            showarrow=False,
            font={"size": 10, "color": "#7B92B2", "family": "Space Grotesk"},
            xref="paper", yref="paper",
        )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(t=10, b=20, l=10, r=10),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_score_hero(result: dict) -> None:
    """
    Render the complete hero section:
    gauge + recommendation pill + confidence badge + verdict text.

    Args:
        result: Assembled final result dict from pipeline.assemble_final_result()
    """
    score = result.get("overall_investment_score", 0)
    recommendation = result.get("final_recommendation", "Consider")
    confidence = result.get("confidence_level", "Medium")
    verdict = result.get("one_line_verdict", "")
    color = get_score_color(score)

    # Centered wrapper
    st.markdown(f"""
    <div style="
        background: #0D1B2E;
        border: 1px solid #1A2F4A;
        border-radius: 16px;
        padding: 2rem 1.5rem 1rem 1.5rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    ">
        <!-- subtle glow behind gauge -->
        <div style="
            position: absolute;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            width: 300px; height: 300px;
            background: radial-gradient(circle, {get_score_glow(score)} 0%, transparent 70%);
            pointer-events: none;
        "></div>

        <div style="
            font-size: 0.65rem;
            color: #3A4F6A;
            text-transform: uppercase;
            letter-spacing: 0.18em;
            font-weight: 600;
            margin-bottom: 0.5rem;
        ">INVESTMENT SCORE</div>
    </div>
    """, unsafe_allow_html=True)

    # Gauge chart
    render_gauge(score)

    # Recommendation + Confidence row
    rec_lower = recommendation.lower()
    if "strong invest" in rec_lower or rec_lower == "invest":
        pill_class = "pill-invest"
        pill_icon = "🟢"
    elif "consider" in rec_lower:
        pill_class = "pill-consider"
        pill_icon = "🟡"
    else:
        pill_class = "pill-reject"
        pill_icon = "🔴"

    conf_lower = confidence.lower()
    if conf_lower == "high":
        badge_class = "badge-high"
        badge_icon = "⬆"
    elif conf_lower == "medium":
        badge_class = "badge-medium"
        badge_icon = "➡"
    else:
        badge_class = "badge-low"
        badge_icon = "⬇"

    st.markdown(f"""
    <div style="text-align:center; margin: 0.2rem 0 1rem 0;">
        <span class="{pill_class}" style="margin-right:0.8rem;">
            {pill_icon} {recommendation}
        </span>
        <span class="{badge_class}">
            {badge_icon} {confidence} Confidence
        </span>
    </div>
    """, unsafe_allow_html=True)

    # One-line verdict
    if verdict:
        st.markdown(f"""
        <div class="verdict-text" style="text-align:center; max-width:600px; margin:0 auto 1rem auto;">
            "{verdict}"
        </div>
        """, unsafe_allow_html=True)