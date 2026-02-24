"""
InvestIQ AI — Agent Definitions
All 6 investment analysis agents with their prompts and API calls.

Model routing is now user-configurable via model_config dict:
  {
    "provider":     "groq" | "gemini",
    "groq_model":   key from GROQ_MODELS,
    "gemini_model": key from GEMINI_MODELS,
    "synthesizer":  "groq" | "gemini"
  }

Defaults (when no config passed):
  Agents 1-5 → Groq llama-3.3-70b-versatile  (fastest)
  Agent 4    → Groq deepseek-r1 always        (deep risk reasoning)
  Agent 6    → Gemini 2.5 Flash               (deepest synthesis)
"""

import json
import re
import streamlit as st
from groq import Groq
import google.generativeai as genai


# ── AVAILABLE MODELS (shown in UI dropdowns) ───────────────────────────────────

GROQ_MODELS = {
    "llama-3.3-70b-versatile":       "Llama 3.3 70B  ⚡ Fastest · Recommended",
    "llama-3.1-8b-instant":          "Llama 3.1 8B   ⚡⚡ Ultra Fast · Lighter",
    "deepseek-r1-distill-llama-70b": "DeepSeek R1 70B 🧠 Deep Reasoning",
    "gemma2-9b-it":                  "Gemma 2 9B     🔵 Google · Fast",
    "mixtral-8x7b-32768":            "Mixtral 8x7B   📄 Long Context",
}

GEMINI_MODELS = {
    "gemini-2.5-flash": "Gemini 2.5 Flash  ⚡ Fastest · Recommended",
    "gemini-2.0-flash": "Gemini 2.0 Flash  🔵 Stable · Fast",
    "gemini-1.5-flash": "Gemini 1.5 Flash  💨 Lightweight",
}

DEFAULT_CONFIG = {
    "provider":     "groq",
    "groq_model":   "llama-3.3-70b-versatile",
    "gemini_model": "gemini-2.5-flash",
    "synthesizer":  "gemini",
}


# ── CLIENT INIT ────────────────────────────────────────────────────────────────

def get_groq_client() -> Groq:
    return Groq(api_key=st.secrets["groq"]["api_key"])


def get_gemini_model_client(model_name: str = "gemini-2.5-flash"):
    genai.configure(api_key=st.secrets["google"]["api_key"])
    return genai.GenerativeModel(model_name)


# ── SHARED HELPERS ─────────────────────────────────────────────────────────────

def _build_startup_context(data: dict) -> str:
    return (
        f"Startup Name: {data.get('startup_name', 'N/A')}\n"
        f"Description: {data.get('description', 'N/A')}\n"
        f"Industry: {data.get('industry', 'N/A')}\n"
        f"Target Market: {data.get('target_market', 'N/A')}\n"
        f"Business Model: {data.get('business_model', 'N/A')}\n"
        f"Revenue Model: {data.get('revenue_model', 'N/A')}\n"
        f"Funding Stage: {data.get('funding_stage', 'N/A')}"
    ).strip()


def _extract_json(text: str) -> dict:
    """Robustly extract JSON from model response."""
    text = re.sub(r"```(?:json)?", "", text).strip()
    text = text.replace("```", "").strip()
    # Strip DeepSeek <think> blocks
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    cleaned = re.sub(r",\s*}", "}", text.replace("'", '"'))
    cleaned = re.sub(r",\s*]", "]", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {}


def _call_groq(system_prompt: str, user_prompt: str,
               model: str = "llama-3.3-70b-versatile",
               temperature: float = 0.25) -> str:
    client = get_groq_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=1024,   # trimmed for speed
    )
    return response.choices[0].message.content.strip()


def _call_gemini(prompt: str, model_name: str = "gemini-2.5-flash",
                 temperature: float = 0.2) -> str:
    model = get_gemini_model_client(model_name)
    cfg = genai.types.GenerationConfig(
        temperature=temperature,
        max_output_tokens=1500,
    )
    response = model.generate_content(prompt, generation_config=cfg)
    return response.text.strip()


