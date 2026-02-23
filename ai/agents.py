"""
InvestIQ AI — Agent Definitions
All 6 investment analysis agents with their prompts and API calls.

Agent Routing:
  Agent 1,2,3,5 → Groq (llama-3.3-70b-versatile)      [speed]
  Agent 4        → Groq (deepseek-r1-distill-llama-70b) [deep reasoning]
  Agent 6        → Gemini 2.5 Flash                     [synthesis depth]
"""

import json
import re
import streamlit as st
from groq import Groq
import google.generativeai as genai


# ── CLIENT INIT ────────────────────────────────────────────────────────────────

def get_groq_client() -> Groq:
    return Groq(api_key=st.secrets["groq"]["api_key"])


def get_gemini_model():
    genai.configure(api_key=st.secrets["google"]["api_key"])
    return genai.GenerativeModel("gemini-2.5-flash")


# ── SHARED HELPERS ─────────────────────────────────────────────────────────────

def _build_startup_context(data: dict) -> str:
    return f"""Startup Name: {data.get('startup_name', 'N/A')}
Description: {data.get('description', 'N/A')}
Industry: {data.get('industry', 'N/A')}
Target Market: {data.get('target_market', 'N/A')}
Business Model: {data.get('business_model', 'N/A')}
Revenue Model: {data.get('revenue_model', 'N/A')}
Funding Stage: {data.get('funding_stage', 'N/A')}""".strip()


def _extract_json(text: str) -> dict:
    """Robustly extract JSON from model response text."""
    # Strip markdown fences
    text = re.sub(r"```(?:json)?", "", text).strip()
    text = text.replace("```", "").strip()

    # Remove DeepSeek <think>...</think> reasoning blocks
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    # Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find JSON object inside text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Fix common single-quote issues and trailing commas
    cleaned = text.replace("'", '"')
    cleaned = re.sub(r",\s*}", "}", cleaned)
    cleaned = re.sub(r",\s*]", "]", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {}


def _call_groq(system_prompt: str, user_prompt: str,
               model: str = "llama-3.3-70b-versatile",
               temperature: float = 0.3) -> str:
    client = get_groq_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=1500,
    )
    return response.choices[0].message.content.strip()


def _call_gemini(prompt: str, temperature: float = 0.2) -> str:
    model = get_gemini_model()
    config = genai.types.GenerationConfig(
        temperature=temperature,
        max_output_tokens=2000,
    )
    response = model.generate_content(prompt, generation_config=config)
    return response.text.strip()


def _run_with_retry(call_fn, fallback: dict, max_retries: int = 2) -> dict:
    """Execute agent call with retry. Return fallback on total failure."""
    for attempt in range(max_retries):
        try:
            raw = call_fn(attempt)
            result = _extract_json(raw)
            if result:
                return result
        except Exception as e:
            print(f"Agent attempt {attempt+1} failed: {e}")
            continue
    return fallback


# ── AGENT 1: MARKET INTELLIGENCE ───────────────────────────────────────────────

_MARKET_SYSTEM = """You are a senior Market Intelligence Analyst at a top-tier global VC firm with 15+ years evaluating emerging markets and growth opportunities.

Evaluate the MARKET OPPORTUNITY for the startup submitted.

Assess rigorously:
- Market size and realistic growth trajectory (TAM/SAM/SOM signals)
- Market timing — right moment, too early, or too late?
- Verifiable customer demand signals
- Market maturity vs disruption potential
- Regulatory and macro environment

RULES:
- Respond with ONLY valid JSON — zero explanation outside JSON
- market_score: 10 = massive proven market, 0 = no viable market exists
- Be direct and analytical — no vague language

Return EXACTLY:
{
  "market_score": <integer 0-10>,
  "confidence": <integer 0-10>,
  "market_analysis": "<3-4 sentence sharp professional analysis>",
  "market_size_signal": "<Large / Medium / Niche>",
  "timing_assessment": "<Early Mover / Right Time / Late Entry>",
  "market_growth": "<High Growth / Stable / Declining>",
  "key_insight": "<one sharp sentence — the single most important market finding>"
}"""


def run_market_agent(startup_data: dict) -> dict:
    context = _build_startup_context(startup_data)
    fallback = {
        "market_score": 5, "confidence": 0,
        "market_analysis": "Market analysis unavailable — retry recommended.",
        "market_size_signal": "Unknown", "timing_assessment": "Unknown",
        "market_growth": "Unknown",
        "key_insight": "Analysis unavailable.",
    }

    def call(attempt):
        note = "\n\nRETURN ONLY VALID JSON. NO OTHER TEXT." if attempt > 0 else ""
        return _call_groq(
            _MARKET_SYSTEM + note,
            f"Analyze this startup for market opportunity:\n\n{context}",
            model="llama-3.3-70b-versatile", temperature=0.25,
        )

    return _run_with_retry(call, fallback)


