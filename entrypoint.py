from Multi_Agent_TourAI.graph.workflow import run_travel_agent, travel_graph
from Multi_Agent_TourAI.utils import logger

__all__ = ["run_travel_agent", "travel_graph"]

if __name__ == "__main__":
    test_query = "Plan a 5 days trip to Dubai from Sri Lanka"
    logger.info(f"====> Starting Travel Agent Test with query: '{test_query}'")
    response = run_travel_agent(test_query)
    print("=" * 80)
    print(response["answer"])
    print("=" * 80)
    logger.info(f"====> Test Finished. Total LLM calls made: {response['llm_calls']}")