def _call_any(system_prompt: str, user_prompt: str,
              cfg: dict, temperature: float = 0.25) -> str:
    """Route call to Groq or Gemini based on cfg['provider']."""
    provider = cfg.get("provider", "groq")

    if provider == "gemini":
        gem_model = cfg.get("gemini_model", "gemini-2.5-flash")
        try:
            return _call_gemini(
                f"{system_prompt}\n\n{user_prompt}",
                model_name=gem_model,
                temperature=temperature,
            )
        except Exception as e:
            print(f"Gemini failed, falling back to Groq: {e}")

    groq_model = cfg.get("groq_model", "llama-3.3-70b-versatile")
    return _call_groq(system_prompt, user_prompt,
                      model=groq_model, temperature=temperature)


def _run_with_retry(call_fn, fallback: dict, max_retries: int = 2) -> dict:
    for attempt in range(max_retries):
        try:
            raw = call_fn(attempt)
            result = _extract_json(raw)
            if result:
                return result
        except Exception as e:
            print(f"Agent attempt {attempt + 1} failed: {e}")
    return fallback


# ── AGENT 1: MARKET INTELLIGENCE ───────────────────────────────────────────────

_MARKET_SYS = """You are a senior Market Intelligence Analyst at a top-tier VC firm.
Evaluate the MARKET OPPORTUNITY. Be direct. Return ONLY valid JSON, nothing else.
market_score: 10=massive proven market, 0=no viable market.

{"market_score":<0-10>,"confidence":<0-10>,"market_analysis":"<3-4 sentences>","market_size_signal":"<Large/Medium/Niche>","timing_assessment":"<Early Mover/Right Time/Late Entry>","market_growth":"<High Growth/Stable/Declining>","key_insight":"<1 sharp sentence>"}"""


def run_market_agent(startup_data: dict, model_config: dict = None) -> dict:
    cfg = model_config or DEFAULT_CONFIG
    ctx = _build_startup_context(startup_data)
    fallback = {"market_score": 5, "confidence": 0,
                "market_analysis": "Unavailable.", "market_size_signal": "Unknown",
                "timing_assessment": "Unknown", "market_growth": "Unknown",
                "key_insight": "Unavailable."}
    def call(attempt):
        note = " RETURN ONLY JSON." if attempt > 0 else ""
        return _call_any(_MARKET_SYS + note,
                         f"Analyze market opportunity:\n{ctx}", cfg, 0.25)
    return _run_with_retry(call, fallback)


# ── AGENT 2: COMPETITIVE LANDSCAPE ────────────────────────────────────────────

_COMPETITION_SYS = """You are a Competitive Intelligence Specialist at a leading VC fund.
Evaluate the COMPETITIVE LANDSCAPE. Be direct. Return ONLY valid JSON, nothing else.
competition_score: 10=near-monopoly, 0=red ocean with giants.

{"competition_score":<0-10>,"confidence":<0-10>,"competition_analysis":"<3-4 sentences>","competitive_intensity":"<Low/Medium/High/Extreme>","moat_assessment":"<Strong/Moderate/Weak/None>","big_tech_risk":"<High/Medium/Low>","key_insight":"<1 sharp sentence>"}"""


def run_competition_agent(startup_data: dict, model_config: dict = None) -> dict:
    cfg = model_config or DEFAULT_CONFIG
    ctx = _build_startup_context(startup_data)
    fallback = {"competition_score": 5, "confidence": 0,
                "competition_analysis": "Unavailable.", "competitive_intensity": "Unknown",
                "moat_assessment": "Unknown", "big_tech_risk": "Unknown",
                "key_insight": "Unavailable."}
    def call(attempt):
        note = " RETURN ONLY JSON." if attempt > 0 else ""
        return _call_any(_COMPETITION_SYS + note,
                         f"Analyze competitive landscape:\n{ctx}", cfg, 0.25)
    return _run_with_retry(call, fallback)


