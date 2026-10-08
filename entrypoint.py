from Multi_Agent_TourAI.graph.workflow import run_travel_agent, travel_graph

__all__ = ["run_travel_agent", "travel_graph"]

if __name__ == "__main__":
    test_query = "Plan a 5 days trip to Dubai from Sri Lanka"
    print(f"Testing Travel Agent with query: '{test_query}'...\n")
    response = run_travel_agent(test_query)
    print("=" * 80)
    print(response["answer"])
    print("=" * 80)
    print(f"Total LLM calls: {response['llm_calls']}")