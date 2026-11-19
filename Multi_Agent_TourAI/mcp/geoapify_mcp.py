import asyncio
import os
import json
from typing import Optional, Dict, Any, List, Union
import certifi
import requests
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from Multi_Agent_TourAI.utils import get_logger

# SSL certificate configuration for windows
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

load_dotenv()
logger = get_logger(__name__)

DEFAULT_TIMEOUT = 15.0


def redact_api_key(key: Optional[str]) -> str:
    """Masks an API key for safe logging, displaying only first 4 and last 4 characters."""
    if not key or not str(key).strip():
        return "[NOT SET]"
    key_str = str(key).strip()
    if len(key_str) <= 8:
        return "***"
    return f"{key_str[:4]}...{key_str[-4:]}"


def get_geoapify_api_key() -> str:
    """Validates and returns the configured Geoapify API key."""
    key = os.getenv("GEOAPIFY_API_KEY")
    if not key or not key.strip():
        raise ValueError(
            "GEOAPIFY_API_KEY is missing or empty. Please set GEOAPIFY_API_KEY in your environment."
        )
    return key.strip()


# Internal client & tool caches
_mcp_client: Optional[MultiServerMCPClient] = None
_geoapify_tools: Dict[str, Any] = {}
_init_lock: Optional[asyncio.Lock] = None


def _get_init_lock() -> asyncio.Lock:
    """Returns or creates an asyncio.Lock tied to the active event loop."""
    global _init_lock
    if _init_lock is None:
        _init_lock = asyncio.Lock()
    return _init_lock


def get_mcp_client() -> MultiServerMCPClient:
    """
    Initializes or returns the cached MultiServerMCPClient for Geoapify Remote MCP.
    Validates presence of API key and protects credentials from plain-text logging.
    """
    global _mcp_client
    if _mcp_client is not None:
        return _mcp_client

    api_key = get_geoapify_api_key()
    logger.info(f"Connecting to Geoapify Remote MCP Server (Key: {redact_api_key(api_key)})")

    _mcp_client = MultiServerMCPClient({
        "geoapify-remote-mcp": {
            "transport": "http",
            "url": f"https://api.geoapify.com/v1/mcp?apiKey={api_key}",
        }
    })
    return _mcp_client


def reset_geoapify_cache():
    """Resets internal client and tool caches (useful for testing and reconfiguration)."""
    global _mcp_client, _geoapify_tools, _init_lock
    _mcp_client = None
    _geoapify_tools = {}
    _init_lock = None


# Module-level client reference for backward compatibility
client = None


async def init_geoapify_tools() -> Dict[str, Any]:
    """
    Loads Geoapify MCP tools once and caches them in memory.
    Thread-safe and concurrency-safe via asyncio.Lock.
    """
    global _geoapify_tools
    if _geoapify_tools:
        return _geoapify_tools

    async with _get_init_lock():
        if _geoapify_tools:
            return _geoapify_tools

        try:
            mcp_client = get_mcp_client()
            tools = await asyncio.wait_for(mcp_client.get_tools(), timeout=DEFAULT_TIMEOUT)
            _geoapify_tools = {getattr(t, "name", f"tool_{i}"): t for i, t in enumerate(tools)}
            logger.info(f"Loaded {len(_geoapify_tools)} tools from Geoapify Remote MCP server.")
        except Exception as e:
            logger.warning(f"Could not initialize Geoapify MCP client: {e}")
            _geoapify_tools = {}

        return _geoapify_tools


def _parse_mcp_response(res: Any) -> Union[dict, list, str]:
    """Helper to parse JSON string or data from MCP content blocks."""
    if res is None:
        return {}
    if isinstance(res, list) and len(res) > 0:
        first = res[0]
        if isinstance(first, dict) and "text" in first:
            text_content = first["text"]
            try:
                return json.loads(text_content)
            except Exception:
                return text_content
        if hasattr(first, "text"):
            text_content = getattr(first, "text")
            try:
                return json.loads(text_content)
            except Exception:
                return text_content
        if hasattr(first, "content"):
            content = getattr(first, "content")
            if isinstance(content, str):
                try:
                    return json.loads(content)
                except Exception:
                    return content
            return content
        return res
    elif isinstance(res, str):
        try:
            return json.loads(res)
        except Exception:
            return res
    elif hasattr(res, "content"):
        content = getattr(res, "content")
        if isinstance(content, str):
            try:
                return json.loads(content)
            except Exception:
                return content
        return content
    return res


