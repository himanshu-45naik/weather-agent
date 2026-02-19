import asyncio
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("City-Attraction")

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

HEADERS = {
    "User-Agent": "CityAttractionsMCP",
}

client = httpx.AsyncClient(timeout=40, headers=HEADERS)


async def get_city_center(city: str) -> tuple | None:
    params = {
        "q": city,
        "format": "json",
        "limit": 1,
    }
    r = await client.get(NOMINATIM_URL, params=params)
    r.raise_for_status()
    data = r.json()
    if not data:
        return None
    return float(data[0]["lat"]), float(data[0]["lon"])


async def query_overpass(query: str) -> dict:
    for url in OVERPASS_URLS:
        try:
            r = await client.post(url, data={"data": query}, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception:
            await asyncio.sleep(2)
            continue
    raise Exception("All Overpass mirrors failed")


async def get_landmarks(city: str) -> list | None:
    coords = await get_city_center(city)
    if not coords:
        return None

    lat, lon = coords
    await asyncio.sleep(1)

    query = f"""
    [out:json][timeout:25];
    (
      node["tourism"="attraction"](around:10000,{lat},{lon});
      node["tourism"="museum"](around:10000,{lat},{lon});
      node["historic"="monument"](around:10000,{lat},{lon});
      node["historic"="memorial"](around:10000,{lat},{lon});
    );
    out body 15;
    """

    data = await query_overpass(query)
    return data.get("elements", [])


@mcp.tool(
    name="city_landmarks",
    description="Get famous landmarks and attractions in a city using OpenStreetMap",
)
async def city_landmarks(city: str) -> str:
    try:
        landmarks = await get_landmarks(city)
    except Exception as e:
        return f"Failed to retrieve landmarks: {str(e)}"

    if landmarks is None:
        return f"City '{city}' not found."

    if not landmarks:
        return f"No major landmarks found in {city}."

    lines = [f"Famous landmarks in {city}:\n"]
    for place in landmarks:
        name = place.get("tags", {}).get("name")
        if name:
            lines.append(f"- {name}")

    if len(lines) == 1:
        return f"No named landmarks found in {city}."

    return "\n".join(lines)


def main():
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()