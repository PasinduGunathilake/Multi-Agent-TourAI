from langgraph.types import Command, interrupt #components for HITL
from langchain_core.messages import AIMessage
from Multi_Agent_TourAI.graph.state import TravelState
from Multi_Agent_TourAI.utils.logger import get_logger, log_execution

logger = get_logger(__name__)

# HITL approval (Human_in_the_Loop)
@log_execution
def human_approval_agent(state: TravelState):
    logger.info("Human Approval: Pausing workflow to await human review...")

    # Do not wrap interrupt() in try/except. LangGraph uses it to pause execution
    review = interrupt(
        {
            "question": "Do you approve this itinerary?",
            "draft_itinerary": state.get("itinerary", ""),
            "approval_request": state.get("approval_request", ""),
            "selected_agents": state.get("selected_agents", []),
            "supervisor_reasoning": state.get("supervisor_reasoning", ""),
            "expected_response": {
                "approved": True,
                "feedback": "Optional revision feedback",
            },
        }
    )

    approved = bool(review.get("approved", False))
    human_feedback = str(review.get("feedback", "")).strip()

    logger.info(f"Human Approval: Resumed from review | Approved={approved} | Feedback='{human_feedback}'")

    return {
        "approved": approved,
        "human_feedback": human_feedback,
        "messages": [AIMessage(content="Human approval step completed.")],
    }


__all__ = ["human_approval_agent"]
