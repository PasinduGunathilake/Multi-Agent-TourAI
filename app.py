import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from Multi_Agent_TourAI.graph.workflow import run_travel_agent
from Multi_Agent_TourAI.utils import get_logger
# nested event loops for async call in fast api
import nest_asyncio
nest_asyncio.apply()

logger = get_logger("Multi_Agent_TourAI.api")

# fastapi app
app = FastAPI(
    title = "Multi_Agent_TourAI API",
    description= "Backend API for LangGraph Travel Planner",
    version="3.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)

# Request , Response data models
class TravelRequest(BaseModel):
    query: str = Field(..., example="Plan a 5 days trip to Dubai from Sri Lanka")
    thread_id: str | None = Field(default=None, example="user_session_123")

class TravelResponse(BaseModel):
    thread_id: str
    answer: str
    flight_results: str
    hotel_results: str
    weather_results: str | None = ""
    itinerary: str
    llm_calls: int 


# API endpoints
@app.get("/health")
async def health_check():
    return {"status": "healthy", "services": "Multi_Agent_TourAI"}

@app.post("/api/plan", response_model=TravelResponse)
async def plan(payload: TravelRequest):
    user_query = payload.query.strip()

    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    logger.info(f"Incoming Travel Request: '{user_query}' | Thread: {payload.thread_id}")

    try:
        # run Multi-Agent Workflow
        result = run_travel_agent(user_input=user_query, thread_id=payload.thread_id)
        logger.info(f"Travel Plan Ready | Total LLM Calls: {result['llm_calls']}")
        return result
    except Exception as e:
        logger.error(f"Error executing Multi-Agent workflow: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Real-time Server-Sent Events (SSE) Streaming Endpoint
import json
import uuid
import asyncio
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from Multi_Agent_TourAI.graph.workflow import travel_graph

@app.post("/api/plan/stream")
async def plan_stream(payload: TravelRequest):
    user_query = payload.query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    thread_id = payload.thread_id or f"user_{uuid.uuid4().hex}"
    user_id = "default_user"
    logger.info(f"Incoming Real-time Streaming Request: '{user_query}' | Thread: {thread_id}")

    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": user_id,
        }
    }

    initial_state = {
        "messages": [HumanMessage(content=user_query)],
        "user_query": user_query,
        "flight_results": "",
        "hotel_results": "",
        "weather_results": "",
        "itinerary": "",
        "llm_calls": 0,
    }

    async def event_generator():
        accumulated_state = dict(initial_state)

        # 1. Yield initial Fan-Out trigger event
        yield f"data: {json.dumps({'event': 'fan_out_start', 'message': 'Dispatched parallel Flight, Hotel & Weather MCP agents'})}\n\n"
        await asyncio.sleep(0.01)

        try:
            # Stream updates from the LangGraph execution graph
            for update in travel_graph.stream(initial_state, config=config, stream_mode="updates"):
                for node_name, node_output in update.items():
                    accumulated_state.update(node_output)

                    # Extract node payload
                    node_payload = {
                        "event": "node_complete",
                        "node": node_name,
                        "flight_results": accumulated_state.get("flight_results", ""),
                        "hotel_results": accumulated_state.get("hotel_results", ""),
                        "weather_results": accumulated_state.get("weather_results", ""),
                        "itinerary": accumulated_state.get("itinerary", ""),
                        "llm_calls": accumulated_state.get("llm_calls", 0),
                    }

                    if node_name == "final_agent":
                        messages = node_output.get("messages", [])
                        if messages:
                            final_text = messages[-1].content
                            # Notify node_complete without dumping full text at once
                            yield f"data: {json.dumps({'event': 'node_complete', 'node': 'final_agent', 'llm_calls': accumulated_state.get('llm_calls', 0)})}\n\n"
                            
                            # Stream tokens word-by-word with realistic typewriter timing (~60 words/sec)
                            import re
                            tokens = re.findall(r'\S+|\s+', final_text)
                            for token in tokens:
                                yield f"data: {json.dumps({'event': 'token', 'token': token})}\n\n"
                                await asyncio.sleep(0.015)
                    else:
                        yield f"data: {json.dumps(node_payload)}\n\n"
                        await asyncio.sleep(0.02)

            # Final complete event
            messages = accumulated_state.get("messages", [])
            final_answer = messages[-1].content if messages else ""

            complete_payload = {
                "event": "complete",
                "thread_id": thread_id,
                "answer": final_answer,
                "flight_results": accumulated_state.get("flight_results", ""),
                "hotel_results": accumulated_state.get("hotel_results", ""),
                "weather_results": accumulated_state.get("weather_results", ""),
                "itinerary": accumulated_state.get("itinerary", ""),
                "llm_calls": accumulated_state.get("llm_calls", 0),
            }
            yield f"data: {json.dumps(complete_payload)}\n\n"

        except Exception as e:
            logger.error(f"Error in streaming Multi-Agent workflow: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )



# Direct Runner (python app.py)
if __name__ == "__main__":
    logger.info("Starting FastAPI server at http://127.0.0.1:8000")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)