import json
import re
from typing import Any
from langchain_core.messages import SystemMessage, HumanMessage
from Multi_Agent_TourAI.graph.state import TravelState
from Multi_Agent_TourAI.llms.llm import fast_llm
from Multi_Agent_TourAI.config.prompts import (SUPERVISOR_SYSTEM_PROMPT, USER_CONTEXT_PROMPT,)
from Multi_Agent_TourAI.utils.logger import get_logger, log_execution

logger = get_logger(__name__)


def _normalize_destination(raw: Any) -> str:
    """Normalizes and cleans extracted destination string."""
    if not raw or not isinstance(raw, str):
        return ""
    clean = raw.strip(" .\n\"'")
    clean = re.sub(r'^(destination|city|location|target)\s*:\s*', '', clean, flags=re.IGNORECASE).strip(" .\n\"'")
    if clean.lower() in ("none", "null", "n/a", "not applicable", "unknown", "ambiguous", "empty", "false"):
        return ""
    return clean


def _deterministic_fallback(query: str, has_itinerary: bool) -> tuple[str, str, list[str], str]:
    """
    Deterministic intent-aware fallback router when model inference or JSON extraction fails.
    Preserves new_plan, specific_query, and follow_up behaviors without running all agents indiscriminately.
    
    Returns:
        tuple[str, str, list[str], str]: (intent, destination, selected_agents, reasoning)
    """
    query_lower = query.lower()

    # 1. Follow-up query with existing itinerary
    if has_itinerary:
        return (
            "follow_up",
            "",
            [],
            "Fallback: existing itinerary detected, routed to conversational memory"
        )

    # 2. Flight-only inquiry
    if any(k in query_lower for k in ["flight", "flights", "airline", "airlines", "airport", "airfare", "fly to", "plane ticket"]) and not any(k in query_lower for k in ["hotel", "weather", "itinerary", "vacation", "trip to", "tour"]):
        return (
            "specific_query",
            "",
            ["flight_agent"],
            "Fallback: flight-specific request identified"
        )

    # 3. Hotel-only inquiry
    if any(k in query_lower for k in ["hotel", "hotels", "resort", "resorts", "accommodation", "hostel", "where to stay"]) and not any(k in query_lower for k in ["flight", "weather", "itinerary", "vacation"]):
        return (
            "specific_query",
            "",
            ["hotel_agent"],
            "Fallback: hotel-specific request identified"
        )

    # 4. Weather-only inquiry
    if any(k in query_lower for k in ["weather", "temperature", "forecast", "climate", "rain", "sunny", "how cold", "how hot"]) and not any(k in query_lower for k in ["flight", "hotel", "itinerary", "plan a trip"]):
        return (
            "specific_query",
            "",
            ["weather_agent"],
            "Fallback: weather-specific request identified"
        )

    # 5. Maps, routes, or local attractions inquiry
    if any(k in query_lower for k in ["how far", "distance between", "route from", "drive from", "travel from", "cafe", "cafes", "restaurant", "restaurants", "top sights", "attractions in"]) and not any(k in query_lower for k in ["flight", "hotel", "full plan"]):
        return (
            "specific_query",
            "",
            ["maps_agent"],
            "Fallback: maps/attraction-specific request identified"
        )

    # 6. Itinerary-only inquiry
    if any(k in query_lower for k in ["itinerary only", "schedule only", "day-by-day plan only"]):
        return (
            "specific_query",
            "",
            ["itinerary_agent"],
            "Fallback: itinerary-only request identified"
        )

    # 7. Default full trip planning fallback: includes all 4 specialist agents
    return (
        "new_plan",
        "",
        ["flight_agent", "hotel_agent", "weather_agent", "maps_agent"],
        "Fallback: general trip planning request, running standard 4 specialist agents"
    )


# json helper
def _extract_json(text: Any) -> dict[str, Any]:
    """Extract the first complete JSON object returned by the model"""
    if isinstance(text, list):
        text = "".join(
            item.get("text", str(item)) if isinstance(item, dict)
            else getattr(item, "text", str(item))
            for item in text
        )
    elif not isinstance(text, str):
        text = str(text or "")

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("Model didn't return a json object")
    return json.loads(text[start: end +1])

# supervisor agent
@log_execution
def supervisor_agent(state: TravelState) -> dict:
    """Inspects state and decides whether to invoke external tool agents (new_plan)
    or bypass tools directly to the conversational response agent (follow_up).
    Extracts destination city in the same analysis without additional LLM calls."""
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
        destination = _normalize_destination(parsed.get("destination", ""))
        selected_agents = parsed.get("selected_agents", [])
        reasoning = parsed.get("reasoning", "")
    except Exception as e:
        logger.warning(f"Supervisor parsing fallback triggered: {e}")
        intent, destination, selected_agents, reasoning = _deterministic_fallback(user_query, has_itinerary)

    logger.info(f"Supervisor Decision -> Intent: '{intent}' | Destination: '{destination}' | Agents: {selected_agents} | Reason: {reasoning}")

    return {
        "intent": intent,
        "destination": destination,
        "selected_agents": selected_agents,
        "supervisor_reasoning": reasoning,
        "llm_calls": 1
    }

__all__ = ["supervisor_agent", "_extract_json", "_normalize_destination", "_deterministic_fallback"]
