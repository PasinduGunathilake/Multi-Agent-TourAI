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

    # Flag indicating whether the user request passed input guardrail validation
    guardrail_allowed: bool

    # Rejection explanation or safety refusal message if the request was blocked
    guardrail_reason: str

    ### Supervisor Agent States (1.intent, 2.select agents, 3.reasoning) ###
    # 1. Intent category determined by Supervisor: "new_plan" or "follow_up"
    intent: str

    # 2. List of specialist agent names selected by the supervisor
    selected_agents: list[str]

    # 3. Reasoning behind the supervisor's routing decision
    supervisor_reasoning: str


__all__ = ["TravelState"]
