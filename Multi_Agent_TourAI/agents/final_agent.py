from langchain_core.messages import SystemMessage, HumanMessage
from Multi_Agent_TourAI.graph.state import TravelState
from Multi_Agent_TourAI.llms.llm import smart_llm
from Multi_Agent_TourAI.config.prompts import (FINAL_RESPONSE_SYSTEM_PROMPT, FINAL_RESPONSE_PROMPT_TEMPLATE,)
from Multi_Agent_TourAI.utils import get_logger, log_execution

# Set up logging for this agent
logger = get_logger(__name__)

# Final Response agent with HITL feedback
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
        maps_info = state.get("maps_results", "")


        system_instruction = (
            "You are an expert AI Travel Assistant. The traveler is asking a follow-up question, "
            "requesting a modification, or asking for clarifications about their travel plan.\n\n"
            "Below is the current context stored in memory:\n"
            f"=== EXISTING ITINERARY ===\n{existing_itinerary}\n\n"
            f"=== FLIGHT DETAILS ===\n{flight_info}\n\n"
            f"=== HOTEL DETAILS ===\n{hotel_info}\n\n"
            f"=== ATTRACTIONS & MAP DETAILS ===\n{maps_info}\n\n"
            f"=== WEATHER DETAILS ===\n{weather_info}\n\n"
            "Answer the traveler's question directly, clearly, and concisely using the above context."
        )

        # Keep only recent dialogue messages to prevent prompt bloat and Groq TPM limits
        all_messages = state.get("messages", [])
        recent_chat = all_messages[-3:] if len(all_messages) > 3 else all_messages
        if recent_chat and recent_chat[-1].content == user_query:
            recent_chat = recent_chat[:-1]

        messages_payload = [
            SystemMessage(content=system_instruction),
            *recent_chat,
            HumanMessage(content=user_query),
        ]

        response = smart_llm.invoke(messages_payload)
        return {
            "final_response": response.content,
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
            f"Collected Maps/Attractions Data: {state.get('maps_results', 'None')}\n"
            f"Collected Itinerary Data: {state.get('itinerary', 'None')}\n\n"
            "Provide a helpful, nicely formatted answer addressing ONLY the user's specific request. "
            "Do not include empty sections for services the user did not ask for."
        )

        response = smart_llm.invoke([
            SystemMessage(content=FINAL_RESPONSE_SYSTEM_PROMPT),
            HumanMessage(content=specific_prompt),
        ])
        return {
            "final_response": response.content,
            "messages": [response],
            "llm_calls": 1,
        }


    # CASE 3: Full New Travel Plan (Standard 7-section guide)
    logger.info("Final Agent: Synthesizing full travel response package...")

    # Get HITL Feedback from user
    approved = state.get("approved", True)
    feedback = state.get("human_feedback", "")

    if approved:
        review_instruction = (
            "The user approved the draft itinerary. Preserve its key decisions "
            "and craft a polished, professional final travel response."
        )
    else:
        review_instruction = (
            f"The user requested revisions to the draft itinerary. "
            f"Carefully incorporate this user feedback: '{feedback}'."
        )

    prompt = FINAL_RESPONSE_PROMPT_TEMPLATE.format(
        review_instruction=review_instruction,
        user_query=state.get("user_query", ""),
        flight_results=state.get("flight_results", ""),
        hotel_results=state.get("hotel_results", ""),
        maps_results=state.get("maps_results", "Attractions data not available."),
        itinerary=state.get("itinerary", ""),
        weather_results=state.get("weather_results", "Weather data not available."),
    )

    response = smart_llm.invoke([
        SystemMessage(content=FINAL_RESPONSE_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])

    return {
        "final_response": response.content,
        "messages": [response],
        "llm_calls": 1,
    }


__all__ = ["final_response_agent"]