import sys
import io

# Ensure UTF-8 output in Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from Multi_Agent_TourAI.tools.flight_tool import format_flight


def test_format_flight_complete():
    """Unit test for formatting flight dictionary into markdown text."""
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
    print("✓ [Unit] format_flight_complete passed")


def test_format_flight_partial_data():
    """Unit test for null-safety when flight dictionary has missing fields."""
    partial_flight = {
        "flight_status": None,
        "airline": None,
        "flight": None,
        "departure": None,
        "arrival": None,
    }

    formatted = format_flight(partial_flight)

    assert "Airline: Unknown airline" in formatted
    assert "Flight: Unknown flight number" in formatted
    assert "Status: Scheduled" in formatted
    assert "Airport: Unknown departure airport" in formatted
    assert "Airport: Unknown arrival airport" in formatted
    print("✓ [Unit] format_flight_partial_data passed")


if __name__ == "__main__":
    print("=" * 60)
    print("Running Unit Tests: flight_formatter")
    print("=" * 60)
    test_format_flight_complete()
    test_format_flight_partial_data()
    print("=" * 60)
    print("All flight_formatter unit tests passed successfully!")
    print("=" * 60)
