"""
InvestIQ AI — Pipeline Orchestrator

Runs all 6 agents sequentially with:
- Live progress tracking via callback
- Per-agent error isolation (one failure never kills the whole run)
- Structured result assembly
- Timing information per agent
"""

import time
from typing import Callable, Optional
from ai.agents import (
    run_market_agent,
    run_competition_agent,
    run_financial_agent,
    run_risk_agent,
    run_innovation_agent,
    run_synthesizer_agent,
)


# ── AGENT REGISTRY ─────────────────────────────────────────────────────────────

AGENTS = [
    {
        "key": "market",
        "name": "Market Intelligence",
        "icon": "🔍",
        "model": "Groq · llama-3.3-70b",
        "status_msg": "Analyzing market size, timing & demand signals...",
        "fn": run_market_agent,
        "needs_prior": False,
    },
    {
        "key": "competition",
        "name": "Competitive Landscape",
        "icon": "⚔️",
        "model": "Groq · llama-3.3-70b",
        "status_msg": "Mapping competitors, moats & differentiation...",
        "fn": run_competition_agent,
        "needs_prior": False,
    },
    {
        "key": "financial",
        "name": "Financial Viability",
        "icon": "💰",
        "model": "Groq · llama-3.3-70b",
        "status_msg": "Evaluating business model & unit economics...",
        "fn": run_financial_agent,
        "needs_prior": False,
    },
    {
        "key": "risk",
        "name": "Risk Assessment",
        "icon": "⚠️",
        "model": "Groq · deepseek-r1",
        "status_msg": "Running deep risk reasoning across all dimensions...",
        "fn": run_risk_agent,
        "needs_prior": False,
    },
    {
        "key": "innovation",
        "name": "Innovation Scout",
        "icon": "💡",
        "model": "Groq · llama-3.3-70b",
        "status_msg": "Assessing novelty, defensibility & differentiation...",
        "fn": run_innovation_agent,
        "needs_prior": False,
    },
    {
        "key": "synthesis",
        "name": "Investment Committee",
        "icon": "🏛️",
        "model": "Gemini 2.5 Flash",
        "status_msg": "Synthesizing all reports into final decision...",
        "fn": None,  # special case — uses synthesizer with prior results
        "needs_prior": True,
    },
]


# ── PIPELINE RESULT SCHEMA ─────────────────────────────────────────────────────

def _empty_result() -> dict:
    """Return a default empty pipeline result structure."""
    return {
        "success": False,
        "startup_data": {},
        "agent_results": {
            "market": {},
            "competition": {},
            "financial": {},
            "risk": {},
            "innovation": {},
        },
        "synthesis": {},
        "timings": {},
        "errors": [],
    }


# ── MAIN PIPELINE ──────────────────────────────────────────────────────────────

def run_pipeline(
    startup_data: dict,
    on_agent_start: Optional[Callable[[str, str, str], None]] = None,
    on_agent_complete: Optional[Callable[[str, dict, float], None]] = None,
    on_agent_error: Optional[Callable[[str, str], None]] = None,
) -> dict:
    """
    Execute the full 6-agent analysis pipeline sequentially.

    Args:
        startup_data:       Dict with startup form fields.
        on_agent_start:     Callback(agent_key, agent_name, status_msg)
                            Called just before each agent runs.
        on_agent_complete:  Callback(agent_key, result_dict, elapsed_seconds)
                            Called after each agent succeeds.
        on_agent_error:     Callback(agent_key, error_message)
                            Called if an agent raises an unexpected exception.

    Returns:
        Full result dict with all agent outputs and synthesis.
    """
    result = _empty_result()
    result["startup_data"] = startup_data
    agent_results = result["agent_results"]

    # ── Run Agents 1–5 ────────────────────────────────────────────────────────
    for agent in AGENTS:
        key = agent["key"]

        if agent["needs_prior"]:
            # Synthesizer is handled separately below
            continue

        # Notify caller that this agent is starting
        if on_agent_start:
            on_agent_start(key, agent["name"], agent["status_msg"])

        t_start = time.time()
        try:
            agent_result = agent["fn"](startup_data)
            elapsed = round(time.time() - t_start, 2)
            agent_results[key] = agent_result
            result["timings"][key] = elapsed

            if on_agent_complete:
                on_agent_complete(key, agent_result, elapsed)

        except Exception as e:
            elapsed = round(time.time() - t_start, 2)
            error_msg = str(e)
            result["errors"].append({"agent": key, "error": error_msg})
            result["timings"][key] = elapsed

            if on_agent_error:
                on_agent_error(key, error_msg)

            # Use neutral fallback — don't break the pipeline
            agent_results[key] = _agent_fallback(key)

    # ── Run Agent 6: Synthesizer ──────────────────────────────────────────────
    synth_agent = AGENTS[-1]
    if on_agent_start:
        on_agent_start("synthesis", synth_agent["name"], synth_agent["status_msg"])

    t_start = time.time()
    try:
        synthesis = run_synthesizer_agent(startup_data, agent_results)
        elapsed = round(time.time() - t_start, 2)
        result["synthesis"] = synthesis
        result["timings"]["synthesis"] = elapsed

        if on_agent_complete:
            on_agent_complete("synthesis", synthesis, elapsed)

    except Exception as e:
        elapsed = round(time.time() - t_start, 2)
        error_msg = str(e)
        result["errors"].append({"agent": "synthesis", "error": error_msg})
        result["timings"]["synthesis"] = elapsed

        if on_agent_error:
            on_agent_error("synthesis", error_msg)

        result["synthesis"] = _synthesis_fallback(agent_results)

    result["success"] = True
    return result


