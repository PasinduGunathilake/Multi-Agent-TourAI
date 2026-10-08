from langchain_core.messages import SystemMessage, HumanMessage
from Multi_Agent_TourAI.graph.state import TravelState
from Multi_Agent_TourAI.llms.llm import llm
from Multi_Agent_TourAI.config.prompts import (FINAL_RESPONSE_SYSTEM_PROMPT, FINAL_RESPONSE_PROMPT_TEMPLATE,)

def final_response_agent(state: TravelState):
    prompt = FINAL_RESPONSE_PROMPT_TEMPLATE.format(
        user_query=state["user_query"],
        flight_results=state["flight_results"],
        hotel_results=state["hotel_results"],
        itinerary=state["itinerary"],
    )
    response = llm.invoke([
        SystemMessage(content=FINAL_RESPONSE_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0)+1
    }