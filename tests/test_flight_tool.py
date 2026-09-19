import sys
import io

# Ensure UTF-8 output in Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from Multi_Agent_TourAI.tools.flight_tool import format_flight, flight_search


def test_format_flight():
    """Test flight dictionary parsing and markdown output generation."""
    sample_flight = {
        "flight_status": "scheduled",
        "airline": {"name": "SriLankan Airlines"},
        "flight": {"iata": "UL302"},
        "departure": {
            "airport": "Bandaranaike International",
            "iata": "CMB",
            "terminal": "1",
            "gate": "A4",
            "scheduled": "2026-09-20T08:00:00+00:00",
            "delay": 15,
        },
        "arrival": {
            "airport": "Singapore Changi",
            "iata": "SIN",
            "terminal": "3",
            "gate": "B2",
            "scheduled": "2026-09-20T14:30:00+00:00",
            "delay": None,
        },
    }

    formatted = format_flight(sample_flight)

    assert "Airline: SriLankan Airlines" in formatted
    assert "Flight: UL302" in formatted
    assert "Status: Scheduled" in formatted
    assert "Airport: Bandaranaike International" in formatted
    assert "IATA: CMB" in formatted
    assert "Delay: 15 minutes" in formatted
    assert "IATA: SIN" in formatted
    assert "Delay: N/A" in formatted
    print("✓ test_format_flight passed")


def test_flight_search_structure():
    """Test flight_search execution with destination parameter."""
    result = flight_search(destination="Dubai", limit=2)
    assert isinstance(result, str)
    assert len(result) > 0
    print("✓ test_flight_search_structure passed")


def test_flight_search_query():
    """Test flight_search execution with natural language query."""
    result = flight_search(query="Plan a 7 days Japan trip from SriLanka", limit=2)
    assert isinstance(result, str)
    assert len(result) > 0
    print("✓ test_flight_search_query passed")


if __name__ == "__main__":
    print("=" * 60)
    print("Running tests for flight_tool.py")
    print("=" * 60)
    test_format_flight()
    test_flight_search_structure()
    test_flight_search_query()
    print("=" * 60)
    print("All flight_tool tests passed successfully!")
    print("=" * 60)
