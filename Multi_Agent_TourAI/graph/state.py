from typing import TypedDict, Annotated
import operator
from langchain_core.messages import AnyMessage

# Shared State Definition for LangGraph
class TravelState(TypedDict):
    """
    TravelState holds all shared data passed between agents in the workflow.
    Each agent reads from and updates this dictionary.
    """
    # Conversation history: messages are appended using operator.add
    messages: Annotated[list[AnyMessage], operator.add]
    
    # User's raw question or request
    user_query: str
    
    # Output from flight_agent (Aviationstack MCP)
    flight_results: str
    
    # Output from hotel_agent (Tavily Remote MCP)
    hotel_results: str
    
    # Output from itinerary_agent (Day-by-day plan)
    itinerary: str
    
    # Output from weather_agent (FastMCP OpenWeatherMap)
    weather_results: str
    
    # Counter for total LLM calls across the workflow
    llm_calls: Annotated[int, operator.add]  # values are summed up automatically using operator.add


__all__ = ["TravelState"]
