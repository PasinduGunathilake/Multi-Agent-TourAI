import asyncio
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from Multi_Agent_TourAI.graph.state import TravelState
from Multi_Agent_TourAI.mcp.aviationstack_mcp import aviationstack_mcp_search
from Multi_Agent_TourAI.llms.llm import fast_llm
from Multi_Agent_TourAI.config.prompts import (FLIGHT_SYSTEM_PROMPT, FLIGHT_PROMPT_TEMPLATE,)
from Multi_Agent_TourAI.utils import get_logger, log_execution, run_async_safely

logger = get_logger(__name__)

# Max character limit per tool output segment to prevent prompt bloat and TPM exhaustion
MAX_TOOL_CHAR_LIMIT = 1200


def _format_tool_segment(raw_result: Any, tool_name: str) -> str:
    """Safely extracts, sanitizes, and bounds a single tool response block."""
    if isinstance(raw_result, Exception):
        logger.warning(f"Flight tool '{tool_name}' failed: {raw_result}")
        return f"Flight {tool_name} data currently unavailable: {type(raw_result).__name__}"
    if raw_result is None or str(raw_result).strip() == "":
        return f"No {tool_name} records returned for this route."
    s = str(raw_result).strip()
    return s[:MAX_TOOL_CHAR_LIMIT] + ("..." if len(s) > MAX_TOOL_CHAR_LIMIT else "")


async def _run_flight_agent_async(user_query: str) -> str:
    """
    Native asynchronous flight search workflow:
    1. Dispatches independent Aviationstack MCP tool queries concurrently via asyncio.gather().
    2. Uses return_exceptions=True so a failure in one tool does not abort the entire search.
    3. Synthesizes a structured flight plan using fast_llm.
    """
    tool_names = [
        "list_airports",
        "list_airlines",
        "list_routes",
        "future_flights_arrival_departure_schedule",
        "list_taxes",
    ]

    logger.info(f"Flight Agent: Concurrently querying {len(tool_names)} Aviationstack MCP tools...")
    tasks = [aviationstack_mcp_search(name) for name in tool_names]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    parsed_tools: Dict[str, str] = {
        name: _format_tool_segment(res, name)
        for name, res in zip(tool_names, results)
    }

    prompt = FLIGHT_PROMPT_TEMPLATE.format(
        user_query=user_query,
        list_airports=parsed_tools["list_airports"],
        list_airlines=parsed_tools["list_airlines"],
        list_routes=parsed_tools["list_routes"],
        future_flights_arrival_departure_schedule=parsed_tools["future_flights_arrival_departure_schedule"],
        list_taxes=parsed_tools["list_taxes"],
    )

    try:
        response = fast_llm.invoke([
            SystemMessage(content=FLIGHT_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        return str(response.content)
    except Exception as llm_err:
        logger.error(f"Flight Agent LLM synthesis failed: {llm_err}", exc_info=True)
        # Deterministic fallback summary from collected partial results
        return (
            f"Flight Route Guidance for '{user_query}':\n"
            f"- Airports: {parsed_tools['list_airports'][:300]}\n"
            f"- Airlines: {parsed_tools['list_airlines'][:300]}\n"
            f"- Routes: {parsed_tools['list_routes'][:300]}\n"
            "(Live airfare synthesis unavailable at this moment.)"
        )


# Synchronous LangGraph node wrapper (loop-safe)
@log_execution
def flight_agent(state: TravelState):
    """
    Flight Agent Node for LangGraph:
    Maintains synchronous node compatibility with travel_graph.stream(),
    executing the concurrent async workflow safely without nested event-loop collisions.
    """
    user_query = state.get("user_query", "")

    try:
        flight_data = run_async_safely(_run_flight_agent_async(user_query))
    except Exception as e:
        logger.error(f"Flight Agent Failed: {str(e)}", exc_info=True)
        flight_data = f"Flight information unavailable: {str(e)}"

    return {
        "flight_results": flight_data,
        "messages": [AIMessage(content="Flight result fetched.")],
        "llm_calls": 1,
    }


__all__ = ["flight_agent", "_run_flight_agent_async", "_format_tool_segment"]
