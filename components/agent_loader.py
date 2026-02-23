"""
InvestIQ AI — Agent Loader Component
Animated loading screen that shows each agent activating sequentially.
Uses Streamlit's native empty() + markdown for live updates.
"""

import time
import streamlit as st
from typing import Callable


# ── AGENT DISPLAY CONFIG ───────────────────────────────────────────────────────

AGENT_DISPLAY = [
    {
        "key": "market",
        "icon": "🔍",
        "name": "Market Intelligence",
        "model": "llama-3.3-70b · Groq",
        "msg": "Analyzing market size, timing & demand signals...",
    },
    {
        "key": "competition",
        "icon": "⚔️",
        "name": "Competitive Landscape",
        "model": "llama-3.3-70b · Groq",
        "msg": "Mapping competitors, moats & differentiation...",
    },
    {
        "key": "financial",
        "icon": "💰",
        "name": "Financial Viability",
        "model": "llama-3.3-70b · Groq",
        "msg": "Evaluating business model & unit economics...",
    },
    {
        "key": "risk",
        "icon": "⚠️",
        "name": "Risk Assessment",
        "model": "deepseek-r1 · Groq",
        "msg": "Running deep risk reasoning across all dimensions...",
    },
    {
        "key": "innovation",
        "icon": "💡",
        "name": "Innovation Scout",
        "model": "llama-3.3-70b · Groq",
        "msg": "Assessing novelty, defensibility & differentiation...",
    },
    {
        "key": "synthesis",
        "icon": "🏛️",
        "name": "Investment Committee",
        "model": "Gemini 2.5 Flash",
        "msg": "Synthesizing all agent reports into final decision...",
    },
]


# ── CARD RENDERER ─────────────────────────────────────────────────────────────

def _render_agent_card(agent: dict, status: str, elapsed: float = 0.0) -> str:
    """
    Build the HTML string for a single agent card.

    status: "pending" | "active" | "complete" | "error"
    """
    if status == "complete":
        border = "rgba(0, 255, 179, 0.35)"
        bg = "rgba(0, 255, 179, 0.04)"
        icon_color = "#00FFB3"
        status_text = f"✓ Complete — {elapsed}s"
        status_color = "#00FFB3"
        name_color = "#F0F6FF"
        dot = ""

    elif status == "active":
        border = "#00D4FF"
        bg = "rgba(0, 212, 255, 0.06)"
        icon_color = "#00D4FF"
        status_text = agent["msg"]
        status_color = "#00D4FF"
        name_color = "#00D4FF"
        dot = """<span style="
            display:inline-block;
            width:6px; height:6px;
            background:#00D4FF;
            border-radius:50%;
            margin-right:5px;
            animation:pulse 1s infinite;
        "></span>"""

    elif status == "error":
        border = "rgba(255, 69, 96, 0.35)"
        bg = "rgba(255, 69, 96, 0.04)"
        icon_color = "#FF4560"
        status_text = "⚠ Error — using fallback score"
        status_color = "#FF4560"
        name_color = "#F0F6FF"
        dot = ""

    else:  # pending
        border = "#1A2F4A"
        bg = "#0D1B2E"
        icon_color = "#3A4F6A"
        status_text = "Waiting..."
        status_color = "#3A4F6A"
        name_color = "#3A4F6A"
        dot = ""

    return f"""
    <div style="
        background:{bg};
        border:1px solid {border};
        border-radius:10px;
        padding:0.8rem 1.2rem;
        margin:0.35rem 0;
        display:flex;
        align-items:center;
        gap:1rem;
        transition:all 0.3s ease;
    ">
        <div style="
            font-size:1.3rem;
            width:2.2rem;
            text-align:center;
            color:{icon_color};
            flex-shrink:0;
        ">{agent['icon']}</div>

        <div style="flex:1; min-width:0;">
            <div style="
                font-size:0.9rem;
                font-weight:600;
                color:{name_color};
                margin-bottom:0.15rem;
                font-family:'Space Grotesk', sans-serif;
            ">{agent['name']}</div>
            <div style="
                font-size:0.72rem;
                color:{status_color};
                font-family:'Space Grotesk', sans-serif;
            ">{dot}{status_text}</div>
        </div>

        <div style="
            font-size:0.62rem;
            color:#3A4F6A;
            text-align:right;
            flex-shrink:0;
            font-family:'Space Grotesk', sans-serif;
        ">{agent['model']}</div>
    </div>
    """