async def _execute_rest_get(url: str, params: dict, timeout: float = 8.0) -> Optional[requests.Response]:
    """Executes a synchronous requests.get non-blockingly using asyncio.to_thread."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(requests.get, url, params=params, timeout=timeout),
            timeout=timeout + 2.0,
        )
    except Exception as e:
        logger.warning(f"REST request to {url} failed: {e}")
        return None


async def geoapify_mcp_geocode(query: str, is_city: bool = False) -> Optional[dict]:
    """
    Geocodes a free-text location/city into coordinates using Geoapify MCP (or REST fallback).
    Non-blocking and concurrency-safe.
    """
    try:
        api_key = get_geoapify_api_key()
    except ValueError:
        logger.warning("GEOAPIFY_API_KEY is not configured.")
        return None

    if not query or not str(query).strip():
        return None

    query = str(query).strip()

    # For city destinations, query with type=city to ensure exact city matching (e.g. Paris, France vs a church named Parish)
    if is_city:
        try:
            url = "https://api.geoapify.com/v1/geocode/search"
            resp = await _execute_rest_get(
                url,
                params={"text": query, "type": "city", "limit": 1, "apiKey": api_key},
                timeout=8.0,
            )
            if resp and resp.status_code == 200:
                features = resp.json().get("features", [])
                if features:
                    props = features[0].get("properties", {})
                    return {
                        "lat": props.get("lat"),
                        "lon": props.get("lon"),
                        "formatted": props.get("formatted", query),
                        "city": props.get("city", query),
                        "country": props.get("country", ""),
                    }
        except Exception as e:
            logger.warning(f"Geoapify city geocode failed, falling back to general MCP: {e}")

    # General geocode via MCP
    try:
        tools = await init_geoapify_tools()
        if "geocode_address" in tools:
            res = await asyncio.wait_for(
                tools["geocode_address"].ainvoke({"query": query, "limit": 3}),
                timeout=DEFAULT_TIMEOUT,
            )
            data = _parse_mcp_response(res)
            if isinstance(data, dict) and "results" in data and len(data["results"]) > 0:
                items = data["results"]
                best_item = next((it for it in items if it.get("result_type") == "city"), items[0]) if is_city else items[0]
                return {
                    "lat": best_item.get("lat"),
                    "lon": best_item.get("lon"),
                    "formatted": best_item.get("formatted", query),
                    "city": best_item.get("city", query),
                    "country": best_item.get("country", ""),
                }
    except Exception as e:
        logger.warning(f"Geoapify MCP geocode failed, falling back to REST: {e}")

    # Fallback to direct REST API
    try:
        url = "https://api.geoapify.com/v1/geocode/search"
        resp = await _execute_rest_get(
            url,
            params={"text": query, "limit": 1, "apiKey": api_key},
            timeout=8.0,
        )
        if resp and resp.status_code == 200:
            features = resp.json().get("features", [])
            if features:
                props = features[0].get("properties", {})
                return {
                    "lat": props.get("lat"),
                    "lon": props.get("lon"),
                    "formatted": props.get("formatted", query),
                    "city": props.get("city", query),
                    "country": props.get("country", ""),
                }
    except Exception as e:
        logger.error(f"Geoapify REST geocode fallback failed: {e}")

    return None


async def geoapify_mcp_search_places(city: str, category: str = "tourism.sights", limit: int = 5) -> str:
    """
    Finds places by category (tourism.sights, catering.cafe, catering.restaurant, etc.)
    and returns a token-optimized clean text summary.
    """
    try:
        api_key = get_geoapify_api_key()
    except ValueError:
        return "Geoapify API key not configured."

    if not city or not str(city).strip():
        return "No destination city provided."

    # Step 1: Geocode city to coordinates
    loc = await geoapify_mcp_geocode(city, is_city=True)
    if not loc or not loc.get("lat") or not loc.get("lon"):
        return f"Could not determine coordinates for destination '{city}'."

    lat = loc["lat"]
    lon = loc["lon"]
    formatted_city = loc["formatted"]

    category_title = "Tourist Attractions & Sights"
    if "cafe" in category:
        category_title = "Cafes & Coffee Spots"
    elif "restaurant" in category:
        category_title = "Recommended Restaurants & Dining"

    # Step 2: Query MCP search_places
    try:
        tools = await init_geoapify_tools()
        if "search_places" in tools:
            res = await asyncio.wait_for(
                tools["search_places"].ainvoke({
                    "category": category,
                    "lat": lat,
                    "lon": lon,
                    "limit": limit,
                }),
                timeout=DEFAULT_TIMEOUT,
            )
            data = _parse_mcp_response(res)
            if isinstance(data, dict) and "results" in data:
                items = data["results"]
                if items:
                    lines = [f"Top {category_title} in {formatted_city}:"]
                    for idx, place in enumerate(items, 1):
                        name = place.get("name") or place.get("formatted", "Place")
                        addr = place.get("formatted", "")
                        cats = ", ".join(place.get("categories", [])[:2])
                        lines.append(f"{idx}. {name} — {addr} ({cats})")
                    return "\n".join(lines)
    except Exception as e:
        logger.warning(f"Geoapify MCP search_places failed, attempting REST fallback: {e}")

    # Fallback to direct Places REST API (non-blocking)
    try:
        url = "https://api.geoapify.com/v2/places"
        params = {
            "categories": category,
            "filter": f"circle:{lon},{lat},10000",
            "bias": f"proximity:{lon},{lat}",
            "limit": limit,
            "apiKey": api_key,
        }
        resp = await _execute_rest_get(url, params=params, timeout=8.0)
        if resp and resp.status_code == 200:
            features = resp.json().get("features", [])
            if features:
                lines = [f"Top {category_title} in {formatted_city}:"]
                for idx, feat in enumerate(features, 1):
                    props = feat.get("properties", {})
                    name = props.get("name") or props.get("formatted", "Place")
                    addr = props.get("formatted", "")
                    cats = ", ".join(props.get("categories", [])[:2])
                    lines.append(f"{idx}. {name} — {addr} ({cats})")
                return "\n".join(lines)
    except Exception as e:
        logger.error(f"Geoapify REST Places fallback failed: {e}")

    return f"No {category_title.lower()} found for {city} via Geoapify."


async def geoapify_mcp_calculate_route(origin: str, destination: str, mode: str = "drive") -> str:
    """
    Calculates driving/walking route distance and travel time between two waypoints.
    """
    try:
        get_geoapify_api_key()
    except ValueError:
        return "Geoapify API key not configured."

    if not origin or not str(origin).strip() or not destination or not str(destination).strip():
        return "Both origin and destination locations must be provided."

    orig_loc = await geoapify_mcp_geocode(origin)
    dest_loc = await geoapify_mcp_geocode(destination)
    if not orig_loc or not dest_loc:
        return f"Could not resolve locations for routing: '{origin}' to '{destination}'."

    waypoints = [
        {"lat": orig_loc["lat"], "lon": orig_loc["lon"]},
        {"lat": dest_loc["lat"], "lon": dest_loc["lon"]},
    ]

    try:
        tools = await init_geoapify_tools()
        if "calculate_route" in tools:
            res = await asyncio.wait_for(
                tools["calculate_route"].ainvoke({
                    "waypoints": waypoints,
                    "mode": mode,
                }),
                timeout=DEFAULT_TIMEOUT,
            )
            data = _parse_mcp_response(res)
            if isinstance(data, dict):
                dist_m = data.get("distance", 0)
                time_s = data.get("time", 0)
                dist_km = round(dist_m / 1000, 1)
                time_min = round(time_s / 60)
                hours = time_min // 60
                mins = time_min % 60
                time_str = f"{hours}h {mins}m" if hours > 0 else f"{mins} mins"
                return (
                    f"Route from {orig_loc['formatted']} to {dest_loc['formatted']}:\n"
                    f"• Mode: {mode.capitalize()}\n"
                    f"• Distance: {dist_km} km\n"
                    f"• Estimated Travel Time: {time_str}"
                )
    except Exception as e:
        logger.warning(f"Geoapify calculate_route failed: {e}")

    return f"Routing unavailable between '{origin}' and '{destination}'."


__all__ = [
    "client",
    "get_mcp_client",
    "init_geoapify_tools",
    "geoapify_mcp_geocode",
    "geoapify_mcp_search_places",
    "geoapify_mcp_calculate_route",
    "get_geoapify_api_key",
    "redact_api_key",
    "reset_geoapify_cache",
]