# ── AGENT 3: FINANCIAL VIABILITY ───────────────────────────────────────────────

_FINANCIAL_SYS = """You are a Financial Due Diligence Analyst at a top-tier VC fund.
Evaluate FINANCIAL VIABILITY. Be direct. Return ONLY valid JSON, nothing else.
financial_score: 10=exceptional model, 0=broken economics.

{"financial_score":<0-10>,"confidence":<0-10>,"financial_analysis":"<3-4 sentences>","revenue_model_quality":"<Excellent/Good/Weak/Unclear>","scalability":"<High/Medium/Low>","margin_potential":"<High/Medium/Low>","capital_efficiency":"<Efficient/Moderate/Capital Intensive>","key_insight":"<1 sharp sentence>"}"""


def run_financial_agent(startup_data: dict, model_config: dict = None) -> dict:
    cfg = model_config or DEFAULT_CONFIG
    ctx = _build_startup_context(startup_data)
    fallback = {"financial_score": 5, "confidence": 0,
                "financial_analysis": "Unavailable.", "revenue_model_quality": "Unknown",
                "scalability": "Unknown", "margin_potential": "Unknown",
                "capital_efficiency": "Unknown", "key_insight": "Unavailable."}
    def call(attempt):
        note = " RETURN ONLY JSON." if attempt > 0 else ""
        return _call_any(_FINANCIAL_SYS + note,
                         f"Evaluate financial viability:\n{ctx}", cfg, 0.2)
    return _run_with_retry(call, fallback)


# ── AGENT 4: RISK ASSESSMENT ───────────────────────────────────────────────────

_RISK_SYS = """You are a Risk Management Partner at a top global investment firm.
Conduct RISK ASSESSMENT. Be direct. Return ONLY valid JSON, nothing else.
risk_score: 10=very LOW risk, 0=extremely HIGH risk.

{"risk_score":<0-10>,"confidence":<0-10>,"risk_analysis":"<3-4 sentences>","primary_risk":"<most likely failure mode>","risk_level":"<Low/Medium/High/Critical>","execution_risk":"<Low/Medium/High>","regulatory_risk":"<Low/Medium/High>","key_insight":"<1 sharp sentence>"}"""


def run_risk_agent(startup_data: dict, model_config: dict = None) -> dict:
    cfg = model_config or DEFAULT_CONFIG
    ctx = _build_startup_context(startup_data)
    fallback = {"risk_score": 5, "confidence": 0,
                "risk_analysis": "Unavailable.", "primary_risk": "Unavailable.",
                "risk_level": "Unknown", "execution_risk": "Unknown",
                "regulatory_risk": "Unknown", "key_insight": "Unavailable."}
    # Risk always uses DeepSeek when Groq is provider (best reasoning)
    risk_cfg = dict(cfg)
    if risk_cfg.get("provider") == "groq":
        risk_cfg["groq_model"] = "deepseek-r1-distill-llama-70b"
    def call(attempt):
        note = " RETURN ONLY JSON." if attempt > 0 else ""
        return _call_any(_RISK_SYS + note,
                         f"Risk assessment:\n{ctx}", risk_cfg, 0.2)
    return _run_with_retry(call, fallback)


# ── AGENT 5: INNOVATION SCOUT ──────────────────────────────────────────────────

_INNOVATION_SYS = """You are an Innovation Scout at a deep-tech VC fund.
Assess INNOVATION QUALITY and DIFFERENTIATION. Be direct. Return ONLY valid JSON, nothing else.
innovation_score: 10=category-defining, 0=commodity copy.

{"innovation_score":<0-10>,"confidence":<0-10>,"innovation_analysis":"<3-4 sentences>","innovation_type":"<Category Creator/Market Disruptor/Model Innovator/Incremental Improver/Commodity>","defensibility":"<Strong/Moderate/Weak>","unfair_advantage_signal":"<Strong/Moderate/Weak/None Visible>","key_insight":"<1 sharp sentence>"}"""


