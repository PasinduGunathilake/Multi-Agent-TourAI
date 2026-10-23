from langchain_core.messages import SystemMessage, HumanMessage
from Multi_Agent_TourAI.graph.state import TravelState
from Multi_Agent_TourAI.llms.llm import smart_llm
from Multi_Agent_TourAI.config.prompts import (ITINERARY_SYSTEM_PROMPT, ITINERARY_PROMPT_TEMPLATE,)
from Multi_Agent_TourAI.utils import get_logger, log_execution

logger = get_logger(__name__)

@log_execution
def itinerary_agent(state: TravelState):

    logger.info("Generating tour plan using LLM...")
    prompt = ITINERARY_PROMPT_TEMPLATE.format(
        user_query = state.get("user_query", ""),
        flight_results = state.get("flight_results", "Not requested."),
        hotel_results = state.get("hotel_results", "Not requested."),
        weather_results = state.get("weather_results", "Not requested."),
        maps_results = state.get("maps_results", "Not requested.")
    )
    response = smart_llm.invoke([
        SystemMessage(content=ITINERARY_SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])

    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_calls": 1
    }