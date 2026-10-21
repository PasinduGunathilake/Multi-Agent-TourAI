import json
from typing import Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from Multi_Agent_TourAI.graph.state import TravelState
from Multi_Agent_TourAI.llms.llm import fast_llm
from Multi_Agent_TourAI.config.prompts import (Guardrail_PROMPT_TEMPLATE,)
from Multi_Agent_TourAI.utils.logger import get_logger, log_execution

logger = get_logger(__name__)

# json helper
def _extract_json(text: str) -> dict[str, Any]:
    """Extract the first complete JSON object returned by the model"""
    start = text.find("{")
    end = text.rfind("}")

    if start ==-1 or end == -1 or end < start:
        raise ValueError("Model didn't return a json object")

    return json.loads(text[start :end +1])


# Model-Based Input Level Guardrail
"""
Evaluates whether the user query is travel-related and safe. Uses fast_llm for ultra-fast validation (~0.5s).
"""
@log_execution
def input_guardrail(state: TravelState):
    user_query = state["user_query"]
    logger.info(f"Input Guardrail inspecting: '{user_query}'")
    prompt = Guardrail_PROMPT_TEMPLATE.format(
        user_query = state["user_query"]
    )
    try:
        response = fast_llm.invoke([
            SystemMessage(content="You are the input guardrail for a travel-planning application.Return strict JSON only."),
            HumanMessage(content=prompt)
        ])

        guardrail_result = _extract_json(response.content)
        allowed = bool(guardrail_result.get("allowed", True))
        guardrail_reason = str(guardrail_result.get("reason", "")).strip()

    except Exception as e:  # fail-open strategy: if json issue came from model, normal query runs without any block.
        logger.warning(f"Guardrail fallback used (fail-open): {e}")
        allowed = True
        guardrail_reason = "Guardrail validation fallback allowed the request"

    if not allowed:
        reason = guardrail_reason or (
            "I can only help with travel-planning requests (destinations, flights, hotels, weather, budgets, and itineraries)."
        )
        logger.warning(f"Guardrail BLOCKED query: {reason}")
        return {
            "guardrail_allowed": False,
            "guardrail_reason": reason,
            "messages": [AIMessage(content=reason)],
            "llm_calls": 1
        }
    logger.info("Guardrail PASSED: Valid travel query.")
    return {
        "guardrail_allowed": True,
        "guardrail_reason": "",
        "llm_calls": 1
    }

# blocked response (when direct route blocked)
@log_execution
def guardrail_blocked(state: TravelState):
    reason = state.get("guardrail_reason") or "This request is outside the scope of travel planning."
    return {
        "messages": [AIMessage(content=reason)]
    }