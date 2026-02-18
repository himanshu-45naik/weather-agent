from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather")

NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"



async def make_nws_request(url: str) -> dict[str, Any] | None:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[NWS ERROR] {url} -> {e}")
            return None


# FORECAST 
@mcp.tool(
    name="get_forecast_by_place",
    description=""" Use this tool to get forecast of a particular place.
    Get weather forecast for any US city or place by name. Handles geocoding internally."""
)
async def get_forecast_by_place(place: str) -> str:

    # Step 1: Geocode
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={place}&count=1"
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(geo_url, timeout=20)
            r.raise_for_status()
            geo_data = r.json()
        except Exception:
            return "Geocoding failed. Try again with a valid US city name."

    if not geo_data.get("results"):
        return f"Could not find '{place}'. Try a major US city name."

    loc = geo_data["results"][0]
    lat = loc.get("latitude")
    lon = loc.get("longitude")
    country = loc.get("country")
    name = loc.get("name")

    if country != "United States":
        return f"'{place}' resolved to {name}, {country} — not a US location. Try a US city."

    # Step 2: NWS points
    points_data = await make_nws_request(f"{NWS_API_BASE}/points/{lat},{lon}")
    if not points_data:
        return f"NWS has no forecast office for {name} ({lat}, {lon}). This can happen for remote areas."

    # Step 3: Forecast
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)
    if not forecast_data:
        return "Forecast data unavailable from NWS."

    periods = forecast_data["properties"]["periods"][:5]
    out = [f"Forecast for {name}:"]
    for p in periods:
        out.append(
            f"{p['name']}: {p['temperature']}°{p['temperatureUnit']}, "
            f"{p['windSpeed']} {p['windDirection']} — {p['detailedForecast']}"
        )

    return "\n".join(out)


# ALERTS
@mcp.tool(
    name="get_us_hazard_alerts",
    description="""Convert place name to  US state code.
    Get hazard alerts using two letter US state code"""
)
async def get_alerts(state_code: str) -> str:

    if len(state_code) != 2:
        return "Invalid state code. Provide two-letter US code like CA or TX."

    url = f"{NWS_API_BASE}/alerts/active/area/{state_code.upper()}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "No alert data returned."

    if not data["features"]:
        return "No active hazard alerts."

    alerts = []
    for feature in data["features"]:
        props = feature["properties"]
        alerts.append(
            f"{props.get('event')} | {props.get('severity')} | {props.get('areaDesc')}"
        )

    return "\n".join(alerts)


def main():
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
