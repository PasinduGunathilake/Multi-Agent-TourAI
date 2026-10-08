import uuid
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
from Multi_Agent_TourAI.graph.state import TravelState
from Multi_Agent_TourAI.agents.flight_agent import flight_agent
from Multi_Agent_TourAI.agents.hotel_agent import hotel_agent
from Multi_Agent_TourAI.agents.itinerary_agent import itinerary_agent
from Multi_Agent_TourAI.agents.final_agent import final_response_agent
from Multi_Agent_TourAI.memory.checkpointer import get_checkpointer
from Multi_Agent_TourAI.utils import get_logger, log_execution

logger = get_logger(__name__)

# 1.StateGraph and Nodes
graph = StateGraph(TravelState)

graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("final_agent", final_response_agent)

# 2.Edges- flow
graph.add_edge(START, "flight_agent")
graph.add_edge("flight_agent", "hotel_agent")
graph.add_edge("hotel_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", "final_agent")
graph.add_edge("final_agent", END)

# 3.Checkpointer/persistant short-term memory Compile 
checkpointer = get_checkpointer()
travel_graph = graph.compile(checkpointer=checkpointer)



# run agent
@log_execution
def run_travel_agent(user_input: str, thread_id: str | None = None) -> dict:
    if not thread_id:
        thread_id = f"user_{uuid.uuid4().hex}"

    logger.info(f"Initializing Workflow | Thread ID: {thread_id} | Query: '{user_input}'")
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }
    result = travel_graph.invoke(
        {
            "messages": [HumanMessage(content=user_input)],
            "user_query": user_input,
            "flight_results": "",
            "hotel_results": "",
            "itinerary": "",
            "llm_calls": 0,
        },
        config=config,
    )
    final_result = result["messages"][-1].content
    logger.info(f"Workflow finished | Total LLM calls: {result.get('llm_calls', 0)}")

    return {
        "thread_id": thread_id,
        "answer": final_result,
        "flight_results": result.get("flight_results", ""),
        "hotel_results": result.get("hotel_results", ""),
        "itinerary": result.get("itinerary", ""),
        "llm_calls": result.get("llm_calls", 0),
    }