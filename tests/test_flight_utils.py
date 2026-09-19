import sys
import io
import pytest

# Ensure UTF-8 output in Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from Multi_Agent_TourAI.utils.flight_utils import (
    clean_text,
    country_to_code,
    get_best_airport_for_country,
    resolve_location_to_iata,
    resolve_to_iata,
    find_location_mentions,
    parse_route,
    DEFAULT_ORIGIN_IATA,
)


def test_clean_text():
    """Test text cleaning, stop words removal, and punctuation stripping."""
    assert clean_text("Flights to Dubai, under $500!") == "dubai 500"
    assert clean_text("Trip from Sri Lanka to Japan!!!") == "sri lanka japan"
    assert clean_text("") == ""
    assert clean_text(None) == ""
    print("✓ test_clean_text passed")


def test_country_to_code():
    """Test country name and alias conversion to ISO alpha-2 codes."""
    assert country_to_code("Sri Lanka") == "LK"
    assert country_to_code("srilanka") == "LK"          # Alias without space
    assert country_to_code("Japan") == "JP"              # pycountry exact match
    assert country_to_code("United Arab Emirates") == "AE"
    assert country_to_code("UnknownCountry123") is None  # Invalid country fallback
    print("✓ test_country_to_code passed")


def test_get_best_airport_for_country():
    """Test heuristic scoring / preferred airport selection for countries."""
    assert get_best_airport_for_country("LK") == "CMB"
    assert get_best_airport_for_country("JP") == "HND"
    assert get_best_airport_for_country("AE") == "DXB"
    print("✓ test_get_best_airport_for_country passed")


def test_resolve_location_to_iata():
    """Test cascading resolution from city, country, or 3-letter IATA code."""
    assert resolve_location_to_iata("CMB") == "CMB"             # Direct IATA uppercase
    assert resolve_location_to_iata("dxb") == "DXB"             # Direct IATA lowercase
    assert resolve_location_to_iata("Tokyo") == "HND"           # City preferred match
    assert resolve_location_to_iata("Colombo") == "CMB"         # City match
    assert resolve_location_to_iata("Japan") == "HND"           # Country lookup
    assert resolve_location_to_iata("Sri Lanka") == "CMB"       # Country lookup
    assert resolve_location_to_iata("NonExistingCity") is None  # Invalid location
    print("✓ test_resolve_location_to_iata passed")


def test_find_location_mentions():
    """Test natural query entity mention detection while preserving position order."""
    query = "Plan a holiday from Sri Lanka to Japan including Tokyo"
    mentions = find_location_mentions(query)
    assert len(mentions) >= 2
    assert "sri lanka" in mentions or "srilanka" in mentions
    assert "japan" in mentions
    print("✓ test_find_location_mentions passed")


def test_parse_route_patterns():
    """Test NLP rule-based route parsing for various user query formulations."""
    # 1. Global / All-country queries
    assert parse_route("all country flight info") == (None, None)
    assert parse_route("global flights worldwide") == (None, None)

    # 2. Direct IATA arrow pattern
    assert parse_route("CMB to DXB") == ("CMB", "DXB")
    assert parse_route("CMB -> DXB") == ("CMB", "DXB")

    # 3. 'from X to Y' pattern
    assert parse_route("flights from Sri Lanka to Japan for 7 days") == ("CMB", "HND")

    # 4. 'to Y from X' pattern
    assert parse_route("Plan a trip to Dubai from Colombo") == ("CMB", "DXB")

    # 5. Route without 'from' ('X to Y')
    assert parse_route("Colombo to London") == ("CMB", "LHR")

    # 6. Single destination fallback (defaults departure to DEFAULT_ORIGIN_IATA)
    assert parse_route("Plan a 7 days Japan trip") == (DEFAULT_ORIGIN_IATA, "HND")
    print("✓ test_parse_route_patterns passed")


if __name__ == "__main__":
    print("=" * 60)
    print("Running tests for flight_utils.py")
    print("=" * 60)
    test_clean_text()
    test_country_to_code()
    test_get_best_airport_for_country()
    test_resolve_location_to_iata()
    test_find_location_mentions()
    test_parse_route_patterns()
    print("=" * 60)
    print("All flight_utils tests passed successfully!")
    print("=" * 60)
