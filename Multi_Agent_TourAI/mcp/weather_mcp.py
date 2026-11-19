import asyncio
import os
import re
from typing import Optional, Dict, Any
import certifi
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from Multi_Agent_TourAI.utils import get_logger

# SSL certificate setup for Windows
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

load_dotenv()
logger = get_logger(__name__)

DEFAULT_TIMEOUT = 15.0

# OpenWeatherMap API Endpoints
CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


def redact_api_key(key: Optional[str]) -> str:
    """Masks an API key for safe logging, displaying only first 4 and last 4 characters."""
    if not key or not str(key).strip():
        return "[NOT SET]"
    key_str = str(key).strip()
    if len(key_str) <= 8:
        return "***"
    return f"{key_str[:4]}...{key_str[-4:]}"


def get_openweather_api_key() -> str:
    """Validates and returns the configured OpenWeatherMap API key."""
    key = os.getenv("OPENWEATHER_API_KEY")
    if not key or not key.strip():
        raise ValueError(
            "OPENWEATHER_API_KEY is missing or empty. Please set OPENWEATHER_API_KEY in your environment."
        )
    return key.strip()


def sanitize_city_query(city: Any) -> str:
    """Sanitizes city parameter, stripping prompt prefixes, quotes, and whitespace."""
    if not city:
        return ""
    clean = re.sub(
        r"^(destination|city|location|target)\s*:\s*",
        "",
        str(city),
        flags=re.IGNORECASE,
    ).strip(" .\n\"'")
    return clean


# FastMCP Server Initialization
mcp = FastMCP("Weather MCP Server")


@mcp.tool()
def get_current_weather(city: str) -> dict:
    """
    Fetch current real-time weather details for a given city.

    Parameters:
        city (str): The destination city (e.g., 'Dubai', 'Tokyo').

    Returns:
        dict: Weather information including temperature, humidity, condition, and wind speed.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key or not api_key.strip():
        logger.warning("OpenWeatherMap API key is missing or not set.")
        return {"error": "OPENWEATHER_API_KEY is not set in your .env file."}

    clean_city = sanitize_city_query(city)
    if not clean_city:
        return {"error": "No valid destination city provided."}

    try:
        response = requests.get(
            url=CURRENT_WEATHER_URL,
            params={
                "q": clean_city,
                "appid": api_key.strip(),
                "units": "metric",
            },
            timeout=10,
        )

        data = response.json()

        if response.status_code != 200:
            msg = data.get("message", f"HTTP {response.status_code}")
            return {"error": f"Failed to fetch weather data: {msg}"}

        return {
            "city": data.get("name", clean_city),
            "temperature": f"{data['main']['temp']} °C",
            "feels_like": f"{data['main']['feels_like']} °C",
            "humidity": f"{data['main']['humidity']}%",
            "condition": data["weather"][0]["description"].capitalize() if data.get("weather") else "Clear",
            "wind_speed": f"{data['wind']['speed']} m/s" if data.get("wind") else "N/A",
        }

    except requests.exceptions.Timeout:
        logger.error(f"OpenWeatherMap current weather request timed out for city '{clean_city}'")
        return {"error": "Weather request timed out."}
    except Exception as error:
        logger.error(f"OpenWeatherMap request failed: {str(error)}")
        return {"error": str(error)}


@mcp.tool()
def get_forecast(city: str) -> dict:
    """
    Fetch 5-day weather forecast summary for a given city.

    Parameters:
        city (str): The destination city (e.g., 'Dubai', 'London').

    Returns:
        dict: Forecast list containing upcoming 3-hour intervals with temperature and condition.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key or not api_key.strip():
        logger.warning("OpenWeatherMap API key is missing or not set.")
        return {"error": "OPENWEATHER_API_KEY is not set in your .env file."}

    clean_city = sanitize_city_query(city)
    if not clean_city:
        return {"error": "No valid destination city provided."}

    try:
        response = requests.get(
            url=FORECAST_URL,
            params={
                "q": clean_city,
                "appid": api_key.strip(),
                "units": "metric",
            },
            timeout=10,
        )

        data = response.json()

        if response.status_code != 200:
            msg = data.get("message", f"HTTP {response.status_code}")
            return {"error": f"Failed to fetch forecast data: {msg}"}

        forecast_list = []
        for item in data.get("list", [])[:5]:
            weather_desc = item["weather"][0]["description"].capitalize() if item.get("weather") else "Clear"
            forecast_list.append({
                "datetime": item.get("dt_txt"),
                "temp": f"{item['main']['temp']} °C",
                "weather": weather_desc,
            })

        return {
            "city": data.get("city", {}).get("name", clean_city),
            "forecast": forecast_list,
        }

    except requests.exceptions.Timeout:
        logger.error(f"OpenWeatherMap forecast request timed out for city '{clean_city}'")
        return {"error": "Forecast request timed out."}
    except Exception as error:
        logger.error(f"OpenWeatherMap forecast request failed: {str(error)}")
        return {"error": str(error)}


# Non-blocking async helpers for agent execution

async def weather_mcp_search(city: str) -> str:
    """
    Asynchronously get current weather and return a clean text summary.
    Executes in a thread pool to avoid blocking the event loop.
    """
    if not city or not str(city).strip():
        return "No destination city provided."

    try:
        res = await asyncio.wait_for(
            asyncio.to_thread(get_current_weather, city),
            timeout=DEFAULT_TIMEOUT,
        )
    except asyncio.TimeoutError:
        return "Current weather unavailable: Request timed out."
    except Exception as e:
        return f"Current weather unavailable: {str(e)}"

    if "error" in res:
        return f"Current weather unavailable: {res['error']}"

    return (
        f"City: {res['city']} | Temp: {res['temperature']} (Feels like: {res['feels_like']}) | "
        f"Condition: {res['condition']} | Humidity: {res['humidity']} | Wind: {res['wind_speed']}"
    )


async def forecast_mcp_search(city: str) -> str:
    """
    Asynchronously get forecast and return a bullet-point text summary.
    Executes in a thread pool to avoid blocking the event loop.
    """
    if not city or not str(city).strip():
        return "No destination city provided."

    try:
        res = await asyncio.wait_for(
            asyncio.to_thread(get_forecast, city),
            timeout=DEFAULT_TIMEOUT,
        )
    except asyncio.TimeoutError:
        return "Forecast unavailable: Request timed out."
    except Exception as e:
        return f"Forecast unavailable: {str(e)}"

    if "error" in res:
        return f"Forecast unavailable: {res['error']}"

    summary = [f"City: {res['city']} Upcoming Forecast:"]
    for item in res.get("forecast", []):
        summary.append(f"• {item['datetime']} -> {item['temp']}, {item['weather']}")
    return "\n".join(summary)


__all__ = [
    "mcp",
    "get_current_weather",
    "get_forecast",
    "weather_mcp_search",
    "forecast_mcp_search",
    "get_openweather_api_key",
    "redact_api_key",
    "sanitize_city_query",
]

if __name__ == "__main__":
    mcp.run()
