import asyncio
from langchain_core.messages import AIMessage
from Multi_Agent_TourAI.graph.state import TravelState
from Multi_Agent_TourAI.mcp.geoapify_mcp import (geoapify_mcp_search_places, geoapify_mcp_calculate_route,)
from Multi_Agent_TourAI.llms.llm import fast_llm
from Multi_Agent_TourAI.config.prompts import DESTINATION_EXTRACTOR_PROMPT_TEMPLATE
from Multi_Agent_TourAI.utils import get_logger, log_execution

logger = get_logger(__name__)


def extract_destination(query: str) -> str:
    """Extracts destination city from user travel query using fast_llm."""
    try:
        prompt = DESTINATION_EXTRACTOR_PROMPT_TEMPLATE.format(query=query)
        response = fast_llm.invoke(prompt)
        return response.content.strip(" .\n\"'")
    except Exception as e:
        logger.warning(f"Destination extraction fallback: {e}")
        return query


@log_execution
def maps_agent(state: TravelState):
    """
    Maps, Places & Routing Agent Node for LangGraph:
    1. Reads user_query from shared state.
    2. Identifies user intent: Route/Distance, Cafes/Dining, or Top Attractions.
    3. Calls Geoapify Remote MCP tools asynchronously.
    4. Updates shared state with 'maps_results'.
    """
    query = state.get("user_query", "")
    city = extract_destination(query)
    query_lower = query.lower()
    logger.info(f"Maps Agent: Processing query for '{city}' (Query: '{query}')...")

    maps_data = ""
    try:
        # Case 1: Route / Distance query between two places
        if any(kw in query_lower for kw in ["how far", "distance between", "route from", "drive from", "travel from", "to get to"]):
            route_extract_prompt = (
                f"Extract the origin and destination from this travel query: '{query}'.\n"
                "Return strict format: ORIGIN | DESTINATION\n"
                "Example: Tokyo | Kyoto"
            )
            route_resp = fast_llm.invoke(route_extract_prompt).content.strip()
            if "|" in route_resp:
                parts = [p.strip() for p in route_resp.split("|")]
                if len(parts) >= 2:
                    origin, destination = parts[0], parts[1]
                    logger.info(f"Maps Agent: Calculating route from '{origin}' to '{destination}'...")
                    maps_data = asyncio.run(geoapify_mcp_calculate_route(origin, destination))

        # Case 2: Food / Dining / Cafe specific query
        if not maps_data:
            if any(kw in query_lower for kw in ["cafe", "coffee", "bakery"]):
                logger.info(f"Maps Agent: Searching cafes in '{city}'...")
                maps_data = asyncio.run(geoapify_mcp_search_places(city, category="catering.cafe", limit=5))
            elif any(kw in query_lower for kw in ["restaurant", "food", "dining", "lunch", "dinner", "eat"]):
                logger.info(f"Maps Agent: Searching restaurants in '{city}'...")
                maps_data = asyncio.run(geoapify_mcp_search_places(city, category="catering.restaurant", limit=5))

        # Case 3: Default - Tourist Attractions & Sights for Itinerary
        if not maps_data:
            logger.info(f"Maps Agent: Searching top tourist attractions in '{city}'...")
            maps_data = asyncio.run(geoapify_mcp_search_places(city, category="tourism.sights", limit=5))

        logger.info(f"Maps Agent: Successfully retrieved location data for '{city}'.")

    except Exception as error:
        logger.error(f"Maps Agent Failed: {str(error)}", exc_info=True)
        maps_data = f"Maps and attractions data unavailable for {city}: {str(error)}"

    return {
        "maps_results": maps_data,
        "messages": [AIMessage(content=f"Location and maps details fetched for {city}.")],
        "llm_calls": 1,
    }


__all__ = ["maps_agent", "extract_destination"]
