import os
import re
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


# Load Environment Variables
# Load API keys from the project .env file
load_dotenv()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


# FastMCP Server Initialization
# FastMCP creates standard MCP tools that agents or external clients can invoke.
mcp = FastMCP("Weather MCP Server")

# Correct OpenWeatherMap API endpoints
CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"



# Tool 1: Get Current Real-Time Weather

@mcp.tool()
def get_current_weather(city: str) -> dict:
    """
    Fetch current real-time weather details for a given city.

    Parameters:
        city (str): The destination city (e.g., 'Dubai', 'Tokyo').

    Returns:
        dict: Weather information including temperature, humidity, condition, and wind speed.
    """
    if not OPENWEATHER_API_KEY:
        return {"error": "OPENWEATHER_API_KEY is not set in your .env file."}

    # Sanitize city parameter (strip prefixes like 'Destination:', quotes, extra whitespace)
    city = re.sub(r'^(destination|city|location|target)\s*:\s*', '', str(city), flags=re.IGNORECASE).strip(" .\n\"'")

    try:
        # Call OpenWeatherMap Current Weather API
        response = requests.get(
            url=CURRENT_WEATHER_URL,
            params={
                "q": city,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric",  # Request temperature in Celsius
            },
            # Timeout (10 seconds): Stops the request after 10s so the agent workflow
            # does not freeze/hang indefinitely if the API or network connection is slow.
            timeout=10,
        )

        data = response.json()

        # If the API returns an error status (like 404 city not found)
        if response.status_code != 200:
            return {"error": data.get("message", "Failed to fetch weather data.")}

        # Parse and return clean data
        return {
            "city": data.get("name", city),
            "temperature": f"{data['main']['temp']} °C",
            "feels_like": f"{data['main']['feels_like']} °C",
            "humidity": f"{data['main']['humidity']}%",
            "condition": data["weather"][0]["description"].capitalize(),
            "wind_speed": f"{data['wind']['speed']} m/s",
        }

    except Exception as error:
        return {"error": str(error)}



# Tool 2: Get 5-Day Weather Forecast

@mcp.tool()
def get_forecast(city: str) -> dict:
    """
    Fetch 5-day weather forecast summary for a given city.

    Parameters:
        city (str): The destination city (e.g., 'Dubai', 'London').

    Returns:
        dict: Forecast list containing upcoming 3-hour intervals with temperature and condition.
    """
    if not OPENWEATHER_API_KEY:
        return {"error": "OPENWEATHER_API_KEY is not set in your .env file."}

    # Sanitize city parameter (strip prefixes like 'Destination:', quotes, extra whitespace)
    city = re.sub(r'^(destination|city|location|target)\s*:\s*', '', str(city), flags=re.IGNORECASE).strip(" .\n\"'")

    try:
        # Call OpenWeatherMap 5-Day Forecast API
        response = requests.get(
            url=FORECAST_URL,
            params={
                "q": city,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric",
            },
            # Timeout (10 seconds): Prevents the whole multi-agent pipeline from getting stuck
            # if the forecast API endpoint takes too long to respond.
            timeout=10,
        )

        data = response.json()

        if response.status_code != 200:
            return {"error": data.get("message", "Failed to fetch forecast data.")}

        # Extract the next 5 intervals (each interval is 3 hours ahead)
        forecast_list = []
        for item in data.get("list", [])[:5]:
            forecast_list.append({
                "datetime": item.get("dt_txt"),
                "temp": f"{item['main']['temp']} °C",
                "weather": item["weather"][0]["description"].capitalize(),
            })

        return {
            "city": data.get("city", {}).get("name", city),
            "forecast": forecast_list,
        }

    except Exception as error:
        return {"error": str(error)}



# Helper Functions for Weather Agent
# These async functions format the weather data into readable strings for the LLM.

async def weather_mcp_search(city: str) -> str:
    """
    Asynchronously get current weather and return a clean text summary.
    Used by weather_agent in the LangGraph workflow.
    """
    res = get_current_weather(city)
    if "error" in res:
        return f"Current weather unavailable: {res['error']}"

    return (
        f"City: {res['city']} | Temp: {res['temperature']} (Feels like: {res['feels_like']}) | "
        f"Condition: {res['condition']} | Humidity: {res['humidity']} | Wind: {res['wind_speed']}"
    )


async def forecast_mcp_search(city: str) -> str:
    """
    Asynchronously get forecast and return a bullet-point text summary.
    Used by weather_agent in the LangGraph workflow.
    """
    res = get_forecast(city)
    if "error" in res:
        return f"Forecast unavailable: {res['error']}"

    summary = [f"City: {res['city']} Upcoming Forecast:"]
    for item in res.get("forecast", []):
        summary.append(f"• {item['datetime']} -> {item['temp']}, {item['weather']}")
    return "\n".join(summary)


# Explicitly export functions and mcp server
__all__ = [
    "mcp",
    "get_current_weather",
    "get_forecast",
    "weather_mcp_search",
    "forecast_mcp_search",
]

# Run FastMCP server if executed directly
if __name__ == "__main__":
    mcp.run()
