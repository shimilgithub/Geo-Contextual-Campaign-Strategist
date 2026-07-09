from typing import Any, Dict, List, Literal, Optional, cast

import httpx
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field, StrictFloat, StrictInt, StrictStr

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_USER_AGENT = "Geo-Context-MCP-Server/1.0"


class WeatherQuery(BaseModel):
    latitude: StrictFloat = Field(..., description="Latitude of the requested location")
    longitude: StrictFloat = Field(..., description="Longitude of the requested location")


class PlacesQuery(BaseModel):
    latitude: StrictFloat = Field(..., description="Latitude of the search center")
    longitude: StrictFloat = Field(..., description="Longitude of the search center")
    radius: StrictInt = Field(
        1000,
        gt=0,
        le=5000,
        description="Search radius in meters, maximum 5000",
    )


class WeatherCurrent(BaseModel):
    time: StrictStr
    temperature: StrictFloat
    windspeed: StrictFloat
    winddirection: StrictFloat
    weathercode: StrictInt
    is_day: StrictInt
    interval: StrictInt


class WeatherResponse(BaseModel):
    source: Literal["open-meteo"] = "open-meteo"
    query: WeatherQuery
    current_weather: WeatherCurrent


class Cafe(BaseModel):
    id: StrictInt
    type: StrictStr
    name: Optional[StrictStr]
    latitude: StrictFloat
    longitude: StrictFloat
    tags: Dict[StrictStr, StrictStr] = Field(default_factory=dict)


class PlacesResponse(BaseModel):
    source: Literal["overpass"] = "overpass"
    query: PlacesQuery
    count: StrictInt
    cafes: List[Cafe]


app = FastAPI(title="Geo-Context MCP Server", version="1.0")


async def fetch_open_meteo(latitude: float, longitude: float) -> Dict[str, Any]:
    params: Dict[str, str] = {
        "latitude": str(latitude),
        "longitude": str(longitude),
        "current_weather": "true",
        "timezone": "auto",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(OPEN_METEO_URL, params=params)
            response.raise_for_status()
            payload = cast(Dict[str, Any], response.json())
            return payload
    except httpx.TimeoutException:
        raise HTTPException(status_code=500, detail="Open-Meteo request timed out")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Open-Meteo returned {exc.response.status_code}",
        )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=500, detail=f"Open-Meteo request failed: {exc}")
    except ValueError:
        raise HTTPException(status_code=500, detail="Open-Meteo returned invalid JSON")


async def fetch_overpass(latitude: float, longitude: float, radius: int) -> Dict[str, Any]:
    query = f"""
[out:json][timeout:25];
(
  node["amenity"="cafe"](around:{radius},{latitude},{longitude});
  way["amenity"="cafe"](around:{radius},{latitude},{longitude});
  relation["amenity"="cafe"](around:{radius},{latitude},{longitude});
);
out center tags;
"""
    headers = {
        "User-Agent": OVERPASS_USER_AGENT,
        "Accept": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(OVERPASS_URL, data={"data": query}, headers=headers)
            response.raise_for_status()
            payload = cast(Dict[str, Any], response.json())
            return payload
    except httpx.TimeoutException:
        raise HTTPException(status_code=500, detail="Overpass request timed out")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Overpass returned {exc.response.status_code}",
        )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=500, detail=f"Overpass request failed: {exc}")
    except ValueError:
        raise HTTPException(status_code=500, detail="Overpass returned invalid JSON")


@app.get("/api/weather", response_model=WeatherResponse)
async def get_weather(query: WeatherQuery = Depends()) -> WeatherResponse:
    payload = await fetch_open_meteo(query.latitude, query.longitude)
    current = payload.get("current_weather")
    if not isinstance(current, dict):
        raise HTTPException(status_code=500, detail="Open-Meteo did not return current weather data")

    try:
        weather = WeatherCurrent(**current)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=f"Invalid Open-Meteo weather payload: {exc}")

    return WeatherResponse(query=query, current_weather=weather)


@app.get("/api/places", response_model=PlacesResponse)
async def get_places(query: PlacesQuery = Depends()) -> PlacesResponse:
    payload = await fetch_overpass(query.latitude, query.longitude, query.radius)
    elements = payload.get("elements")
    if not isinstance(elements, list):
        raise HTTPException(status_code=500, detail="Overpass did not return elements")

    cafes: List[Cafe] = []
    for element in elements:
        if not isinstance(element, dict):
            continue
        tags = element.get("tags") or {}
        latitude = element.get("lat")
        longitude = element.get("lon")
        if latitude is None or longitude is None:
            center = element.get("center") or {}
            latitude = center.get("lat")
            longitude = center.get("lon")

        if latitude is None or longitude is None:
            continue

        cafe_data = {
            "id": element.get("id"),
            "type": element.get("type"),
            "name": tags.get("name"),
            "latitude": latitude,
            "longitude": longitude,
            "tags": {str(k): str(v) for k, v in tags.items() if isinstance(k, str) and isinstance(v, str)},
        }
        try:
            cafes.append(Cafe(**cafe_data))
        except ValueError:
            continue

    return PlacesResponse(query=query, count=len(cafes), cafes=cafes)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
