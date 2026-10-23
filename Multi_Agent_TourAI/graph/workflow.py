import uuid
from langgraph.types import Command # for human approval flow
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
from Multi_Agent_TourAI.graph.state import TravelState
from Multi_Agent_TourAI.agents.flight_agent import flight_agent
from Multi_Agent_TourAI.agents.hotel_agent import hotel_agent
from Multi_Agent_TourAI.agents.itinerary_agent import itinerary_agent
from Multi_Agent_TourAI.agents.weather_agent import weather_agent
from Multi_Agent_TourAI.agents.maps_agent import maps_agent
from Multi_Agent_TourAI.agents.final_agent import final_response_agent
from Multi_Agent_TourAI.memory.checkpointer import get_checkpointer
from Multi_Agent_TourAI.memory.store import get_store
from Multi_Agent_TourAI.guardrails.inputguardrail import input_guardrail, guardrail_blocked
from Multi_Agent_TourAI.agents.supervisor_agent import supervisor_agent
from Multi_Agent_TourAI.agents.approval_agent import human_approval_agent
from Multi_Agent_TourAI.utils import get_logger, log_execution

# Initialize logger
logger = get_logger(__name__)


# 1. Build the Multi-Agent StateGraph
# Define the graph with our shared state schema (TravelState)
graph = StateGraph(TravelState)

