import re
import asyncio
from langchain_core.messages import AIMessage
from Multi_Agent_TourAI.graph.state import TravelState
from Multi_Agent_TourAI.mcp.weather_mcp import weather_mcp_search, forecast_mcp_search
from Multi_Agent_TourAI.llms.llm import llm
from Multi_Agent_TourAI.config.prompts import (DESTINATION_EXTRACTOR_PROMPT_TEMPLATE,)
from Multi_Agent_TourAI.utils import get_logger, log_execution

# Initialize logger for the Weather Agent
logger = get_logger(__name__)

# Destination extract from query (Because mcp should be past results for destination)- helper function
def extract_destination(query: str) -> str:
    """
    Finds and extracts the destination city from the user's travel prompt.
    For example: 'Plan a 5 days trip to Dubai from Sri Lanka' -> 'Dubai'
    """
    prompt = DESTINATION_EXTRACTOR_PROMPT_TEMPLATE.format(
        query = query
    )

    response = llm.invoke(prompt)

    return response.content.strip(" .\n\"'")
    



@log_execution
def weather_agent(state: TravelState):
    """
    Weather Agent Node for LangGraph:
    1. Reads user_query from the shared state.
    2. Identifies the destination city.
    3. Calls the Weather FastMCP tools (Current Weather & 5-Day Forecast).
    4. Updates the state with 'weather_results'.
    """
    query = state["user_query"]
    city = extract_destination(query)
    logger.info(f"Weather Agent: Fetching real-time weather & forecast for '{city}'...")

    try:
        # Run async search helpers to query OpenWeatherMap via FastMCP
        current_weather = asyncio.run(weather_mcp_search(city))
        forecast = asyncio.run(forecast_mcp_search(city))

        # Combine both results into a clean string for the LLM
        weather_data = (
            f"Current Weather for {city} \n{current_weather}\n\n"
            f"5-Day Forecast for {city} \n{forecast}"
        )
        logger.info(f"Weather Agent: Successfully retrieved weather data for '{city}'.")

    except Exception as error:
        logger.error(f"Weather Agent Failed: {str(error)}", exc_info=True)
        weather_data = f"Weather data unavailable for {city}: {str(error)}"

    # Return updated state dictionary to pass to final_agent
    return {
        "weather_results": weather_data,
        "messages": [AIMessage(content=f"Weather information fetched for {city}.")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


__all__ = ["weather_agent", "extract_destination"]