# ── AGENT 2: COMPETITIVE LANDSCAPE ────────────────────────────────────────────

_COMPETITION_SYSTEM = """You are a Competitive Intelligence Specialist at a leading global VC fund with deep expertise in mapping competitive landscapes and defensible market positions.

Evaluate the COMPETITIVE LANDSCAPE for the startup submitted.

Assess rigorously:
- Existence and strength of direct and indirect competitors
- Real differentiation vs marketing claims
- Moat potential: network effects, switching costs, IP, brand, data advantages
- Barriers to entry for future competitors
- Big Tech disruption risk

RULES:
- Respond with ONLY valid JSON — zero explanation outside JSON
- competition_score: 10 = near-monopoly position, 0 = red ocean with giants dominating
- Be brutally honest — investors need accurate competitive assessments

Return EXACTLY:
{
  "competition_score": <integer 0-10>,
  "confidence": <integer 0-10>,
  "competition_analysis": "<3-4 sentence sharp professional analysis>",
  "competitive_intensity": "<Low / Medium / High / Extreme>",
  "moat_assessment": "<Strong / Moderate / Weak / None>",
  "big_tech_risk": "<High / Medium / Low>",
  "key_insight": "<one sharp sentence — the single most important competitive finding>"
}"""


def run_competition_agent(startup_data: dict) -> dict:
    context = _build_startup_context(startup_data)
    fallback = {
        "competition_score": 5, "confidence": 0,
        "competition_analysis": "Competitive analysis unavailable — retry recommended.",
        "competitive_intensity": "Unknown", "moat_assessment": "Unknown",
        "big_tech_risk": "Unknown",
        "key_insight": "Analysis unavailable.",
    }

    def call(attempt):
        note = "\n\nRETURN ONLY VALID JSON. NO OTHER TEXT." if attempt > 0 else ""
        return _call_groq(
            _COMPETITION_SYSTEM + note,
            f"Analyze this startup's competitive landscape:\n\n{context}",
            model="llama-3.3-70b-versatile", temperature=0.25,
        )

    return _run_with_retry(call, fallback)


# ── AGENT 3: FINANCIAL VIABILITY ───────────────────────────────────────────────

_FINANCIAL_SYSTEM = """You are a Financial Due Diligence Analyst at a top-tier Series A VC fund specializing in evaluating business model quality and financial viability of early-stage companies.

Evaluate the FINANCIAL VIABILITY of the startup submitted.

Assess rigorously:
- Revenue model clarity, repeatability, and scalability
- Unit economics potential (LTV/CAC signals from model type)
- Path to profitability — how long and capital-intensive?
- Capital efficiency — massive burn required or lean growth possible?
- Pricing power and gross margin potential

RULES:
- Respond with ONLY valid JSON — zero explanation outside JSON
- financial_score: 10 = exceptional model (SaaS recurring, high margins), 0 = broken economics
- Be precise — vague financial assessments are useless

Return EXACTLY:
{
  "financial_score": <integer 0-10>,
  "confidence": <integer 0-10>,
  "financial_analysis": "<3-4 sentence sharp professional analysis>",
  "revenue_model_quality": "<Excellent / Good / Weak / Unclear>",
  "scalability": "<High / Medium / Low>",
  "margin_potential": "<High / Medium / Low>",
  "capital_efficiency": "<Efficient / Moderate / Capital Intensive>",
  "key_insight": "<one sharp sentence — the single most important financial finding>"
}"""


def run_financial_agent(startup_data: dict) -> dict:
    context = _build_startup_context(startup_data)
    fallback = {
        "financial_score": 5, "confidence": 0,
        "financial_analysis": "Financial analysis unavailable — retry recommended.",
        "revenue_model_quality": "Unknown", "scalability": "Unknown",
        "margin_potential": "Unknown", "capital_efficiency": "Unknown",
        "key_insight": "Analysis unavailable.",
    }

    def call(attempt):
        note = "\n\nRETURN ONLY VALID JSON. NO OTHER TEXT." if attempt > 0 else ""
        return _call_groq(
            _FINANCIAL_SYSTEM + note,
            f"Evaluate the financial viability of this startup:\n\n{context}",
            model="llama-3.3-70b-versatile", temperature=0.2,
        )

    return _run_with_retry(call, fallback)


# ── AGENT 4: RISK ASSESSMENT ───────────────────────────────────────────────────

