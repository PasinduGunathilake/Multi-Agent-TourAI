import json
import uuid
import asyncio
import uvicorn
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from Multi_Agent_TourAI.graph.workflow import travel_graph
from langgraph.types import Command
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from Multi_Agent_TourAI.graph.workflow import run_travel_agent, resume_travel_agent
from Multi_Agent_TourAI.utils import get_logger
# nested event loops for async call in fast api
import nest_asyncio
nest_asyncio.apply()

logger = get_logger("Multi_Agent_TourAI.api")

# fastapi app
app = FastAPI(
    title = "Multi_Agent_TourAI API",
    description= "Backend API for LangGraph Travel Planner with Human-in-the-Loop",
    version="2.0.0",
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

class ResumeRequest(BaseModel):
    thread_id: str = Field(..., example="user_session_123")
    approved: bool = Field(..., example=True)
    feedback: str = Field(default="", example="Please add more budget-friendly hotel options.")

class TravelResponse(BaseModel):
    thread_id: str
    answer: str
    requires_approval: bool = False
    approval_request: str | None = ""
    flight_results: str | None = ""
    hotel_results: str | None = ""
    weather_results: str | None = ""
    itinerary: str | None = ""
    approved: bool | None = None
    human_feedback: str | None = ""
    llm_calls: int = 0


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
        logger.info(f"Travel Plan Ready | Requires Approval: {result.get('requires_approval', False)} | Total LLM Calls: {result.get('llm_calls', 0)}")
        return result
    except Exception as e:
        logger.error(f"Error executing Multi-Agent workflow: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/plan/resume", response_model=TravelResponse)
async def resume(payload: ResumeRequest):
    if not payload.thread_id:
        raise HTTPException(status_code=400, detail="thread_id is required to resume workflow.")

    logger.info(f"Incoming Resume Request: Thread={payload.thread_id} | Approved={payload.approved} | Feedback='{payload.feedback}'")
    try:
        result = resume_travel_agent(
            thread_id=payload.thread_id,
            approved=payload.approved,
            feedback=payload.feedback,
        )
        logger.info(f"Workflow Resumed | Total LLM Calls: {result.get('llm_calls', 0)}")
        return result
    except Exception as e:
        logger.error(f"Error resuming workflow: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Real-time Server-Sent Events (SSE) Streaming Endpoint
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

    # Check if this thread has prior state in the Postgres checkpointer
    checkpoint_state = travel_graph.get_state(config)
    is_existing_session = bool(checkpoint_state and checkpoint_state.values)

    if is_existing_session:
        # Existing session: pass only the new user message so prior memory is preserved
        initial_state = {
            "messages": [HumanMessage(content=user_query)],
            "user_query": user_query,
        }
    else:
        # Brand new session: initialize empty defaults
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
        if is_existing_session and checkpoint_state:
            accumulated_state = dict(checkpoint_state.values)
            accumulated_state.update(initial_state)
        else:
            accumulated_state = dict(initial_state)

        try:
            # Stream updates from the LangGraph execution graph
            for update in travel_graph.stream(initial_state, config=config, stream_mode="updates"):
                for node_name, node_output in update.items():
                    # Catch LangGraph HITL interrupt event immediately
                    if node_name == "__interrupt__":
                        interrupt_items = node_output if isinstance(node_output, (list, tuple)) else [node_output]
                        first_interrupt = interrupt_items[0] if interrupt_items else None
                        interrupt_val = getattr(first_interrupt, "value", first_interrupt) if first_interrupt else {}
                        payload_val = interrupt_val if isinstance(interrupt_val, dict) else {"question": str(interrupt_val)}

                        logger.info(f"Workflow paused at HITL interrupt | Thread: {thread_id}")
                        approval_payload = {
                            "event": "approval_required",
                            "thread_id": thread_id,
                            "question": payload_val.get("question", "Do you approve this draft itinerary?"),
                            "draft_itinerary": payload_val.get("draft_itinerary") or accumulated_state.get("itinerary", ""),
                            "flight_results": accumulated_state.get("flight_results", ""),
                            "hotel_results": accumulated_state.get("hotel_results", ""),
                            "weather_results": accumulated_state.get("weather_results", ""),
                            "llm_calls": accumulated_state.get("llm_calls", 0),
                        }
                        yield f"data: {json.dumps(approval_payload)}\n\n"
                        return

                    if isinstance(node_output, dict):
                        accumulated_state.update(node_output)

                    # Trigger UI fan_out indicator only when specialist tool agents are actually scheduled
                    if node_name == "supervisor" and accumulated_state.get("intent") != "follow_up":
                        yield f"data: {json.dumps({'event': 'fan_out_start', 'message': 'Dispatched specialist MCP agents'})}\n\n"
                        await asyncio.sleep(0.01)

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
                            raw_content = messages[-1].content
                            if isinstance(raw_content, list):
                                # Handle list of text/dict blocks
                                final_text = "".join(
                                    part if isinstance(part, str) else part.get("text", str(part))
                                    for part in raw_content
                                )
                            else:
                                final_text = str(raw_content or "")

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

            # Check if execution paused on Human-in-the-Loop (HITL) interrupt
            post_stream_state = travel_graph.get_state(config)
            if post_stream_state.tasks and any(t.interrupts for t in post_stream_state.tasks):
                interrupt_item = post_stream_state.tasks[0].interrupts[0]
                interrupt_val = getattr(interrupt_item, "value", interrupt_item)
                payload_val = interrupt_val if isinstance(interrupt_val, dict) else {"question": str(interrupt_val)}

                logger.info(f"Workflow paused for Human-in-the-Loop approval | Thread: {thread_id}")
                approval_payload = {
                    "event": "approval_required",
                    "thread_id": thread_id,
                    "question": payload_val.get("question", "Do you approve this draft itinerary?"),
                    "draft_itinerary": payload_val.get("draft_itinerary") or accumulated_state.get("itinerary", ""),
                    "flight_results": accumulated_state.get("flight_results", ""),
                    "hotel_results": accumulated_state.get("hotel_results", ""),
                    "weather_results": accumulated_state.get("weather_results", ""),
                    "llm_calls": accumulated_state.get("llm_calls", 0),
                }
                yield f"data: {json.dumps(approval_payload)}\n\n"
                return

            # Final complete event
            messages = accumulated_state.get("messages", [])
            if messages:
                raw_ans = messages[-1].content
                if isinstance(raw_ans, list):
                    final_answer = "".join(
                        part if isinstance(part, str) else part.get("text", str(part))
                        for part in raw_ans
                    )
                else:
                    final_answer = str(raw_ans or "")
            else:
                final_answer = ""

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


# Real-time Streaming Resume Endpoint (SSE)
@app.post("/api/plan/resume/stream")
async def resume_stream(payload: ResumeRequest):
    if not payload.thread_id:
        raise HTTPException(status_code=400, detail="thread_id is required.")

    thread_id = payload.thread_id
    user_id = "default_user"
    logger.info(f"Incoming Streaming Resume: Thread={thread_id} | Approved={payload.approved} | Feedback='{payload.feedback}'")

    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": user_id,
        }
    }

    async def event_generator():
        try:
            resume_command = Command(
                resume={
                    "approved": payload.approved,
                    "feedback": payload.feedback.strip(),
                }
            )

            accumulated_state = {}
            prior_state = travel_graph.get_state(config)
            if prior_state and prior_state.values:
                accumulated_state = dict(prior_state.values)

            for update in travel_graph.stream(resume_command, config=config, stream_mode="updates"):
                for node_name, node_output in update.items():
                    if isinstance(node_output, dict):
                        accumulated_state.update(node_output)

                    if node_name == "final_agent":
                        messages = node_output.get("messages", [])
                        if messages:
                            raw_content = messages[-1].content
                            if isinstance(raw_content, list):
                                final_text = "".join(
                                    part if isinstance(part, str) else part.get("text", str(part))
                                    for part in raw_content
                                )
                            else:
                                final_text = str(raw_content or "")

                            yield f"data: {json.dumps({'event': 'node_complete', 'node': 'final_agent', 'llm_calls': accumulated_state.get('llm_calls', 0)})}\n\n"
                            
                            import re
                            tokens = re.findall(r'\S+|\s+', final_text)
                            for token in tokens:
                                yield f"data: {json.dumps({'event': 'token', 'token': token})}\n\n"
                                await asyncio.sleep(0.015)
                    else:
                        node_payload = {
                            "event": "node_complete",
                            "node": node_name,
                            "llm_calls": accumulated_state.get("llm_calls", 0),
                        }
                        yield f"data: {json.dumps(node_payload)}\n\n"
                        await asyncio.sleep(0.02)

            # Final complete event
            messages = accumulated_state.get("messages", [])
            final_answer = accumulated_state.get("final_response") or (messages[-1].content if messages else "")
            if isinstance(final_answer, list):
                final_answer = "".join(
                    part if isinstance(part, str) else part.get("text", str(part))
                    for part in final_answer
                )

            complete_payload = {
                "event": "complete",
                "thread_id": thread_id,
                "answer": str(final_answer),
                "flight_results": accumulated_state.get("flight_results", ""),
                "hotel_results": accumulated_state.get("hotel_results", ""),
                "weather_results": accumulated_state.get("weather_results", ""),
                "itinerary": accumulated_state.get("itinerary", ""),
                "llm_calls": accumulated_state.get("llm_calls", 0),
            }
            yield f"data: {json.dumps(complete_payload)}\n\n"

        except Exception as e:
            logger.error(f"Error in streaming resume workflow: {str(e)}", exc_info=True)
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