# Add Guardrail nodes to the graph
graph.add_node("input_guardrail", input_guardrail)
graph.add_node("guardrail_blocked", guardrail_blocked)
# Add supervisor node to the graph
graph.add_node("supervisor", supervisor_agent)
# Add HITL node to the graph
graph.add_node("human_approval", human_approval_agent)
# Add all 6 agent nodes to the graph
graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("weather_agent", weather_agent)
graph.add_node("maps_agent", maps_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("final_agent", final_response_agent)





# 2. Define Execution Flow (Edges)

#### Method 1: The sequential/ (Synchronous) multi-agent execution pipeline: slow execution
'''
# START ---------> Flight Agent ---------> Hotel Agent ---------> Weather Agent ---------> Itinerary Agent ---------> Final ---------> END

graph.add_edge(START, "flight_agent")
graph.add_edge("flight_agent", "hotel_agent")
graph.add_edge("hotel_agent", "weather_agent")
graph.add_edge("weather_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", "final_agent")
graph.add_edge("final_agent", END) 
'''

#### Method 2: Dynamic Intent-Aware, Parallel (Asynchronous) & HITL Multi-Agent Pipeline (Current Production Architecture)
'''
                                  ┌───────┐
                                  │ START │
                                  └───┬───┘
                                      │
                                      ▼
                            ┌───────────────────┐
                            │  input_guardrail  │
                            └─────────┬─────────┘
                                      │
              ┌───────────────────────┴───────────────────────┐
              │ [allowed == False]                            │ [allowed == True]
              ▼                                               ▼
    ┌───────────────────┐                               ┌────────────┐
    │ guardrail_blocked │                               │ supervisor │
    └─────────┬─────────┘                               └─────┬──────┘
              │                                               │
              │         ┌─────────────────────────────────────┼──────────────────────────────────┐
              │         │                                     │                                  │
              │         │ (1. new_plan)                       │ (2. specific_query)              │ (3. follow_up)
              │         ▼                                     ▼                                  │
              │  ┌──────────────┐                       ┌──────────────┐                         │
              │  │ Parallel Fan │                       │ Single Tool  │                         │
              │  │  • flight    │                       │  • flight    │                         │
              │  │  • hotel     │                       │  • hotel     │                         │
              │  │  • weather   │                       │  • weather   │                         │
              │  │  • maps      │                       │  • maps      │                         │
              │  └──────┬───────┘                       └──────┬───────┘                         │
              │         │                                      │                                 │
              │         │ [new_plan]                           │ [specific_query]                │
              │         ▼                                      │                                 │
              │  ┌─────────────────┐                           │                                 │
              │  │ itinerary_agent │ ◄── (Itinerary Only) ─────┤                                 │
              │  └────────┬────────┘                           │                                 │
              │           │                                    │                                 │
              │           ▼                                    │                                 │
              │  ┌──────────────────┐                          │                                 │
              │  │  human_approval  │                          │                                 │
              │  │  (HITL Pause)    │                          │                                 │
              │  └────────┬─────────┘                          │                                 │
              │           │                                    │                                 │
              │           │ [Approved / Feedback Applied]      │                                 │
              │           └──────────────────┐                 │                                 │
              │                              ▼                 ▼                                 ▼
              │                     ┌──────────────────────────────────────────────────────────────┐
              │                     │                         final_agent                          │
              │                     │ (Itinerary Polish / Specific Summary / Conversational Chat)  │
              │                     └──────────────────────────────┬───────────────────────────────┘
              │                                                    │
              └───────────────────────────────┬────────────────────┘
                                              ▼
                                           ┌─────┐
                                           │ END │
                                           └─────┘


WHY WE USE THIS DYNAMIC PARALLEL & INTENT-AWARE PIPELINE:

1. Data Independence & Parallel Latency Reduction (Fan-Out):
   - Flight, Hotel, Weather, and Maps agents are completely INDEPENDENT of each other.
   - They only need the destination city from the user query (e.g. 'Dubai').
   - Hotel Agent does not need Flight data to search hotels, and Weather/Maps Agents do not need Hotel data.
   - Running them concurrently allows the slowest branch to dictate tool latency rather than 
     their cumulative sum:
        T_sequential = T_flight (~21s) + T_hotel (~8s) + T_weather (~3s) + T_maps (~2s) = ~34s
        T_parallel   = max(T_flight, T_hotel, T_weather, T_maps) = max(21s, 8s, 3s, 2s) = ~21s
     -> Yields an immediate ~38% - 40% reduction in external tool wait time!

2. Data Dependency & Synchronization (Fan-In):
   - Only the Itinerary Agent depends on the outputs of all four (flights, hotels, weather, and maps)
     to build a realistic, geographically clustered day-by-day plan.
   - Hence, for full vacation plans, Itinerary Agent acts as a barrier that waits until all 
     selected parallel agents finish before executing.

3. Human-in-the-Loop (HITL) Verification & Review:
   - Pauses execution via interrupt() immediately after the draft itinerary is generated.
   - Allows the traveler to inspect the draft plan, approve it, or submit custom modifications.
   - Preserves state in PostgreSQL checkpoints until the user resumes with Command(resume=...).

4. Intent-Driven Conditional Routing (Zero-Tool Bypass):
   - 'follow_up' Intent: 
     When user asks questions about an existing plan (e.g. "expenses in USD?"), all external 
     tools and approval checks are 100% BYPASSED (0.0s tool time). 
     Final Agent synthesizes the response in ~1-2s directly from PostgresSaver checkpointer memory!
   - 'specific_query' Intent: 
     Runs strictly the requested single specialist agent and bypasses Itinerary and Approval agents.
     Example: Weather inquiry finishes in ~4-6s instead of ~35s!

5. Guardrail Early-Exit Security:
   - Evaluates request safety and travel relevance in ~0.5s.
   - Unrelated, malicious, or adversarial prompts are blocked immediately before triggering any 
     expensive LLMs or external API calls.
'''
# 2. Graph Edges & Routing Logic

# Route from START to the Input Guardrail
graph.add_edge(START, "input_guardrail")


# Conditional Router: Directs traffic based on Guardrail validation
def route_after_guardrail(state: TravelState):
    """
    Evaluates whether the user request is allowed by the input guardrail.
    - If allowed: triggers the 4 parallel agents (flight, hotel, weather, maps).
    - If blocked: routes directly to the guardrail_blocked terminal node.
    """
    if state.get("guardrail_allowed", True):
        # Query is travel-related -> Run Supervisor agent
        return "supervisor"
    # Off-topic or harmful query -> Route to blocked exit node
    return "guardrail_blocked"


# Add conditional edges from the guardrail inspection
graph.add_conditional_edges(
    "input_guardrail",
    route_after_guardrail,
    {
        "supervisor":"supervisor",
        "guardrail_blocked":"guardrail_blocked",
    },
)

# Supervisor Route: Distribute traffic
def route_from_supervisor(state: TravelState):
    intent = state.get("intent", "new_plan")
    selected_agents = state.get("selected_agents", [])

    # if query is Follow_up -> final agent (with memory)
    if intent == "follow_up":
        logger.info("Supervisor routed: Follow-up -> Direct to final_agent.")
        return ["final_agent"]

    # if query about specific Query (Weather only, Hotel only, Flight only, Itinerary only)
    if intent == "specific_query" and selected_agents:
        logger.info(f"Supervisor routed: Specific Query -> Running {selected_agents}")
        return selected_agents

    # if Travel plan -> parallel....
    logger.info("Supervisor routed: Full Travel Plan -> Running parallel tool agents.")
    return ["flight_agent", "hotel_agent", "weather_agent", "maps_agent"]

# Supervisor Possible Target Nodes
graph.add_conditional_edges(
    "supervisor",
    route_from_supervisor,
    ["flight_agent", "hotel_agent", "weather_agent", "maps_agent", "itinerary_agent", "final_agent"],
)

# Route after specialist tool:
def route_after_tool(state: TravelState):
    """
    Directs flow after a specialist tool agent executes:
    - If user asked for a specific tool (specific_query) -> skip itinerary, go straight to final_agent.
    - If user asked for a full travel plan (new_plan) -> proceed to itinerary_agent.
    """
    intent = state.get("intent", "new_plan")
    if intent == "specific_query":
        return "final_agent"
    return "itinerary_agent"


# Flight, Hotel, and Weather conditional edges
graph.add_conditional_edges(
    "flight_agent",
    route_after_tool,
    {"itinerary_agent": "itinerary_agent", "final_agent": "final_agent"},
)
graph.add_conditional_edges(
    "hotel_agent",
    route_after_tool,
    {"itinerary_agent": "itinerary_agent", "final_agent": "final_agent"},
)
graph.add_conditional_edges(
    "weather_agent",
    route_after_tool,
    {"itinerary_agent": "itinerary_agent", "final_agent": "final_agent"},
)
graph.add_conditional_edges(
    "maps_agent",
    route_after_tool,
    {"itinerary_agent": "itinerary_agent", "final_agent": "final_agent"},
)


# Sequential flow: Itinerary Agent -> Human Approval Agent -> Final Response Agent -> END
graph.add_edge("itinerary_agent", "human_approval")
graph.add_edge("human_approval", "final_agent")
graph.add_edge("final_agent", END)

# Early exit: Blocked requests terminate immediately without executing external APIs or LLMs
graph.add_edge("guardrail_blocked", END)


# 3. Compile Graph with Checkpointer (Persistent Short-Term Memory) and Store (Persistance Long-Term Memory)
# Uses PostgreSQL checkpointer to maintain persistent short-term memory per thread
checkpointer = get_checkpointer()
store = get_store()

travel_graph = graph.compile(checkpointer=checkpointer, store=store)






# 4. Result Serializer & Workflow Runner Functions

def _serialize_workflow_result(result: dict, thread_id: str, user_id: str) -> dict:
    """
    Serializes LangGraph result into a structured dictionary.
    Handles HITL interrupt payloads if paused at human_approval node.
    """
    interrupts = result.get("__interrupt__", [])
    interrupt_payload = None
    if interrupts:
        first_interrupt = interrupts[0]
        payload = getattr(first_interrupt, "value", first_interrupt)
        interrupt_payload = payload if isinstance(payload, dict) else {"value": payload}

    messages = result.get("messages", [])
    last_msg = messages[-1].content if messages else ""
    answer = result.get("final_response") or last_msg

    requires_approval = interrupt_payload is not None
    if requires_approval and interrupt_payload:
        # Paused on human approval: present draft itinerary to human
        answer = interrupt_payload.get("draft_itinerary") or result.get("itinerary", "")
        approval_question = interrupt_payload.get("question", "Do you approve this draft itinerary?")
    else:
        approval_question = result.get("approval_request", "")

    return {
        "thread_id": thread_id,
        "user_id": user_id,
        "answer": answer,
        "requires_approval": requires_approval,
        "approval_request": approval_question,
        "flight_results": result.get("flight_results", ""),
        "hotel_results": result.get("hotel_results", ""),
        "weather_results": result.get("weather_results", ""),
        "maps_results": result.get("maps_results", ""),
        "itinerary": (
            interrupt_payload.get("draft_itinerary", "")
            if interrupt_payload
            else result.get("itinerary", "")
        ),
        "approved": result.get("approved"),
        "human_feedback": result.get("human_feedback", ""),
        "final_response": result.get("final_response", ""),
        "llm_calls": result.get("llm_calls", 0),
        "guardrail_allowed": result.get("guardrail_allowed", True),
        "guardrail_reason": result.get("guardrail_reason", ""),
    }


@log_execution
def run_travel_agent(user_input: str, thread_id: str | None = None, user_id: str | None = None) -> dict:
    """
    Main function to run the full travel planner agent workflow.
    Starts execution and pauses if human approval is required.

    Parameters:
        user_input (str): The travel query provided by the user.
        thread_id (str, optional): A unique ID for session persistence.
        user_id (str, optional): User ID for long-term profile persistence.

    Returns:
        dict: Final answer or draft itinerary with approval request.
    """
    if not thread_id:
        thread_id = f"user_{uuid.uuid4().hex}"

    if not user_id:
        user_id = "default_user"

    logger.info(f"Initializing Workflow | Thread: {thread_id} | User: {user_id}  | Query: '{user_input}'")

    config = {
        "configurable": {
            "thread_id": thread_id, # Checkpointer - current session (short term)
            "user_id": user_id,      # Store - permanent user profile (long term)
        }
    }

    # Check if this thread has prior state in the Postgres checkpointer
    checkpoint_state = travel_graph.get_state(config)
    is_existing = bool(checkpoint_state and checkpoint_state.values)

    if is_existing:
        initial_input = {
            "messages": [HumanMessage(content=user_input)],
            "user_query": user_input,
        }
    else:
        initial_input = {
            "messages": [HumanMessage(content=user_input)],
            "user_query": user_input,
            "flight_results": "",
            "hotel_results": "",
            "weather_results": "",
            "maps_results": "",
            "itinerary": "",
            "approval_request": "",
            "approved": False,
            "human_feedback": "",
            "final_response": "",
            "llm_calls": 0,
            "guardrail_allowed": True,
            "guardrail_reason": "",
        }

    # Invoke the graph with the initial state dictionary
    result = travel_graph.invoke(initial_input, config=config)

    logger.info(f"Workflow reached checkpoint | Thread: {thread_id} | Total LLM calls: {result.get('llm_calls', 0)}")
    return _serialize_workflow_result(result, thread_id, user_id)


@log_execution
def resume_travel_agent(
    thread_id: str,
    approved: bool,
    feedback: str = "",
    user_id: str | None = None,
) -> dict:
    """
    Resumes the paused LangGraph workflow after human review.

    Parameters:
        thread_id (str): The session ID of the paused workflow.
        approved (bool): True if user approves draft itinerary, False if changes requested.
        feedback (str): Optional feedback or requested changes.
        user_id (str, optional): User ID for long-term profile persistence.

    Returns:
        dict: Final polished travel response.
    """
    if not thread_id:
        raise ValueError("thread_id is required to resume a travel plan.")

    if not user_id:
        user_id = "default_user"

    logger.info(f"Resuming Workflow | Thread: {thread_id} | Approved: {approved} | Feedback: '{feedback}'")

    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": user_id,
        }
    }

    # Resume graph execution using Command(resume=...)
    result = travel_graph.invoke(
        Command(
            resume={
                "approved": approved,
                "feedback": feedback.strip(),
            }
        ),
        config=config,
    )

    logger.info(f"Workflow resumed & completed | Thread: {thread_id}")
    return _serialize_workflow_result(result, thread_id, user_id)


__all__ = ["graph", "travel_graph", "run_travel_agent", "resume_travel_agent"]