# ── SCORE HELPERS ──────────────────────────────────────────────────────────────

def calculate_weighted_score(agent_results: dict) -> int:
    """
    Calculate overall investment score from agent scores.
    Weights: Market 25%, Competition 20%, Financial 25%, Risk 20%, Innovation 10%
    """
    weights = {
        "market": ("market_score", 0.25),
        "competition": ("competition_score", 0.20),
        "financial": ("financial_score", 0.25),
        "risk": ("risk_score", 0.20),
        "innovation": ("innovation_score", 0.10),
    }
    total = 0.0
    for key, (field, weight) in weights.items():
        score = agent_results.get(key, {}).get(field, 5)
        total += score * 10 * weight
    return round(total)


def get_recommendation_label(score: int) -> str:
    if score >= 70:
        return "Strong Invest"
    elif score >= 45:
        return "Consider"
    else:
        return "Reject"


def assemble_final_result(pipeline_output: dict) -> dict:
    """
    Flatten pipeline output into a single result dict
    suitable for saving to Firestore and rendering the dashboard.
    """
    startup = pipeline_output.get("startup_data", {})
    agents = pipeline_output.get("agent_results", {})
    synth = pipeline_output.get("synthesis", {})

    market = agents.get("market", {})
    competition = agents.get("competition", {})
    financial = agents.get("financial", {})
    risk = agents.get("risk", {})
    innovation = agents.get("innovation", {})

    overall = synth.get(
        "overall_investment_score",
        calculate_weighted_score(agents)
    )

    return {
        # Startup metadata
        "startup_name": startup.get("startup_name", ""),
        "description": startup.get("description", ""),
        "industry": startup.get("industry", ""),
        "target_market": startup.get("target_market", ""),
        "business_model": startup.get("business_model", ""),
        "revenue_model": startup.get("revenue_model", ""),
        "funding_stage": startup.get("funding_stage", ""),

        # Individual scores
        "market_score": market.get("market_score", 5),
        "competition_score": competition.get("competition_score", 5),
        "financial_score": financial.get("financial_score", 5),
        "risk_score": risk.get("risk_score", 5),
        "innovation_score": innovation.get("innovation_score", 5),

        # Individual analyses
        "market_analysis": market.get("market_analysis", ""),
        "competition_analysis": competition.get("competition_analysis", ""),
        "financial_analysis": financial.get("financial_analysis", ""),
        "risk_analysis": risk.get("risk_analysis", ""),
        "innovation_analysis": innovation.get("innovation_analysis", ""),

        # Key insights per agent
        "market_key_insight": market.get("key_insight", ""),
        "competition_key_insight": competition.get("key_insight", ""),
        "financial_key_insight": financial.get("key_insight", ""),
        "risk_key_insight": risk.get("key_insight", ""),
        "innovation_key_insight": innovation.get("key_insight", ""),

        # Agent sub-fields
        "market_size_signal": market.get("market_size_signal", ""),
        "timing_assessment": market.get("timing_assessment", ""),
        "market_growth": market.get("market_growth", ""),
        "competitive_intensity": competition.get("competitive_intensity", ""),
        "moat_assessment": competition.get("moat_assessment", ""),
        "big_tech_risk": competition.get("big_tech_risk", ""),
        "revenue_model_quality": financial.get("revenue_model_quality", ""),
        "scalability": financial.get("scalability", ""),
        "margin_potential": financial.get("margin_potential", ""),
        "capital_efficiency": financial.get("capital_efficiency", ""),
        "primary_risk": risk.get("primary_risk", ""),
        "risk_level": risk.get("risk_level", ""),
        "execution_risk": risk.get("execution_risk", ""),
        "regulatory_risk": risk.get("regulatory_risk", ""),
        "innovation_type": innovation.get("innovation_type", ""),
        "defensibility": innovation.get("defensibility", ""),
        "unfair_advantage_signal": innovation.get("unfair_advantage_signal", ""),

        # Agent confidence scores
        "agent_confidences": {
            "market": market.get("confidence", 5),
            "competition": competition.get("confidence", 5),
            "financial": financial.get("confidence", 5),
            "risk": risk.get("confidence", 5),
            "innovation": innovation.get("confidence", 5),
        },

        # Synthesis outputs
        "overall_investment_score": overall,
        "final_recommendation": synth.get(
            "final_recommendation",
            get_recommendation_label(overall)
        ),
        "confidence_level": synth.get("confidence_level", "Medium"),
        "decision_reasoning": synth.get("decision_reasoning", ""),
        "strengths": synth.get("strengths", []),
        "weaknesses": synth.get("weaknesses", []),
        "recommended_actions": synth.get("recommended_actions", []),
        "one_line_verdict": synth.get("one_line_verdict", ""),

        # Meta
        "pipeline_errors": pipeline_output.get("errors", []),
        "timings": pipeline_output.get("timings", {}),
    }


