from langchain_core.messages import AIMessage
from Multi_Agent_TourAI.graph.state import TravelState
from Multi_Agent_TourAI.tools.flight_tool import flight_search


def flight_agent(state: TravelState):
    query = state["user_query"]
    flight_data = flight_search(query=query)

    return {
        "flight_results": flight_data,
        "messages": [AIMessage(content="Flight result fetched.")],
        "llm_calls": state.get("llm_calls", 0)+1
    }