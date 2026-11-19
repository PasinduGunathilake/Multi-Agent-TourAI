from langchain_core.messages import AIMessage
from Multi_Agent_TourAI.graph.state import TravelState
from Multi_Agent_TourAI.mcp.tavily_mcp import tavily_mcp_search
from Multi_Agent_TourAI.utils import get_logger, log_execution, run_async_safely

logger = get_logger(__name__)

# Max character limit for hotel search results to optimize prompt tokens
MAX_HOTEL_CHAR_LIMIT = 1500


@log_execution
def hotel_agent(state: TravelState):
    """
    Hotel Agent Node for LangGraph:
    Searches accommodations using Tavily Remote MCP asynchronously.
    Executes via loop-safe bridge and bounds output context.
    """
    query = f"best hotels for {state.get('user_query', '')}"

    logger.info(f"Searching hotels via Tavily: '{query}'")
    try:
        raw_results = run_async_safely(tavily_mcp_search(query))
        s = str(raw_results or "").strip()
        hotel_results = s[:MAX_HOTEL_CHAR_LIMIT] + ("..." if len(s) > MAX_HOTEL_CHAR_LIMIT else "")
    except Exception as e:
        logger.error(f"Hotel Agent failed: {e}", exc_info=True)
        hotel_results = f"Hotel recommendations currently unavailable: {str(e)}"

    return {
        "hotel_results": hotel_results,
        "messages": [AIMessage(content="Hotel information fetched.")],
        "llm_calls": 0,
    }


__all__ = ["hotel_agent"]