def run_innovation_agent(startup_data: dict, model_config: dict = None) -> dict:
    cfg = model_config or DEFAULT_CONFIG
    ctx = _build_startup_context(startup_data)
    fallback = {"innovation_score": 5, "confidence": 0,
                "innovation_analysis": "Unavailable.", "innovation_type": "Unknown",
                "defensibility": "Unknown", "unfair_advantage_signal": "Unknown",
                "key_insight": "Unavailable."}
    def call(attempt):
        note = " RETURN ONLY JSON." if attempt > 0 else ""
        return _call_any(_INNOVATION_SYS + note,
                         f"Assess innovation:\n{ctx}", cfg, 0.3)
    return _run_with_retry(call, fallback)


# ── AGENT 6: INVESTMENT COMMITTEE SYNTHESIZER ──────────────────────────────────

def run_synthesizer_agent(startup_data: dict, agent_results: dict,
                           model_config: dict = None) -> dict:
    """Agent 6: Synthesize all 5 outputs into final investment decision."""
    cfg = model_config or DEFAULT_CONFIG
    fallback = {
        "overall_investment_score": 50, "final_recommendation": "Consider",
        "confidence_level": "Low",
        "decision_reasoning": "Synthesis unavailable. Review individual agent scores.",
        "strengths": ["See individual reports."],
        "weaknesses": ["Synthesis error."],
        "recommended_actions": ["Re-run analysis."],
        "one_line_verdict": "Incomplete — retry for full decision.",
    }

    m = agent_results.get("market", {})
    c = agent_results.get("competition", {})
    f = agent_results.get("financial", {})
    r = agent_results.get("risk", {})
    i = agent_results.get("innovation", {})
    ctx = _build_startup_context(startup_data)

    prompt = f"""You are the Chairperson of an Investment Committee at a top global VC fund.
Five agents completed analysis. Synthesize into a final investment decision.

STARTUP: {ctx}

AGENT SCORES & ANALYSES:
Market {m.get('market_score',5)}/10: {m.get('market_analysis','')} Key: {m.get('key_insight','')}
Competition {c.get('competition_score',5)}/10: {c.get('competition_analysis','')} Key: {c.get('key_insight','')}
Financial {f.get('financial_score',5)}/10: {f.get('financial_analysis','')} Key: {f.get('key_insight','')}
Risk {r.get('risk_score',5)}/10 (10=low risk): {r.get('risk_analysis','')} Primary: {r.get('primary_risk','')}
Innovation {i.get('innovation_score',5)}/10: {i.get('innovation_analysis','')} Key: {i.get('key_insight','')}

SCORING: overall=(market*10*0.25)+(competition*10*0.20)+(financial*10*0.25)+(risk*10*0.20)+(innovation*10*0.10)
70-100=>"Strong Invest" | 45-69=>"Consider" | 0-44=>"Reject"
avg_confidence>=7=>"High" | 4-6=>"Medium" | <4=>"Low"

Return ONLY valid JSON:
{{"overall_investment_score":<0-100>,"final_recommendation":"<Strong Invest/Consider/Reject>","confidence_level":"<High/Medium/Low>","decision_reasoning":"<5-6 sentence executive reasoning>","strengths":["<s1>","<s2>","<s3>"],"weaknesses":["<w1>","<w2>","<w3>"],"recommended_actions":["<a1>","<a2>","<a3>"],"one_line_verdict":"<sharp one-line verdict>"}}"""

    synth_provider = cfg.get("synthesizer", "gemini")

    def call(attempt):
        p = prompt + (" ONLY JSON." if attempt > 0 else "")
        if synth_provider == "groq":
            groq_model = cfg.get("groq_model", "llama-3.3-70b-versatile")
            return _call_groq(
                "You are an investment committee synthesizer. Return ONLY valid JSON.",
                p, model=groq_model, temperature=0.2,
            )
        else:
            gem_model = cfg.get("gemini_model", "gemini-2.5-flash")
            return _call_gemini(p, model_name=gem_model, temperature=0.2)

    return _run_with_retry(call, fallback)