_RISK_SYSTEM = """You are a Risk Management Partner at a top global investment firm specializing in identifying, categorizing, and scoring investment risks across all dimensions.

Conduct a comprehensive RISK ASSESSMENT for the startup submitted.

Think deeply and evaluate:
- Execution risk: team capability signals, product complexity, GTM difficulty
- Market risk: demand uncertainty, customer adoption barriers
- Regulatory risk: current and emerging legal threats to this model
- Technology risk: build complexity, third-party dependencies
- Timing and macro risk: economic sensitivity, funding environment
- Competitive disruption risk

RULES:
- Respond with ONLY valid JSON — zero explanation outside JSON
- risk_score: 10 = very LOW risk (safe bet), 0 = extremely HIGH risk (likely failure)
- primary_risk = the single most likely failure mode for this startup
- Think carefully before scoring

Return EXACTLY:
{
  "risk_score": <integer 0-10>,
  "confidence": <integer 0-10>,
  "risk_analysis": "<3-4 sentence sharp professional risk analysis>",
  "primary_risk": "<the single most likely failure mode in one direct sentence>",
  "risk_level": "<Low / Medium / High / Critical>",
  "execution_risk": "<Low / Medium / High>",
  "regulatory_risk": "<Low / Medium / High>",
  "key_insight": "<one sharp sentence — the most critical risk finding>"
}"""


def run_risk_agent(startup_data: dict) -> dict:
    context = _build_startup_context(startup_data)
    fallback = {
        "risk_score": 5, "confidence": 0,
        "risk_analysis": "Risk analysis unavailable — retry recommended.",
        "primary_risk": "Assessment unavailable.",
        "risk_level": "Unknown", "execution_risk": "Unknown",
        "regulatory_risk": "Unknown",
        "key_insight": "Analysis unavailable.",
    }

    def call(attempt):
        note = "\n\nRETURN ONLY VALID JSON. NO OTHER TEXT." if attempt > 0 else ""
        return _call_groq(
            _RISK_SYSTEM + note,
            f"Conduct a comprehensive risk assessment for this startup:\n\n{context}",
            model="deepseek-r1-distill-llama-70b", temperature=0.2,
        )

    return _run_with_retry(call, fallback)


# ── AGENT 5: INNOVATION SCOUT ──────────────────────────────────────────────────

_INNOVATION_SYSTEM = """You are an Innovation Scout and Technology Strategist at a deep-tech VC fund with expertise in identifying genuinely novel ventures vs incremental improvements.

Assess the INNOVATION QUALITY and DIFFERENTIATION STRENGTH of the startup submitted.

Evaluate rigorously:
- Genuine novelty: truly new or a rebrand of existing solutions?
- Depth of technology or business model innovation
- Category creation potential vs incremental improvement
- Long-term defensibility through continued innovation
- Compounding advantages from the core innovation
- Founder unfair advantage signals from the description

RULES:
- Respond with ONLY valid JSON — zero explanation outside JSON
- innovation_score: 10 = category-defining breakthrough, 0 = pure commodity copy
- Be precise about WHAT is innovative — vague praise is worthless

Return EXACTLY:
{
  "innovation_score": <integer 0-10>,
  "confidence": <integer 0-10>,
  "innovation_analysis": "<3-4 sentence sharp professional analysis>",
  "innovation_type": "<Category Creator / Market Disruptor / Model Innovator / Incremental Improver / Commodity>",
  "defensibility": "<Strong / Moderate / Weak>",
  "unfair_advantage_signal": "<Strong / Moderate / Weak / None Visible>",
  "key_insight": "<one sharp sentence — the most important innovation finding>"
}"""


def run_innovation_agent(startup_data: dict) -> dict:
    context = _build_startup_context(startup_data)
    fallback = {
        "innovation_score": 5, "confidence": 0,
        "innovation_analysis": "Innovation analysis unavailable — retry recommended.",
        "innovation_type": "Unknown", "defensibility": "Unknown",
        "unfair_advantage_signal": "Unknown",
        "key_insight": "Analysis unavailable.",
    }

    def call(attempt):
        note = "\n\nRETURN ONLY VALID JSON. NO OTHER TEXT." if attempt > 0 else ""
        return _call_groq(
            _INNOVATION_SYSTEM + note,
            f"Assess the innovation and differentiation of this startup:\n\n{context}",
            model="llama-3.3-70b-versatile", temperature=0.3,
        )

    return _run_with_retry(call, fallback)


# ── AGENT 6: INVESTMENT COMMITTEE SYNTHESIZER ──────────────────────────────────

