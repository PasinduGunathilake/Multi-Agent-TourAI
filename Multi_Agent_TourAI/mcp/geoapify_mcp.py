import os
import json
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

GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")

# Remote Geaapify MCP Server client (HTTP JSON-RPC)
client = MultiServerMCPClient({
    "geoapify-remote-mcp":{
        "transport": "http",
        "url": f"https://api.geoapify.com/v1/mcp?apiKey={GEOAPIFY_API_KEY}",
    }
})

# Tool Cache Dictionary: maps tool name to tool object
_geoapify_tools = {}

async def init_geoapify_tools():
    """Loads Geoapify MCP tools once and caches them in memory."""
    global _geoapify_tools
    if _geoapify_tools:
        return _geoapify_tools

    try:
        tools = await client.get_tools()
        _geoapify_tools = {t.name: t for t in tools}
        logger.info(f"Loaded {len(_geoapify_tools)} tools from Geoapify Remote MCP server.")
    except Exception as e:
        logger.warning(f"Could not initialize Geoapify MCP client: {e}")

        _geoapify_tools = {}

    return _geoapify_tools


def _parse_mcp_response(res) -> dict | list | str:
    """Helper to parse JSON string from MCP text content blocks."""
    if isinstance(res, list) and len(res) > 0 and isinstance(res[0], dict) and "text" in res[0]:
        text_content = res[0]["text"]
        try:
            return json.loads(text_content)
        except Exception:
            return text_content
    elif isinstance(res, str):
        try:
            return json.loads(res)
        except Exception:
            return res
    return res


async def geoapify_mcp_geocode(query: str) -> dict | None:
    """
    Geocodes a free-text location/city into coordinates using Geoapify MCP (or REST fallback).
    """
    if not GEOAPIFY_API_KEY:
        logger.warning("GEOAPIFY_API_KEY is not set.")
        return None
    # Try MCP first
    try:
        tools = await init_geoapify_tools()
        if "geocode_address" in tools:
            res = await tools["geocode_address"].ainvoke({"query": query, "limit": 1})
            data = _parse_mcp_response(res)
            if isinstance(data, dict) and "results" in data and len(data["results"]) > 0:
                item = data["results"][0]
                return {
                    "lat": item.get("lat"),
                    "lon": item.get("lon"),
                    "formatted": item.get("formatted", query),
                    "city": item.get("city", query),
                    "country": item.get("country", ""),
                }
    except Exception as e:
        logger.warning(f"Geoapify MCP geocode failed, falling back to REST: {e}")
    # Fallback to direct REST API
    try:
        url = "https://api.geoapify.com/v1/geocode/search"
        resp = requests.get(url, params={"text": query, "limit": 1, "apiKey": GEOAPIFY_API_KEY}, timeout=8)
        if resp.status_code == 200:
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
    if not GEOAPIFY_API_KEY:
        return "Geoapify API key not configured."
    # Step 1: Geocode city to coordinates
    loc = await geoapify_mcp_geocode(city)
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
            res = await tools["search_places"].ainvoke({
                "category": category,
                "lat": lat,
                "lon": lon,
                "limit": limit
            })
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
    # Fallback to direct Places REST API
    try:
        url = "https://api.geoapify.com/v2/places"
        params = {
            "categories": category,
            "filter": f"circle:{lon},{lat},10000",
            "bias": f"proximity:{lon},{lat}",
            "limit": limit,
            "apiKey": GEOAPIFY_API_KEY,
        }
        resp = requests.get(url, params=params, timeout=8)
        if resp.status_code == 200:
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
    if not GEOAPIFY_API_KEY:
        return "Geoapify API key not configured."
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
            res = await tools["calculate_route"].ainvoke({
                "waypoints": waypoints,
                "mode": mode,
            })
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
    "init_geoapify_tools",
    "geoapify_mcp_geocode",
    "geoapify_mcp_search_places",
    "geoapify_mcp_calculate_route",
]