"""
InvestIQ AI — Radar Chart Component
5-dimension radar chart for visualizing agent scores.
Supports single analysis and overlay comparison mode.
"""

import plotly.graph_objects as go
import streamlit as st


_DIMENSIONS = ["Market", "Competition", "Financial", "Risk", "Innovation"]
_SCORE_KEYS = [
    "market_score",
    "competition_score",
    "financial_score",
    "risk_score",
    "innovation_score",
]


def _get_values(result: dict) -> list:
    """Extract agent scores from result dict in radar dimension order."""
    return [result.get(k, 5) for k in _SCORE_KEYS]


def render_radar(result: dict, height: int = 380) -> None:
    """
    Render single-analysis radar chart.

    Args:
        result: Assembled final result dict.
        height: Chart height in pixels.
    """
    values = _get_values(result)
    cats = _DIMENSIONS + [_DIMENSIONS[0]]   # close the polygon
    vals = values + [values[0]]

    fig = go.Figure()

    # Filled area
    fig.add_trace(go.Scatterpolar(
        r=vals,
        theta=cats,
        fill="toself",
        fillcolor="rgba(0, 212, 255, 0.10)",
        line=dict(color="#00D4FF", width=2.5),
        marker=dict(color="#00D4FF", size=7, symbol="circle"),
        name="Score",
        hovertemplate="<b>%{theta}</b><br>Score: %{r}/10<extra></extra>",
    ))

    # Reference ring at 5 (midpoint)
    ref_vals = [5] * 6
    fig.add_trace(go.Scatterpolar(
        r=ref_vals,
        theta=cats,
        fill="none",
        line=dict(color="#1A2F4A", width=1, dash="dot"),
        showlegend=False,
        hoverinfo="skip",
    ))

    fig.update_layout(
        polar=dict(
            bgcolor="#0D1B2E",
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                tickvals=[2, 4, 6, 8, 10],
                ticktext=["2", "4", "6", "8", "10"],
                color="#3A4F6A",
                gridcolor="#1A2F4A",
                linecolor="#1A2F4A",
                tickfont={"color": "#3A4F6A", "size": 9, "family": "Space Grotesk"},
            ),
            angularaxis=dict(
                color="#7B92B2",
                gridcolor="#1A2F4A",
                linecolor="#1A2F4A",
                tickfont={"color": "#7B92B2", "size": 11, "family": "Space Grotesk",
                          "weight": 600},
            ),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#F0F6FF", "family": "Space Grotesk"},
        showlegend=False,
        height=height,
        margin=dict(t=40, b=40, l=60, r=60),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_comparison_radar(result_a: dict, result_b: dict,
                             name_a: str = "Startup A",
                             name_b: str = "Startup B",
                             height: int = 420) -> None:
    """
    Render overlaid radar chart for comparing two startups.

    Args:
        result_a: First assembled result dict.
        result_b: Second assembled result dict.
        name_a:   Label for first startup.
        name_b:   Label for second startup.
        height:   Chart height.
    """
    vals_a = _get_values(result_a)
    vals_b = _get_values(result_b)
    cats = _DIMENSIONS + [_DIMENSIONS[0]]
    va = vals_a + [vals_a[0]]
    vb = vals_b + [vals_b[0]]

    fig = go.Figure()

    # Startup A — Cyan
    fig.add_trace(go.Scatterpolar(
        r=va, theta=cats,
        fill="toself",
        fillcolor="rgba(0, 212, 255, 0.10)",
        line=dict(color="#00D4FF", width=2.5),
        marker=dict(color="#00D4FF", size=6),
        name=name_a,
        hovertemplate=f"<b>{name_a}</b><br>%{{theta}}: %{{r}}/10<extra></extra>",
    ))

    # Startup B — Violet
    fig.add_trace(go.Scatterpolar(
        r=vb, theta=cats,
        fill="toself",
        fillcolor="rgba(108, 99, 255, 0.10)",
        line=dict(color="#6C63FF", width=2.5),
        marker=dict(color="#6C63FF", size=6),
        name=name_b,
        hovertemplate=f"<b>{name_b}</b><br>%{{theta}}: %{{r}}/10<extra></extra>",
    ))

    # Reference ring
    fig.add_trace(go.Scatterpolar(
        r=[5]*6, theta=cats,
        fill="none",
        line=dict(color="#1A2F4A", width=1, dash="dot"),
        showlegend=False, hoverinfo="skip",
    ))

    fig.update_layout(
        polar=dict(
            bgcolor="#0D1B2E",
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                tickvals=[2, 4, 6, 8, 10],
                color="#3A4F6A",
                gridcolor="#1A2F4A",
                linecolor="#1A2F4A",
                tickfont={"color": "#3A4F6A", "size": 9, "family": "Space Grotesk"},
            ),
            angularaxis=dict(
                color="#7B92B2",
                gridcolor="#1A2F4A",
                linecolor="#1A2F4A",
                tickfont={"color": "#7B92B2", "size": 11, "family": "Space Grotesk",
                          "weight": 600},
            ),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#F0F6FF", "family": "Space Grotesk"},
        showlegend=True,
        legend=dict(
            bgcolor="rgba(13,27,46,0.9)",
            bordercolor="#1A2F4A",
            borderwidth=1,
            font={"color": "#F0F6FF", "size": 11, "family": "Space Grotesk"},
            x=1.15, y=1.0,
        ),
        height=height,
        margin=dict(t=40, b=40, l=60, r=100),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_score_bar_chart(result: dict, height: int = 260) -> None:
    """
    Alternative horizontal bar chart view of all 5 agent scores.
    Used as a supplementary view on the dashboard.
    """
    values = _get_values(result)
    colors = []
    for v in values:
        pct = (v / 10) * 100
        if pct >= 70:
            colors.append("#00FFB3")
        elif pct >= 45:
            colors.append("#F59E0B")
        else:
            colors.append("#FF4560")

    fig = go.Figure(go.Bar(
        x=values,
        y=_DIMENSIONS,
        orientation="h",
        marker=dict(
            color=colors,
            opacity=0.85,
            line=dict(color="rgba(0,0,0,0)", width=0),
        ),
        text=[f"{v}/10" for v in values],
        textposition="outside",
        textfont={"color": "#7B92B2", "size": 11, "family": "Space Grotesk"},
        hovertemplate="<b>%{y}</b>: %{x}/10<extra></extra>",
    ))

    # Background track bars
    fig.add_trace(go.Bar(
        x=[10]*5,
        y=_DIMENSIONS,
        orientation="h",
        marker=dict(color="rgba(26,47,74,0.4)", line=dict(color="rgba(0,0,0,0)")),
        showlegend=False,
        hoverinfo="skip",
    ))

    fig.update_layout(
        barmode="overlay",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            range=[0, 11.5],
            showgrid=False,
            showticklabels=False,
            zeroline=False,
        ),
        yaxis=dict(
            color="#7B92B2",
            gridcolor="#1A2F4A",
            tickfont={"size": 11, "family": "Space Grotesk", "color": "#7B92B2"},
        ),
        height=height,
        margin=dict(t=10, b=10, l=10, r=50),
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})