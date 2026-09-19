import sys
import io

# Ensure UTF-8 output in Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from Multi_Agent_TourAI.utils.flight_utils import (
    clean_text,
    country_to_code,
    get_best_airport_for_country,
    resolve_location_to_iata,
    find_location_mentions,
    parse_route,
    DEFAULT_ORIGIN_IATA,
)


def test_clean_text():
    """Unit test for text cleaning, stop words removal, and punctuation stripping."""
    assert clean_text("Flights to Dubai, under $500!") == "dubai 500"
    assert clean_text("Trip from Sri Lanka to Japan!!!") == "sri lanka japan"
    assert clean_text("") == ""
    assert clean_text(None) == ""
    print("✓ [Unit] clean_text passed")


def test_country_to_code():
    """Unit test for ISO alpha-2 country code resolution and caching."""
    assert country_to_code("Sri Lanka") == "LK"
    assert country_to_code("srilanka") == "LK"
    assert country_to_code("Japan") == "JP"
    assert country_to_code("United Arab Emirates") == "AE"
    assert country_to_code("InvalidCountry999") is None
    print("✓ [Unit] country_to_code passed")


def test_get_best_airport_for_country():
    """Unit test for heuristic scoring and country best airport selection."""
    assert get_best_airport_for_country("LK") == "CMB"
    assert get_best_airport_for_country("JP") == "HND"
    assert get_best_airport_for_country("AE") == "DXB"
    print("✓ [Unit] get_best_airport_for_country passed")


def test_resolve_location_to_iata():
    """Unit test for 4-tier cascading IATA resolution."""
    assert resolve_location_to_iata("CMB") == "CMB"
    assert resolve_location_to_iata("dxb") == "DXB"
    assert resolve_location_to_iata("Tokyo") == "HND"
    assert resolve_location_to_iata("Colombo") == "CMB"
    assert resolve_location_to_iata("Japan") == "HND"
    assert resolve_location_to_iata("Sri Lanka") == "CMB"
    assert resolve_location_to_iata("FakeCityX") is None
    print("✓ [Unit] resolve_location_to_iata passed")


def test_find_location_mentions():
    """Unit test for entity location discovery and positional sorting."""
    query = "Plan a holiday from Sri Lanka to Japan including Tokyo"
    mentions = find_location_mentions(query)
    assert len(mentions) >= 2
    assert "sri lanka" in mentions or "srilanka" in mentions
    assert "japan" in mentions
    print("✓ [Unit] find_location_mentions passed")


def test_parse_route_patterns():
    """Unit test for NLP rule-based route extraction."""
    assert parse_route("all country flight info") == (None, None)
    assert parse_route("CMB to DXB") == ("CMB", "DXB")
    assert parse_route("CMB -> DXB") == ("CMB", "DXB")
    assert parse_route("flights from Sri Lanka to Japan for 7 days") == ("CMB", "HND")
    assert parse_route("Plan a trip to Dubai from Colombo") == ("CMB", "DXB")
    assert parse_route("Colombo to London") == ("CMB", "LHR")
    assert parse_route("Plan a 7 days Japan trip") == (DEFAULT_ORIGIN_IATA, "HND")
    print("✓ [Unit] parse_route_patterns passed")


if __name__ == "__main__":
    print("=" * 60)
    print("Running Unit Tests: flight_utils")
    print("=" * 60)
    test_clean_text()
    test_country_to_code()
    test_get_best_airport_for_country()
    test_resolve_location_to_iata()
    test_find_location_mentions()
    test_parse_route_patterns()
    print("=" * 60)
    print("All flight_utils unit tests passed successfully!")
    print("=" * 60)