def run_synthesizer_agent(startup_data: dict, agent_results: dict) -> dict:
    """Agent 6: Synthesize all 5 agent outputs into final committee decision via Gemini."""

    fallback = {
        "overall_investment_score": 50,
        "final_recommendation": "Consider",
        "confidence_level": "Low",
        "decision_reasoning": "Synthesis could not be completed. Please review individual agent scores above.",
        "strengths": ["See individual agent reports.", "Retry for full synthesis.", ""],
        "weaknesses": ["Synthesis agent error.", "Individual scores available.", ""],
        "recommended_actions": ["Re-run the analysis.", "Review individual scores.", ""],
        "one_line_verdict": "Incomplete analysis — retry for full committee decision.",
    }

    m = agent_results.get("market", {})
    c = agent_results.get("competition", {})
    f = agent_results.get("financial", {})
    r = agent_results.get("risk", {})
    i = agent_results.get("innovation", {})
    ctx = _build_startup_context(startup_data)

    prompt = f"""You are the Chairperson of an Investment Committee at a top global VC fund.
Five specialist agents have completed their analysis. Synthesize into a final investment decision.

STARTUP:
{ctx}

━━━ AGENT REPORTS ━━━

MARKET AGENT — Score: {m.get('market_score',5)}/10 | Confidence: {m.get('confidence',5)}/10
Analysis: {m.get('market_analysis','N/A')}
Key Insight: {m.get('key_insight','N/A')}
Size: {m.get('market_size_signal','N/A')} | Timing: {m.get('timing_assessment','N/A')} | Growth: {m.get('market_growth','N/A')}

COMPETITION AGENT — Score: {c.get('competition_score',5)}/10 | Confidence: {c.get('confidence',5)}/10
Analysis: {c.get('competition_analysis','N/A')}
Key Insight: {c.get('key_insight','N/A')}
Intensity: {c.get('competitive_intensity','N/A')} | Moat: {c.get('moat_assessment','N/A')} | Big Tech Risk: {c.get('big_tech_risk','N/A')}

FINANCIAL AGENT — Score: {f.get('financial_score',5)}/10 | Confidence: {f.get('confidence',5)}/10
Analysis: {f.get('financial_analysis','N/A')}
Key Insight: {f.get('key_insight','N/A')}
Model: {f.get('revenue_model_quality','N/A')} | Scalability: {f.get('scalability','N/A')} | Margins: {f.get('margin_potential','N/A')}

RISK AGENT — Score: {r.get('risk_score',5)}/10 (10=Low Risk) | Confidence: {r.get('confidence',5)}/10
Analysis: {r.get('risk_analysis','N/A')}
Primary Risk: {r.get('primary_risk','N/A')}
Level: {r.get('risk_level','N/A')} | Execution: {r.get('execution_risk','N/A')} | Regulatory: {r.get('regulatory_risk','N/A')}

INNOVATION AGENT — Score: {i.get('innovation_score',5)}/10 | Confidence: {i.get('confidence',5)}/10
Analysis: {i.get('innovation_analysis','N/A')}
Key Insight: {i.get('key_insight','N/A')}
Type: {i.get('innovation_type','N/A')} | Defensibility: {i.get('defensibility','N/A')}

━━━ SCORING RULES ━━━
overall_investment_score (0-100) = weighted sum:
  (market_score × 10 × 0.25) + (competition_score × 10 × 0.20) +
  (financial_score × 10 × 0.25) + (risk_score × 10 × 0.20) +
  (innovation_score × 10 × 0.10)

final_recommendation:
  70-100 → "Strong Invest"
  45-69  → "Consider"
  0-44   → "Reject"

confidence_level:
  avg agent confidence ≥ 7 → "High"
  avg 4-6 → "Medium"
  avg < 4 → "Low"

━━━ OUTPUT RULES ━━━
Respond with ONLY valid JSON. No preamble. No markdown. No explanation outside JSON.
Be decisive — this is a committee decision, not a consulting report.

Return EXACTLY:
{{
  "overall_investment_score": <integer 0-100>,
  "final_recommendation": "<Strong Invest / Consider / Reject>",
  "confidence_level": "<High / Medium / Low>",
  "decision_reasoning": "<5-6 sentence executive-level investment reasoning. Direct and decisive.>",
  "strengths": ["<specific strength 1>", "<specific strength 2>", "<specific strength 3>"],
  "weaknesses": ["<specific weakness 1>", "<specific weakness 2>", "<specific weakness 3>"],
  "recommended_actions": [
    "<concrete actionable recommendation 1>",
    "<concrete actionable recommendation 2>",
    "<concrete actionable recommendation 3>"
  ],
  "one_line_verdict": "<sharp, direct, memorable one-line investment verdict>"
}}"""

    def call(attempt):
        p = prompt
        if attempt > 0:
            p += "\n\nCRITICAL: Return ONLY valid JSON. No markdown, no explanation outside JSON."
        return _call_gemini(p, temperature=0.2)

    return _run_with_retry(call, fallback)
