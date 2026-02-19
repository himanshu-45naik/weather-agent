from typing import Any
import httpx
from datetime import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather")

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Weather codes -> Weather description
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 
    2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}

# Function to decode weathers
def decode_weather(code: int) -> str:
    return WEATHER_CODES.get(code, f"Unknown (code {code})")

# Get geocode for a city
async def geocode(place: str) -> dict | None:
    city = place.split(",")[0].strip()
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            r = await client.get(
                GEOCODING_URL,
                params={"name": city, "count": 1},
                timeout=20
            )
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        print(f"[GEOCODE ERROR] {e}")
        return None

    if not data.get("results"):
        return None

    loc = data["results"][0]
    return {
        "name": loc.get("name"),
        "latitude": loc.get("latitude"),
        "longitude": loc.get("longitude"),
        "country": loc.get("country"),
    }


async def fetch_open_meteo(params: dict) -> dict | None:
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            r = await client.get(FORECAST_URL, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        print(f"[OPEN-METEO ERROR] {e}")
        return None


# Current weather tool
@mcp.tool(
    name="get_current_weather",
    description="Get current weather for any city in the world by name."
)
async def get_current_weather(place: str) -> str:
    loc = await geocode(place)
    if not loc:
        return f"Could not find '{place}'. Try a valid city name."

    data = await fetch_open_meteo({
        "latitude": loc["latitude"],
        "longitude": loc["longitude"],
        "current": "temperature_2m,windspeed_10m,precipitation,weathercode,relativehumidity_2m",
        "timezone": "auto"
    })

    if not data:
        return "Weather data unavailable. Try again."

    c = data["current"]
    code = c["weathercode"]
    return (
        f"Current weather for {loc['name']}, {loc['country']}:\n"
        f"Condition   : {decode_weather(code)} (code {code})\n"
        f"Temperature : {c['temperature_2m']}°C\n"
        f"Humidity    : {c['relativehumidity_2m']}%\n"
        f"Wind Speed  : {c['windspeed_10m']} km/h\n"
        f"Precipitation: {c['precipitation']} mm\n"
    )


# Forecast tool -> one api call gives max 16 Days forecast
@mcp.tool(
    name="get_forecast_by_place",
    description=(
        "Get weather forecast for any city in the world by name. "
        "Requires start_date and end_date in YYYY-MM-DD format. "
        "Supports up to 16 days into the future and historical dates."
    )
)
async def get_forecast_by_place(place: str, start_date: str, end_date: str) -> str:

    # Date validation
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return "Dates must be in YYYY-MM-DD format (example: 2026-02-18)"
    
    loc = await geocode(place)
    if not loc:
        return f"Could not find '{place}'. Try a valid city name."

    data = await fetch_open_meteo({
        "latitude": loc["latitude"],
        "longitude": loc["longitude"],
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,weathercode",
        "start_date": start_date,
        "end_date": end_date,
        "timezone": "auto"
    })

    if not data:
        return "Forecast data unavailable. Try again."

    daily = data["daily"]
    out = [f"Forecast for {loc['name']}, {loc['country']} ({start_date} to {end_date}):"]

    for i, date in enumerate(daily["time"]):
        code = daily["weathercode"][i]
        out.append(
            f"{date}: {decode_weather(code)} (code {code}) | "
            f"High {daily['temperature_2m_max'][i]}°C / "
            f"Low {daily['temperature_2m_min'][i]}°C | "
            f"Precipitation: {daily['precipitation_sum'][i]}mm | "
            f"Max Wind: {daily['windspeed_10m_max'][i]} km/h"
        )

    return "\n".join(out)


def main():
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()