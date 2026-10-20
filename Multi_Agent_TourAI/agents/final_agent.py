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
    Dynamically crafts the response depending on intent:
    1. follow_up: Answers questions directly using conversation memory & prior itinerary.
    2. specific_query: Formats specific specialist data (flight, hotel, or weather only).
    3. new_plan: Generates the full comprehensive 7-section travel plan.
    """
    intent = state.get("intent", "new_plan")
    user_query = state.get("user_query", "")

    # CASE 1: Follow-up Conversation (Memory-based response)
    if intent == "follow_up":
        logger.info("Final Agent: Answering follow-up query from memory and itinerary...")
        existing_itinerary = state.get("itinerary", "")
        flight_info = state.get("flight_results", "")
        hotel_info = state.get("hotel_results", "")
        weather_info = state.get("weather_results", "")

        system_instruction = (
            "You are an expert AI Travel Assistant. The traveler is asking a follow-up question, "
            "requesting a modification, or asking for clarifications about their travel plan.\n\n"
            "Below is the current context stored in memory:\n"
            f"=== EXISTING ITINERARY ===\n{existing_itinerary}\n\n"
            f"=== FLIGHT DETAILS ===\n{flight_info}\n\n"
            f"=== HOTEL DETAILS ===\n{hotel_info}\n\n"
            f"=== WEATHER DETAILS ===\n{weather_info}\n\n"
            "Answer the traveler's question directly, clearly, and concisely using the above context."
        )

        chat_history = state.get("messages", [])

        messages_payload = [
            SystemMessage(content=system_instruction),
            *chat_history,
            HumanMessage(content=user_query),
        ]

        response = smart_llm.invoke(messages_payload)
        return {
            "messages": [response],
            "llm_calls": 1,
        }

    # CASE 2: Specific Query (Flight only / Hotel only / Weather only / Itinerary only)
    if intent == "specific_query":
        logger.info("Final Agent: Formatting specific single-service inquiry...")
        specific_prompt = (
            f"The user specifically asked for: '{user_query}'\n\n"
            f"Collected Flight Data: {state.get('flight_results', 'None')}\n"
            f"Collected Hotel Data: {state.get('hotel_results', 'None')}\n"
            f"Collected Weather Data: {state.get('weather_results', 'None')}\n"
            f"Collected Itinerary Data: {state.get('itinerary', 'None')}\n\n"
            "Provide a helpful, nicely formatted answer addressing ONLY the user's specific request. "
            "Do not include empty sections for services the user did not ask for."
        )

        response = smart_llm.invoke([
            SystemMessage(content=FINAL_RESPONSE_SYSTEM_PROMPT),
            HumanMessage(content=specific_prompt),
        ])
        return {
            "messages": [response],
            "llm_calls": 1,
        }


    # CASE 3: Full New Travel Plan (Standard 7-section guide)
    logger.info("Final Agent: Synthesizing full travel response package...")
    prompt = FINAL_RESPONSE_PROMPT_TEMPLATE.format(
        user_query=state.get("user_query", ""),
        flight_results=state.get("flight_results", ""),
        hotel_results=state.get("hotel_results", ""),
        itinerary=state.get("itinerary", ""),
        weather_results=state.get("weather_results", "Weather data not available."),
    )

    response = smart_llm.invoke([
        SystemMessage(content=FINAL_RESPONSE_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])

    return {
        "messages": [response],
        "llm_calls": 1,
    }


__all__ = ["final_response_agent"]