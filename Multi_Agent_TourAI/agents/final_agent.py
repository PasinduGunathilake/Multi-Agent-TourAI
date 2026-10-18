from langchain_core.messages import SystemMessage, HumanMessage
from Multi_Agent_TourAI.graph.state import TravelState
from Multi_Agent_TourAI.llms.llm import smart_llm
from Multi_Agent_TourAI.config.prompts import (
    FINAL_RESPONSE_SYSTEM_PROMPT,
    FINAL_RESPONSE_PROMPT_TEMPLATE,
)
from Multi_Agent_TourAI.utils import get_logger, log_execution

# Set up logging for this agent
logger = get_logger(__name__)


@log_execution
def final_response_agent(state: TravelState):
    """
    Final Response Agent:
    Combines all collected data (flights, hotels, itinerary, and weather)
    into one nicely formatted travel guide for the user.
    """
    logger.info("Synthesizing final travel response package...")

    # Fill in the prompt template with data collected from all earlier agents
    prompt = FINAL_RESPONSE_PROMPT_TEMPLATE.format(
        user_query=state["user_query"],
        flight_results=state["flight_results"],
        hotel_results=state["hotel_results"],
        itinerary=state["itinerary"],
        weather_results=state.get("weather_results", "Weather data not available."),
    )

    # Ask the LLM to write the final polished response
    response = smart_llm.invoke([
        SystemMessage(content=FINAL_RESPONSE_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


__all__ = ["final_response_agent"]