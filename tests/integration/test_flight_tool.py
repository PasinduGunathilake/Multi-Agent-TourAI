import sys
import io

# Ensure UTF-8 output in Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from Multi_Agent_TourAI.tools.flight_tool import flight_search


def test_flight_search_structured():
    """Integration test for flight_search with destination parameter."""
    result = flight_search(destination="Dubai", limit=2)
    assert isinstance(result, str)
    assert len(result) > 0
    print("✓ [Integration] flight_search_structured passed")


def test_flight_search_natural_query():
    """Integration test for flight_search with natural language query."""
    result = flight_search(query="Plan a 7 days Japan trip from SriLanka", limit=2)
    assert isinstance(result, str)
    assert len(result) > 0
    print("✓ [Integration] flight_search_natural_query passed")


if __name__ == "__main__":
    print("=" * 60)
    print("Running Integration Tests: flight_tool")
    print("=" * 60)
    test_flight_search_structured()
    test_flight_search_natural_query()
    print("=" * 60)
    print("All flight_tool integration tests passed successfully!")
    print("=" * 60)
