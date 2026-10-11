from langchain_core.messages import SystemMessage, HumanMessage
import asyncio
from langchain_core.messages import AIMessage
from Multi_Agent_TourAI.graph.state import TravelState
#from Multi_Agent_TourAI.tools.flight_tool import flight_search # uncomment when using custom implement search tool via aviationstack_api
from Multi_Agent_TourAI.mcp.aviationstack_mcp import aviationstack_mcp_search
from Multi_Agent_TourAI.llms.llm import llm
from Multi_Agent_TourAI.config.prompts import (FLIGHT_SYSTEM_PROMPT,FLIGHT_PROMPT_TEMPLATE,)
from Multi_Agent_TourAI.utils import get_logger, log_execution

logger = get_logger(__name__)

# Use without mcp
'''
@log_execution
def flight_agent(state: TravelState):
    query = state["user_query"]

    logger.info(f"Searching flights for query: '{query}'")
    flight_data = flight_search(query=query)

    return {
        "flight_results": flight_data,
        "messages": [AIMessage(content="Flight result fetched.")],
        "llm_calls": state.get("llm_calls", 0)+1
    }
    '''

# mcp - llm based flight agent
@log_execution
def flight_agent(state: TravelState):
    user_query = state["user_query"]

    try:

        airports = asyncio.run(
            aviationstack_mcp_search("list_airports")
        )

        airlines = asyncio.run(
            aviationstack_mcp_search("list_airlines")
        )

        routes = asyncio.run(
            aviationstack_mcp_search("list_routes")
        )

        shedules = asyncio.run(
            aviationstack_mcp_search("future_flights_arrival_departure_schedule")
        )

        taxes = asyncio.run(
            aviationstack_mcp_search("list_taxes")
        )

        prompt = FLIGHT_PROMPT_TEMPLATE.format(
            user_query=user_query,
            list_airports=str(airports)[:3000],
            list_airlines=str(airlines)[:3000],
            list_routes=str(routes)[:3000],
            future_flights_arrival_departure_schedule=str(shedules)[:3000],
            list_taxes=str(taxes)[:3000],
        )

        response = llm.invoke([
            SystemMessage(content=FLIGHT_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])

        flight_data = response.content
    except Exception as e:
        flight_data = f"Flight information unavailable: {str(e)}"

    return {
        "flight_results": flight_data,
        "messages": [AIMessage(content="Flight result fetched.")],
        "llm_calls": state.get("llm_calls", 0)+1
    }

