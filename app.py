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
    return {"status": "healthy", "services":"Multi_Agent_TourAI"}

@app.post("/api/plan", response_model=TravelResponse)
async def plan(payload:TravelRequest):
    user_query = payload.query.strip()

    if not user_query:
        raise HTTPException(status_code=400, detail= "Query can not be empty.")
    logger.info(f"Incoming Travel Request: '{user_query}' | Thread: {payload.thread_id}")

    try:
        # run Multi-Agent Workflow
        result = run_travel_agent(user_input=user_query, thread_id=payload.thread_id)
        logger.info(f"Travel Plan Ready | Total LLM Calls: {result['llm_calls']}")
        return result
    except Exception as e:
        logger.error(f"Error executing Multi-Agent workflow: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



# Direct Runner (python app.py)
if __name__ == "__main__":
    logger.info("Starting FastAPI server at http://127.0.0.1:8000")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)