"""
InvestIQ AI — Agent Loader
Terminal-style execution log — streams live as each agent runs.
Matches the reference UI: macOS bar · timestamps · SYS/AGENT/TASK/DONE tags · status footer.
"""

import re
import time
import streamlit as st


# ── AGENT METADATA ─────────────────────────────────────────────────────────────

AGENT_META = {
    "market": {
        "name": "Market Intelligence",
        "boot": [
            "Instantiating Market Intelligence agent...",
            "Loading market sizing &amp; timing heuristics...",
        ],
        "task": "Scanning TAM/SAM estimates, demand curves, growth signals...",
        "done": "Market analysis complete &mdash; score computed.",
    },
    "competition": {
        "name": "Competitive Landscape",
        "boot": [
            "Instantiating Competitive Landscape agent...",
            "Loading moat &amp; differentiation evaluation matrix...",
        ],
        "task": "Mapping competitor landscape, barriers to entry, Big Tech risk...",
        "done": "Competitive analysis complete &mdash; score computed.",
    },
    "financial": {
        "name": "Financial Viability",
        "boot": [
            "Instantiating Financial Viability agent...",
            "Loading unit economics &amp; scalability models...",
        ],
        "task": "Evaluating revenue model, margin potential, capital efficiency...",
        "done": "Financial analysis complete &mdash; score computed.",
    },
    "risk": {
        "name": "Risk Assessment",
        "boot": [
            "Instantiating Risk Assessment agent (DeepSeek R1)...",
            "Deep reasoning engine initialized &mdash; extended context active...",
        ],
        "task": "Running multi-dimensional risk reasoning: execution &middot; regulatory &middot; macro...",
        "done": "Risk assessment complete &mdash; score computed.",
    },
    "innovation": {
        "name": "Innovation Scout",
        "boot": [
            "Instantiating Innovation Scout agent...",
            "Loading differentiation &amp; defensibility models...",
        ],
        "task": "Assessing novelty, unfair advantage signals, category potential...",
        "done": "Innovation analysis complete &mdash; score computed.",
    },
    "synthesis": {
        "name": "Investment Committee",
        "boot": [
            "Convening Investment Committee (Gemini 2.5 Flash)...",
            "Aggregating all 5 agent reports for final synthesis...",
        ],
        "task": "Computing weighted scores &rarr; generating investment decision...",
        "done": "Committee decision reached &mdash; final report ready.",
    },
}


