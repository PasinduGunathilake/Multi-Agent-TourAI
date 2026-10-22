import sys
from Multi_Agent_TourAI.graph.workflow import run_travel_agent, resume_travel_agent, travel_graph
from Multi_Agent_TourAI.utils import logger

# Windows console UTF-8 fix for emojis and special characters
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

__all__ = ["run_travel_agent", "resume_travel_agent", "travel_graph"]

if __name__ == "__main__":
    test_query = input("Enter the test query: ")
    logger.info(f"====> Starting Travel Agent Test with query: '{test_query}'")

    # 1. First Pass: Starts workflow and pauses at Human Approval (if itinerary generated)
    response = run_travel_agent(test_query)
    thread_id = response["thread_id"]

    print("\n" + "=" * 80)
    print(response["answer"])
    print("=" * 80 + "\n")

    # 2. Check if Human-in-the-Loop Approval is required
    if response.get("requires_approval"):
        print("\n")
        print(f"HUMAN APPROVAL REQUIRED: {response.get('approval_request', 'Do you approve this draft itinerary?')}")
        print("\n")

        user_choice = input("\nDo you approve this draft itinerary? (y/n): ").strip().lower()
        if user_choice in ["y", "yes"]:
            approved = True
            feedback = ""
        else:
            approved = False
            feedback = input("Please enter your revision feedback / requested changes: ").strip()

        # 3. Second Pass: Resumes workflow from PostgreSQL checkpoint
        logger.info(f"====> Resuming Workflow with Approved={approved}, Feedback='{feedback}'")
        final_response = resume_travel_agent(
            thread_id=thread_id,
            approved=approved,
            feedback=feedback,
        )

        print("\n" + "=" * 80)
        print("FINAL POLISHED RESPONSE:")
        print("=" * 80)
        print(final_response["answer"])
        print("=" * 80 + "\n")
        logger.info(f"====> Test Finished. Total LLM calls made: {final_response.get('llm_calls', 0)}")
    else:
        # For follow-ups or single queries that don't need approval
        logger.info(f"====> Test Finished. Total LLM calls made: {response.get('llm_calls', 0)}")