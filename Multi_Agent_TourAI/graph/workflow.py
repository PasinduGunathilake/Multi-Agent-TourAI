import uuid
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
from Multi_Agent_TourAI.graph.state import TravelState
from Multi_Agent_TourAI.agents.flight_agent import flight_agent
from Multi_Agent_TourAI.agents.hotel_agent import hotel_agent
from Multi_Agent_TourAI.agents.itinerary_agent import itinerary_agent
from Multi_Agent_TourAI.agents.weather_agent import weather_agent
from Multi_Agent_TourAI.agents.final_agent import final_response_agent
from Multi_Agent_TourAI.memory.checkpointer import get_checkpointer
from Multi_Agent_TourAI.memory.store import get_store
from Multi_Agent_TourAI.guardrails.inputguardrail import input_guardrail, guardrail_blocked
from Multi_Agent_TourAI.utils import get_logger, log_execution

# Initialize logger
logger = get_logger(__name__)


# 1. Build the Multi-Agent StateGraph
# Define the graph with our shared state schema (TravelState)
graph = StateGraph(TravelState)

# Add Guardrail nodes to the graph
graph.add_node("input_guardrail", input_guardrail)
graph.add_node("guardrail_blocked", guardrail_blocked)
# Add all 5 agent nodes to the graph
graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("weather_agent", weather_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("final_agent", final_response_agent)






# 2. Define Execution Flow (Edges)
'''
#### Method 1: The sequential/ Synchronous multi-agent execution pipeline: slow execution

# START ---------> Flight Agent ---------> Hotel Agent ---------> Weather Agent ---------> Itinerary Agent ---------> Final ---------> END

graph.add_edge(START, "flight_agent")
graph.add_edge("flight_agent", "hotel_agent")
graph.add_edge("hotel_agent", "weather_agent")
graph.add_edge("weather_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", "final_agent")
graph.add_edge("final_agent", END) 
'''

#### Method 2: The Parallel / Asynchronous multi-agent execution pipeline: faster execution (~x3 times speed than 1st methode)
'''
                                                         -- flight_agent --+
                                                        |                  |
START -> input_guardrail  +---- [allowed == True] +----- -- hotel_agent ---+ ----> itinerary_agent -> final_agent -> END
                    |                                   |                  |
                    |                                    -- weather_agent -+
                    |                                   
                    +-------- [allowed == False] -------> guardrail_blocked ---------------------------> END



WHY WE CAN USE THIS PARALLEL APPROACH:

1. Data Independence:
   - Flight Agent, Hotel Agent, and Weather Agent are completely INDEPENDENT of each other.
   - They only need the destination city from the user query (e.g. 'Dubai').
   - Hotel Agent does not need Flight data to search hotels, and Weather Agent does not need Hotel data.
   - Therefore, running them sequentially wastes time. They can run concurrently (at the same time).

2. Data Dependency:
   - Only the Itinerary Agent depends on the outputs of all three (flights, hotels, and weather)
     to build a realistic day-by-day plan.
   - Hence, Itinerary Agent waits until all 3 parallel agents finish before executing.

'''
# 2. Graph Edges & Routing Logic

# Route from START to the Input Guardrail
graph.add_edge(START, "input_guardrail")


# Conditional Router: Directs traffic based on Guardrail validation
def route_after_guardrail(state: TravelState):
    """
    Evaluates whether the user request is allowed by the input guardrail.
    - If allowed: triggers the 3 parallel agents (flight, hotel, weather).
    - If blocked: routes directly to the guardrail_blocked terminal node.
    """
    if state.get("guardrail_allowed", True):
        # Query is travel-related -> Run parallel independent agents
        return ["flight_agent", "hotel_agent", "weather_agent"]
    else:
        # Off-topic or harmful query -> Route to blocked exit node
        return ["guardrail_blocked"]


# Add conditional edges from the guardrail inspection
graph.add_conditional_edges(
    "input_guardrail",
    route_after_guardrail,
    ["flight_agent", "hotel_agent", "weather_agent", "guardrail_blocked"],
)

# Parallel synchronization: Wait for all 3 agents to finish, then pass data to Itinerary Agent
graph.add_edge("flight_agent", "itinerary_agent")
graph.add_edge("hotel_agent", "itinerary_agent")
graph.add_edge("weather_agent", "itinerary_agent")

# Sequential flow: Itinerary Agent -> Final Response Agent -> END
graph.add_edge("itinerary_agent", "final_agent")
graph.add_edge("final_agent", END)

# Early exit: Blocked requests terminate immediately without executing external APIs or LLMs
graph.add_edge("guardrail_blocked", END)






# 3. Compile Graph with Checkpointer (Persistent Short-Term Memory) and Store (Persistance Long-Term Memory)
# Uses PostgreSQL checkpointer to maintain persistent short-term memory per thread
checkpointer = get_checkpointer()
store = get_store()

travel_graph = graph.compile(checkpointer=checkpointer, store=store)






# 4. Workflow Runner Function
@log_execution
def run_travel_agent(user_input: str, thread_id: str | None = None, user_id: str | None = None) -> dict:
    """
    Main function to run the full travel planner agent workflow.

    Parameters:
        user_input (str): The travel query provided by the user.
        thread_id (str, optional): A unique ID for session persistence.

    Returns:
        dict: Final answer and step-by-step results from all agents.
    """
    if not thread_id:
        thread_id = f"user_{uuid.uuid4().hex}"

    if not user_id:
        user_id = "default_user"

    logger.info(f"Initializing Workflow | Thread: {thread_id} | User: {user_id}  | Query: '{user_input}'")

    config = {
        "configurable": {
            "thread_id": thread_id, # Checkpointer - current session (short term)
            "user_id": user_id # Store - permenents user profile (long term)
        }
    }

    # Invoke the graph with the initial state dictionary
    result = travel_graph.invoke(
        {
            "messages": [HumanMessage(content=user_input)],
            "user_query": user_input,
            "flight_results": "",
            "hotel_results": "",
            "weather_results": "",
            "itinerary": "",
            "llm_calls": 0,
            "guardrail_allowed": True,
            "guardrail_reason": "",
        },
        config=config,
    )

    final_result = result["messages"][-1].content
    logger.info(f"Workflow finished | Total LLM calls: {result.get('llm_calls', 0)}")

    return {
        "thread_id": thread_id,
        "user_id": user_id,
        "answer": final_result,
        "flight_results": result.get("flight_results", ""),
        "hotel_results": result.get("hotel_results", ""),
        "weather_results": result.get("weather_results", ""),
        "itinerary": result.get("itinerary", ""),
        "llm_calls": result.get("llm_calls", 0),
        "guardrail_allowed": result.get("guardrail_allowed", True),
        "guardrail_reason": result.get("guardrail_reason", ""),
    }


__all__ = ["graph", "travel_graph", "run_travel_agent"]