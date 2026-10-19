import sys
from Multi_Agent_TourAI.graph.workflow import run_travel_agent, travel_graph
from Multi_Agent_TourAI.utils import logger

# Windows console UTF-8 fix for emojis and special characters
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

__all__ = ["run_travel_agent", "travel_graph"]

if __name__ == "__main__":
    test_query = input("Enter the test query: ")
    logger.info(f"====> Starting Travel Agent Test with query: '{test_query}'")
    response = run_travel_agent(test_query)
    print("=" * 80)
    print(response["answer"])
    print("=" * 80)
    logger.info(f"====> Test Finished. Total LLM calls made: {response['llm_calls']}")