def _build_loader_html(agent_states: dict) -> str:
    """Build the complete loader panel HTML from current agent states."""
    cards_html = ""
    for agent in AGENT_DISPLAY:
        key = agent["key"]
        state = agent_states.get(key, {"status": "pending", "elapsed": 0.0})
        cards_html += _render_agent_card(agent, state["status"], state.get("elapsed", 0.0))

    return f"""
    <style>
    @keyframes pulse {{
        0%, 100% {{ opacity:1; transform:scale(1); }}
        50% {{ opacity:0.4; transform:scale(0.85); }}
    }}
    </style>
    <div style="
        background:#0D1B2E;
        border:1px solid #1A2F4A;
        border-radius:14px;
        padding:1.5rem;
        max-width:680px;
        margin:0 auto;
    ">
        <div style="
            text-align:center;
            margin-bottom:1.2rem;
        ">
            <div style="
                font-size:0.65rem;
                color:#3A4F6A;
                text-transform:uppercase;
                letter-spacing:0.18em;
                font-weight:600;
                margin-bottom:0.3rem;
            ">MULTI-AGENT ANALYSIS IN PROGRESS</div>
            <div style="
                font-size:0.8rem;
                color:#7B92B2;
            ">Each specialist agent is independently evaluating the startup</div>
        </div>
        {cards_html}
    </div>
    """


# ── MAIN LOADER ───────────────────────────────────────────────────────────────

class AgentLoader:
    """
    Context manager / controller for the animated agent loader.

    Usage:
        loader = AgentLoader()
        loader.init()

        loader.set_active("market")
        result = run_market_agent(data)
        loader.set_complete("market", elapsed=2.3)

        ...

        loader.finish()
    """

    def __init__(self):
        self._placeholder = None
        self._states = {
            a["key"]: {"status": "pending", "elapsed": 0.0}
            for a in AGENT_DISPLAY
        }

    def init(self):
        """Create the Streamlit placeholder and render initial state."""
        self._placeholder = st.empty()
        self._render()

    def set_active(self, key: str):
        """Mark an agent as currently running."""
        self._states[key] = {"status": "active", "elapsed": 0.0}
        self._render()

    def set_complete(self, key: str, elapsed: float = 0.0):
        """Mark an agent as successfully completed."""
        self._states[key] = {"status": "complete", "elapsed": round(elapsed, 1)}
        self._render()

    def set_error(self, key: str):
        """Mark an agent as errored (used fallback)."""
        self._states[key] = {"status": "error", "elapsed": 0.0}
        self._render()

    def finish(self):
        """Clear the loader placeholder after pipeline completes."""
        if self._placeholder:
            self._placeholder.empty()

    def _render(self):
        if self._placeholder:
            self._placeholder.markdown(
                _build_loader_html(self._states),
                unsafe_allow_html=True,
            )


# ── PIPELINE RUNNER WITH LOADER ───────────────────────────────────────────────

def run_pipeline_with_loader(startup_data: dict) -> dict:
    """
    Run the full analysis pipeline while displaying the animated loader.

    Returns the assembled final result dict ready for dashboard rendering.
    """
    from ai.pipeline import run_pipeline, assemble_final_result

    loader = AgentLoader()

    # Header above loader
    st.markdown("""
    <div style="text-align:center; margin:1.5rem 0 1rem 0;">
        <div style="
            font-size:1.3rem;
            font-weight:700;
            color:#F0F6FF;
            margin-bottom:0.3rem;
            font-family:'Space Grotesk', sans-serif;
        ">Analyzing Startup</div>
        <div style="color:#7B92B2; font-size:0.85rem;">
            This typically takes 20–40 seconds
        </div>
    </div>
    """, unsafe_allow_html=True)

    loader.init()

    # ── Pipeline callbacks ─────────────────────────────────────────────────────

    def on_start(key, name, msg):
        loader.set_active(key)

    def on_complete(key, result, elapsed):
        loader.set_complete(key, elapsed)

    def on_error(key, error_msg):
        loader.set_error(key)

    # ── Run pipeline ───────────────────────────────────────────────────────────
    pipeline_output = run_pipeline(
        startup_data=startup_data,
        on_agent_start=on_start,
        on_agent_complete=on_complete,
        on_agent_error=on_error,
    )

    # Brief pause so user can see all agents complete before dashboard loads
    time.sleep(0.8)
    loader.finish()

    return assemble_final_result(pipeline_output)