# ── CSS + ANIMATIONS (injected once) ──────────────────────────────────────────

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap');
@keyframes iq-blink  { 0%,100%{opacity:1} 50%{opacity:0} }
@keyframes iq-spin   { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
@keyframes iq-fadein { from{opacity:0;transform:translateY(4px)} to{opacity:1;transform:translateY(0)} }
.iq-line { animation: iq-fadein 0.18s ease; }
</style>
"""

# Tag definitions: (background, text-color, border)
_TAG = {
    "SYS":   ("rgba(59,130,246,0.13)",  "#93C5FD", "rgba(59,130,246,0.28)"),
    "AGENT": ("rgba(0,212,255,0.12)",   "#00D4FF", "rgba(0,212,255,0.28)"),
    "TASK":  ("rgba(245,158,11,0.14)",  "#FBB040", "rgba(245,158,11,0.28)"),
    "DONE":  ("rgba(0,255,179,0.11)",   "#00FFB3", "rgba(0,255,179,0.28)"),
    "ERROR": ("rgba(255,69,96,0.12)",   "#FF4560", "rgba(255,69,96,0.28)"),
}


# ── ROW BUILDER ────────────────────────────────────────────────────────────────

def _row(ts: float, tag: str, msg: str) -> str:
    bg, col, border = _TAG.get(tag, _TAG["SYS"])
    ts_str = f"{ts:.1f}s"
    return (
        f'<div class="iq-line" style="display:flex;align-items:baseline;'
        f'gap:0;padding:0.19rem 0;">'

        # timestamp
        f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:0.62rem;'
        f'color:#2E4A66;min-width:3rem;text-align:right;padding-right:0.7rem;'
        f'flex-shrink:0;">{ts_str}</span>'

        # tag pill
        f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:0.58rem;'
        f'font-weight:600;padding:0.09rem 0.42rem;border-radius:3px;'
        f'background:{bg};color:{col};border:1px solid {border};'
        f'flex-shrink:0;letter-spacing:0.04em;margin-right:0.75rem;">{tag}</span>'

        # message
        f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:0.7rem;'
        f'color:#B8CCE0;line-height:1.5;">{msg}</span>'

        f'</div>'
    )


def _cursor_row() -> str:
    return (
        '<div style="display:flex;align-items:center;padding:0.25rem 0;">'
        '<span style="min-width:3rem;"></span>'
        '<span style="width:7px;height:14px;background:#00D4FF;display:inline-block;'
        'border-radius:1px;animation:iq-blink 1.1s step-end infinite;margin-left:0.7rem;"></span>'
        '</div>'
    )


# ── FULL TERMINAL HTML ─────────────────────────────────────────────────────────

def _terminal(startup_name: str, log_rows: list, status_msg: str) -> str:
    body = "".join(log_rows) + _cursor_row()

    return (
        _CSS

        # Outer wrapper
        + '<div style="max-width:820px;margin:1.8rem auto 0 auto;">'

        # Card
        + '<div style="background:#0C1623;border:1px solid #1C3050;border-radius:13px;'
        + 'overflow:hidden;box-shadow:0 0 60px rgba(0,212,255,0.05);">'

        # ── Title bar ──────────────────────────────────────────────────────────
        + '<div style="background:#0F1E30;padding:0.58rem 1rem;'
        + 'display:flex;align-items:center;gap:0.5rem;border-bottom:1px solid #1C3050;">'
        + '<span style="width:11px;height:11px;border-radius:50%;background:#FF5F57;'
        + 'display:inline-block;flex-shrink:0;"></span>'
        + '<span style="width:11px;height:11px;border-radius:50%;background:#FEBC2E;'
        + 'display:inline-block;flex-shrink:0;"></span>'
        + '<span style="width:11px;height:11px;border-radius:50%;background:#28C840;'
        + 'display:inline-block;flex-shrink:0;"></span>'
        + f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:0.6rem;'
        + f'color:#2E4A66;letter-spacing:0.13em;font-weight:600;margin-left:0.5rem;">'
        + f'DUE DILIGENCE &nbsp;&middot;&nbsp; EXECUTION LOG'
        + f'</span>'
        + '</div>'

        # ── Log body ───────────────────────────────────────────────────────────
        + '<div style="padding:0.85rem 1.1rem 0.4rem 0.6rem;min-height:200px;">'
        + body
        + '</div>'

        # ── Status footer ──────────────────────────────────────────────────────
        + '<div style="padding:0.5rem 1rem 0.85rem 1rem;">'
        + '<div style="background:rgba(0,212,255,0.05);border:1px solid rgba(0,212,255,0.13);'
        + 'border-radius:7px;padding:0.5rem 0.85rem;display:flex;align-items:center;gap:0.6rem;">'
        + '<span style="width:6px;height:6px;border-radius:50%;background:#00D4FF;flex-shrink:0;'
        + 'animation:iq-blink 1.1s step-end infinite;"></span>'
        + f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:0.68rem;'
        + f'color:#5B7A9A;">{status_msg}</span>'
        + '</div>'
        + '</div>'

        + '</div>'   # card
        + '</div>'   # wrapper
    )


# ── AGENT LOADER CLASS ─────────────────────────────────────────────────────────

class AgentLoader:
    def __init__(self, startup_data: dict, model_config: dict):
        self._name    = startup_data.get("startup_name", "Startup")
        self._cfg     = model_config or {}
        self._ph      = None
        self._rows    = []
        self._t0      = time.time()
        self._status  = "Initializing pipeline..."

    # ── internals ─────────────────────────────────────────────────────────────

    def _ts(self) -> float:
        return round(time.time() - self._t0, 1)

    def _add(self, tag: str, msg: str):
        self._rows.append(_row(self._ts(), tag, msg))

    def _flush(self):
        if self._ph:
            self._ph.markdown(
                _terminal(self._name, self._rows, self._status),
                unsafe_allow_html=True,
            )

    def _model_str(self) -> str:
        """Return clean model label for display."""
        try:
            provider = self._cfg.get("provider", "groq")
            if provider == "groq":
                from ai.agents import GROQ_MODELS
                raw = GROQ_MODELS.get(self._cfg.get("groq_model", ""), "Groq")
            else:
                from ai.agents import GEMINI_MODELS
                raw = GEMINI_MODELS.get(self._cfg.get("gemini_model", ""), "Gemini")
            # strip emoji and trailing noise
            clean = re.sub(r'[^\x20-\x7E]', '', raw.split("·")[0]).strip()
            return clean if clean else "AI Model"
        except Exception:
            return "AI Model"

    # ── public API ────────────────────────────────────────────────────────────

    def init(self):
        """Render boot sequence."""
        self._ph = st.empty()
        provider  = self._cfg.get("provider", "groq").upper()
        model     = self._model_str()
        synth     = self._cfg.get("synthesizer", "gemini")
        synth_lbl = "Gemini 2.5 Flash" if synth == "gemini" else model

        boot_seq = [
            ("SYS",   f"Startup: {self._name} &nbsp;&middot;&nbsp; Stage: Analysis"),
            ("SYS",   f"Model: {model} &nbsp;&middot;&nbsp; Provider: {provider} &nbsp;&middot;&nbsp; Depth: Standard"),
            ("AGENT", "Instantiating 6 specialist agents..."),
            ("AGENT", "Market &nbsp;&middot;&nbsp; Competition &nbsp;&middot;&nbsp; Financial &nbsp;&middot;&nbsp; Risk &nbsp;&middot;&nbsp; Innovation &nbsp;&middot;&nbsp; Committee ready"),
            ("TASK",  "6 tasks queued: Market &rarr; Competition &rarr; Financial &rarr; Risk &rarr; Innovation &rarr; Synthesis"),
            ("SYS",   f"Process: Sequential &nbsp;&middot;&nbsp; Synthesizer: {synth_lbl} &nbsp;&middot;&nbsp; Error isolation: enabled"),
        ]
        for tag, msg in boot_seq:
            self._add(tag, msg)
            self._flush()
            time.sleep(0.08)

        self._status = "Agents running due diligence \u2014 this takes 20\u201350 seconds. Six specialists analyzing your startup..."
        self._flush()

    def set_active(self, key: str):
        meta = AGENT_META.get(key, {})
        self._status = f"Running {meta.get('name', key)}..."
        for msg in meta.get("boot", []):
            self._add("AGENT", msg)
            self._flush()
            time.sleep(0.07)
        self._add("TASK", meta.get("task", f"Analyzing {key}..."))
        self._flush()

    def set_complete(self, key: str, elapsed: float = 0.0):
        meta = AGENT_META.get(key, {})
        self._add("DONE", f"{meta.get('done', 'Complete.')} &nbsp;({elapsed}s)")
        self._flush()

    def set_error(self, key: str):
        meta = AGENT_META.get(key, {})
        self._add("ERROR", f"{meta.get('name', key)}: agent error &mdash; fallback score applied")
        self._flush()

    def finish(self):
        self._status = "All agents complete \u2014 building investment dashboard..."
        self._add("DONE", "Pipeline complete. Preparing report...")
        self._flush()
        time.sleep(0.8)
        if self._ph:
            self._ph.empty()


# ── TOP-LEVEL RUNNER ───────────────────────────────────────────────────────────

def run_pipeline_with_loader(startup_data: dict,
                              model_config: dict = None) -> dict:
    from ai.pipeline import run_pipeline, assemble_final_result

    loader = AgentLoader(startup_data, model_config)
    loader.init()

    pipeline_output = run_pipeline(
        startup_data=startup_data,
        on_agent_start=lambda k, n, m: loader.set_active(k),
        on_agent_complete=lambda k, r, e: loader.set_complete(k, round(e, 1)),
        on_agent_error=lambda k, err: loader.set_error(k),
        model_config=model_config,
    )

    loader.finish()
    return assemble_final_result(pipeline_output)
