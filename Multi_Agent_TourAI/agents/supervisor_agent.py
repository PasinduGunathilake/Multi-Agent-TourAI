import json
from typing import Any
from langchain_core.messages import SystemMessage, HumanMessage
from Multi_Agent_TourAI.graph.state import TravelState
from Multi_Agent_TourAI.llms.llm import fast_llm
from Multi_Agent_TourAI.config.prompts import (SUPERVISOR_SYSTEM_PROMPT, USER_CONTEXT_PROMPT,)
from Multi_Agent_TourAI.utils.logger import get_logger, log_execution

logger = get_logger(__name__)

# json helper
def _extract_json(text: str) -> dict[str, Any]:
    """Extract the first complete JSON object returned by the model"""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("Model didn't return a json object")
    return json.loads(text[start: end +1])

# supervisor agent
@log_execution
def supervisor_agent(state: TravelState) -> dict:
    """Inspects state and decides whether to invoke external tool agents (new_plan)
    or bypass tools directly to the conversational response agent (follow_up)."""
    user_query = state.get("user_query", "")
    has_itinerary = bool(state.get("itinerary", "").strip())
    history_len = len(state.get("messages", []))
    logger.info(
        f"Supervisor inspecting query: '{user_query}' | Has Itinerary: {has_itinerary} | History: {history_len} msgs"
    )

    prompt = USER_CONTEXT_PROMPT.format(
        user_query = user_query,
        has_itinerary = has_itinerary,
        history_len = history_len
    )

    try:
        response = fast_llm.invoke([
            SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])

        parsed = _extract_json(response.content)
        intent = parsed.get("intent", "new_plan")
        selected_agents = parsed.get("selected_agents", [])
        reasoning = parsed.get("reasoning", "")
    except Exception as e:
        logger.warning(f"Supervisor parsing fallback triggered: {e}")

        # safe deterministic fallback
        if has_itinerary:
            intent = "follow_up"
            selected_agents = []
            reasoning = "Fallback: existing itinerary detected, routed to conversational memory"
        else:
            intent = "new_plan"
            selected_agents = ["flight_agent", "hotel_agent", "weather_agent"]
            reasoning = "Fallback: no prior itinerary found, running standard multi-agent pipeline"

    logger.info(f"Supervisor Decision -> Intent: '{intent}' | Agents: {selected_agents} | Reason: {reasoning}")

    return {
        "intent": intent,
        "selected_agents": selected_agents,
        "supervisor_reasoning": reasoning,
        "llm_calls": 1
    }

__all__ = ["supervisor_agent"]
