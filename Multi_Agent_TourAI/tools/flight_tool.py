import os
from typing import Optional, Dict, Any
import certifi
import requests
import urllib3.util.connection as urllib_connection
from dotenv import load_dotenv
from Multi_Agent_TourAI.utils.flight_utils import (parse_route, resolve_to_iata, DEFAULT_ORIGIN_IATA,)
from Multi_Agent_TourAI.utils import get_logger

logger = get_logger(__name__)

# Avoid Windows IPv6 TCP connection timeout delay
urllib_connection.HAS_IPV6 = False

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

api_key = os.getenv("AVIATIONSTACK_API_KEY", "")
BASE_URL = "http://api.aviationstack.com/v1/flights"


def format_flight(flight: Dict[str, Any]) -> str:
    """Formats a flight dictionary into readable markdown text."""
    airline = flight.get("airline", {}).get("name") or "Unknown airline"
    flight_number = flight.get("flight", {}).get("iata") or "Unknown flight number"
    status = (flight.get("flight_status") or "Scheduled").capitalize()

    dep = flight.get("departure", {}) or {}
    arr = flight.get("arrival", {}) or {}

    dep_airport = dep.get("airport") or "Unknown departure airport"
    dep_iata = dep.get("iata") or "Unknown"
    dep_terminal = dep.get("terminal") or "N/A"
    dep_gate = dep.get("gate") or "N/A"
    dep_scheduled = dep.get("scheduled") or "Unknown"
    dep_delay = dep.get("delay")
    dep_delay_text = f"{dep_delay} minutes" if dep_delay is not None else "N/A"

    arr_airport = arr.get("airport") or "Unknown arrival airport"
    arr_iata = arr.get("iata") or "Unknown"
    arr_terminal = arr.get("terminal") or "N/A"
    arr_gate = arr.get("gate") or "N/A"
    arr_scheduled = arr.get("scheduled") or "Unknown"
    arr_delay = arr.get("delay")
    arr_delay_text = f"{arr_delay} minutes" if arr_delay is not None else "N/A"

    return f"""
Airline: {airline}
Flight: {flight_number}
Status: {status}

Departure:
- Airport: {dep_airport}
- IATA: {dep_iata}
- Terminal: {dep_terminal}
- Gate: {dep_gate}
- Scheduled: {dep_scheduled}
- Delay: {dep_delay_text}

Arrival:
- Airport: {arr_airport}
- IATA: {arr_iata}
- Terminal: {arr_terminal}
- Gate: {arr_gate}
- Scheduled: {arr_scheduled}
- Delay: {arr_delay_text}
""".strip()


def flight_search(
    destination: Optional[str] = None,
    origin: Optional[str] = None,
    date: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 5,
) -> str:
    """
    Search for flights using structured parameters (destination, origin, date)
    or a natural language query string.

    Args:
        destination: Destination city, country, or 3-letter IATA code (e.g. 'Japan', 'London', 'DXB').
        origin: Origin city, country, or 3-letter IATA code (defaults to DEFAULT_ORIGIN_IATA, e.g. 'CMB').
        date: Optional flight date in YYYY-MM-DD format.
        query: Natural language query (e.g. 'flights to Japan from SriLanka' or 'all country flight info').
        limit: Maximum number of flights to return (default 5).

    Returns:
        Formatted string containing flight status options or informative message.
    """
    if not api_key:
        return (
            "Flight search unavailable: AVIATIONSTACK_API_KEY is not configured.\n"
            "Please add this in your .env file:\n"
            "AVIATIONSTACK_API_KEY=your_api_key_here"
        )

    dep_iata = None
    arr_iata = None

    # Case 1: Natural language query provided without explicit destination
    if query and not destination:
        dep_iata, arr_iata = parse_route(query)
        if origin:
            dep_iata = resolve_to_iata(origin) or dep_iata
    # Case 2: Structured search (destination provided)
    else:
        if destination:
            arr_iata = resolve_to_iata(destination)
            if not arr_iata:
                return f"Could not determine airport code for destination: '{destination}'. Please specify a major city, country, or 3-letter IATA airport code."

        dep_iata = resolve_to_iata(origin) if origin else (DEFAULT_ORIGIN_IATA if arr_iata else None)

    params = {
        "access_key": api_key,
        "limit": min(limit, 100),
    }

    if dep_iata:
        params["dep_iata"] = dep_iata
    if arr_iata:
        params["arr_iata"] = arr_iata
    if date:
        params["flight_date"] = date.strip()

    try:
        logger.info(f"AviationStack API Request: Dep={dep_iata} -> Arr={arr_iata} | Date={date}")
        response = requests.get(BASE_URL, params=params, timeout=25)
        response.raise_for_status()
        data = response.json()
        flight_data = data.get("data", [])
        logger.info(f"AviationStack API Response: Found {len(flight_data)} flights.")
    except requests.exceptions.Timeout:
        route_str = f" for route {dep_iata} -> {arr_iata}" if (dep_iata or arr_iata) else ""
        return f"Flight search timed out connecting to AviationStack{route_str}."
    except requests.exceptions.RequestException as e:
        return f"Flight search network error: {e}"
    except (ValueError, KeyError) as e:
        return f"Flight search data parsing error: {e}"
    except Exception as e:
        return f"An unexpected error occurred during flight search: {e}"

    if "error" in data:
        error = data["error"]
        return (
            "Flight API error:\n"
            f"Code: {error.get('code', 'Unknown')}\n"
            f"Message: {error.get('message', 'Unknown error')}"
        )

    flight_data = data.get("data", [])

    if not flight_data:
        route_text = ""
        if dep_iata and arr_iata:
            route_text = f" for route {dep_iata} -> {arr_iata}"
        elif dep_iata:
            route_text = f" from {dep_iata}"
        elif arr_iata:
            route_text = f" to {arr_iata}"

        date_text = f" on {date}" if date else ""
        return (
            f"No live flight data found{route_text}{date_text}.\n\n"
            "Note: AviationStack provides live/scheduled flight data, not ticket prices. "
            "For actual fare prices, use a flight-pricing API such as Amadeus."
        )

    if dep_iata and arr_iata:
        route_info = f"### Available Flights ({dep_iata} -> {arr_iata})"
    elif dep_iata:
        route_info = f"### Live Flights from {dep_iata}"
    elif arr_iata:
        route_info = f"### Live Flights to {arr_iata}"
    else:
        route_info = "### Global Live Flights"

    formatted_flights = [format_flight(flight) for flight in flight_data[:limit]]
    return f"{route_info}\n\n" + "\n\n---\n\n".join(formatted_flights)


if __name__ == "__main__":
    print(flight_search(query="Plan a 7 days Japan trip from SriLanka"))
    print("\n" + "=" * 80 + "\n")
    print(flight_search(destination="Dubai"))
    print("\n" + "=" * 80 + "\n")
    print(flight_search(query="all country flight info"))