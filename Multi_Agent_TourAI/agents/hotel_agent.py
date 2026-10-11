import asyncio
from langchain_core.messages import AIMessage
from Multi_Agent_TourAI.graph.state import TravelState
# from Multi_Agent_TourAI.tools.tavily_tool import tavily_search  # uncomment when using custom implement search tool via tavily_api
from Multi_Agent_TourAI.mcp.tavily_mcp import tavily_mcp_search
from Multi_Agent_TourAI.utils import get_logger, log_execution


logger = get_logger(__name__)

@log_execution
def hotel_agent(state:TravelState):
    query = f"best hotels for {state['user_query']}"
    
    logger.info(f"Searching hotels via Tavily: '{query}'")
    # hotel_results = tavily_search(query) # uncomment when using - from Multi_Agent_TourAI.tools.tavily_tool...
    hotel_results = asyncio.run(tavily_mcp_search(query))
    return {
        "hotel_results": hotel_results,
        "messages": [AIMessage(content="Hotel information fetched.")],
        "llm_calls": state.get("llm_calls", 0)+1
    }