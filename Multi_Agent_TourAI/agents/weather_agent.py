import re
import asyncio
from typing import Any
from langchain_core.messages import AIMessage
from Multi_Agent_TourAI.graph.state import TravelState
from Multi_Agent_TourAI.mcp.weather_mcp import weather_mcp_search, forecast_mcp_search
from Multi_Agent_TourAI.utils import get_logger, log_execution, run_async_safely

logger = get_logger(__name__)


def extract_destination(query: str, state_destination: str = "") -> str:
    """
    Finds and extracts the destination city from state or query.
    Reuses supervisor analysis if present, avoiding redundant LLM calls.
    Falls back gracefully to the raw query if destination is missing.
    """
    if state_destination and str(state_destination).strip():
        clean = str(state_destination).strip(" .\n\"'")
        clean = re.sub(r'^(destination|city|location|target)\s*:\s*', '', clean, flags=re.IGNORECASE).strip(" .\n\"'")
        if clean.lower() not in ("none", "null", "n/a", "not applicable", "unknown", "ambiguous", "empty", "false"):
            return clean
    return (query or "").strip()


async def _run_weather_agent_async(city: str) -> str:
    """
    Asynchronously queries current weather and 5-day forecast concurrently.
    Preserves partial results if either tool fails or times out.
    """
    logger.info(f"Weather Agent: Concurrently querying current weather and forecast for '{city}'...")
    tasks = [weather_mcp_search(city), forecast_mcp_search(city)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    current_res, forecast_res = results[0], results[1]

    # Handle current weather
    if isinstance(current_res, Exception):
        logger.warning(f"Current weather query failed for '{city}': {current_res}")
        current_part = f"Current weather data currently unavailable ({type(current_res).__name__})."
    elif current_res is None or str(current_res).strip() == "":
        current_part = "Current weather data not available."
    else:
        current_part = str(current_res).strip()

    # Handle forecast
    if isinstance(forecast_res, Exception):
        logger.warning(f"Weather forecast query failed for '{city}': {forecast_res}")
        forecast_part = f"5-day forecast currently unavailable ({type(forecast_res).__name__})."
    elif forecast_res is None or str(forecast_res).strip() == "":
        forecast_part = "5-day forecast data not available."
    else:
        forecast_part = str(forecast_res).strip()

    # Check if both failed
    if isinstance(current_res, Exception) and isinstance(forecast_res, Exception):
        return f"Weather and forecast data unavailable for {city}: {current_res}"

    return (
        f"Current Weather for {city}:\n{current_part}\n\n"
        f"5-Day Forecast for {city}:\n{forecast_part}"
    )


@log_execution
def weather_agent(state: TravelState):
    """
    Weather Agent Node for LangGraph:
    1. Reads user_query and destination from shared state.
    2. Concurrently queries Weather FastMCP tools (Current Weather & 5-Day Forecast).
    3. Handles partial failures gracefully without discarding successful responses.
    4. Updates shared state with 'weather_results'.
    """
    query = state.get("user_query", "")
    city = extract_destination(query, state_destination=state.get("destination", ""))
    logger.info(f"Weather Agent: Fetching real-time weather & forecast for '{city}'...")

    try:
        weather_data = run_async_safely(_run_weather_agent_async(city))
        logger.info(f"Weather Agent: Successfully retrieved weather data for '{city}'.")
    except Exception as error:
        logger.error(f"Weather Agent Failed: {str(error)}", exc_info=True)
        weather_data = f"Weather data unavailable for {city}: {str(error)}"

    return {
        "weather_results": weather_data,
        "messages": [AIMessage(content=f"Weather information fetched for {city}.")],
        "llm_calls": 0,
    }


__all__ = ["weather_agent", "extract_destination", "_run_weather_agent_async"]
