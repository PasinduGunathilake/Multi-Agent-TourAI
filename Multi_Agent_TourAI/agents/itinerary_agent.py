from langchain_core.messages import SystemMessage, HumanMessage
from Multi_Agent_TourAI.graph.state import TravelState
from Multi_Agent_TourAI.llms.llm import llm
from Multi_Agent_TourAI.config.prompts import (ITINERARY_SYSTEM_PROMPT, ITINERARY_PROMPT_TEMPLATE,)

def itinerary_agent(state: TravelState):
    prompt = ITINERARY_PROMPT_TEMPLATE.format(
        user_query = state["user_query"],
        flight_results = state["flight_results"],
        hotel_results = state["hotel_results"],
    )
    response = llm.invoke([
        SystemMessage(content=ITINERARY_SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])

    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0)+1
    }