# ── FALLBACKS ──────────────────────────────────────────────────────────────────

def _agent_fallback(key: str) -> dict:
    """Return a neutral fallback result for a failed agent."""
    fallbacks = {
        "market": {
            "market_score": 5, "confidence": 0,
            "market_analysis": "Agent encountered an error. Score set to neutral.",
            "market_size_signal": "Unknown", "timing_assessment": "Unknown",
            "market_growth": "Unknown", "key_insight": "Agent unavailable.",
        },
        "competition": {
            "competition_score": 5, "confidence": 0,
            "competition_analysis": "Agent encountered an error. Score set to neutral.",
            "competitive_intensity": "Unknown", "moat_assessment": "Unknown",
            "big_tech_risk": "Unknown", "key_insight": "Agent unavailable.",
        },
        "financial": {
            "financial_score": 5, "confidence": 0,
            "financial_analysis": "Agent encountered an error. Score set to neutral.",
            "revenue_model_quality": "Unknown", "scalability": "Unknown",
            "margin_potential": "Unknown", "capital_efficiency": "Unknown",
            "key_insight": "Agent unavailable.",
        },
        "risk": {
            "risk_score": 5, "confidence": 0,
            "risk_analysis": "Agent encountered an error. Score set to neutral.",
            "primary_risk": "Assessment unavailable.",
            "risk_level": "Unknown", "execution_risk": "Unknown",
            "regulatory_risk": "Unknown", "key_insight": "Agent unavailable.",
        },
        "innovation": {
            "innovation_score": 5, "confidence": 0,
            "innovation_analysis": "Agent encountered an error. Score set to neutral.",
            "innovation_type": "Unknown", "defensibility": "Unknown",
            "unfair_advantage_signal": "Unknown", "key_insight": "Agent unavailable.",
        },
    }
    return fallbacks.get(key, {"score": 5, "confidence": 0})


def _synthesis_fallback(agent_results: dict) -> dict:
    """Build a basic synthesis from raw agent scores if Gemini fails."""
    score = calculate_weighted_score(agent_results)
    return {
        "overall_investment_score": score,
        "final_recommendation": get_recommendation_label(score),
        "confidence_level": "Low",
        "decision_reasoning": (
            "The Investment Committee synthesizer encountered an error. "
            "The overall score has been calculated mathematically from individual agent scores. "
            "Please review individual agent analyses above for detailed findings."
        ),
        "strengths": [
            "See individual agent reports for detailed findings.",
            "Score calculated from 5 specialist agent assessments.",
            "Re-run analysis for full committee synthesis.",
        ],
        "weaknesses": [
            "Committee synthesis unavailable — Gemini API error.",
            "Individual scores may be reviewed above.",
            "Full reasoning requires successful synthesis run.",
        ],
        "recommended_actions": [
            "Re-run the analysis to get the full committee decision.",
            "Review individual agent breakdowns in the deep-dive section.",
            "Check API key configuration if errors persist.",
        ],
        "one_line_verdict": f"Score: {score}/100 — {get_recommendation_label(score)} (synthesis error, see individual reports).",
    }