import httpx
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

# --- 1. Define Tools connecting to MCP Server ---
@tool
async def get_local_weather(lat: float, lon: float) -> str:
    """Fetch the current temperature from the local MCP wrapper.

    This tool calls the local FastAPI weather endpoint at http://localhost:8000/api/weather
    using asynchronous HTTP requests.

    Parameters:
    - lat: The geographic latitude for the location, in decimal degrees.
    - lon: The geographic longitude for the location, in decimal degrees.

    Use this tool when the agent needs a precise ambient temperature for a specific
    location to decide campaign timing, seasonal messaging, or product positioning.
    It returns only the temperature as a human-readable string.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"http://localhost:8000/api/weather?latitude={lat}&longitude={lon}")
            response.raise_for_status()
            payload = response.json()
            current = payload.get("current_weather") or {}
            temperature = current.get("temperature")
            if temperature is None:
                return "Temperature data is unavailable from the local weather service."
            return f"The temperature is {temperature}°C."
    except httpx.HTTPStatusError as exc:
        return f"Weather fetch failed with status {exc.response.status_code}."
    except httpx.TimeoutException:
        return "Weather request timed out while contacting the local MCP service."
    except Exception as exc:
        return f"Unable to fetch local weather: {exc}"


@tool
async def get_amenity_density(lat: float, lon: float, amenity_type: str) -> str:
    """Estimate local amenity density using the local MCP wrapper.

    This tool calls the local FastAPI places endpoint at http://localhost:8000/api/places
    using asynchronous HTTP requests.

    Parameters:
    - lat: The geographic latitude for the search center, in decimal degrees.
    - lon: The geographic longitude for the search center, in decimal degrees.
    - amenity_type: The OpenStreetMap amenity type to search for, such as 'cafe',
      'restaurant', or 'park'.

    Use this tool when the agent requires competitive or foot-traffic context for
    marketing creative, location-based promotions, event planning, or local
    partnership recommendations. It returns a short description of the estimated
    amenity density around the target coordinates.
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"http://localhost:8000/api/places?latitude={lat}&longitude={lon}&radius=1000&amenity={amenity_type}"
            )
            response.raise_for_status()
            payload = response.json()
            count = payload.get("count")
            if count is None:
                return "Amenity density data is unavailable from the local service."
            return f"Estimated {count} {amenity_type} locations are within 1 km of the target area."
    except httpx.HTTPStatusError as exc:
        return f"Amenity density fetch failed with status {exc.response.status_code}."
    except httpx.TimeoutException:
        return "Amenity density request timed out while contacting the local MCP service."
    except Exception as exc:
        return f"Unable to fetch amenity density: {exc}"


tools = [get_local_weather, get_amenity_density]
# --- 2. Initialize Open Source LLM ---
# Using Ollama locally ensures 100% open-source compliance

llm = ChatOllama(model="llama3.1", temperature=0)

# --- 3. Create LangGraph Agent ---
agent_executor = create_react_agent(llm, tools)

def run_campaign_agent(prompt: str) -> str:
    """Executes the agent workflow."""
    system_prompt = (
        "You are a location-based marketing strategist. "
        "Use the provided tools to check the weather and surrounding amenities for the given coordinates. "
        "Based on the results, suggest a highly targeted advertising copy and strategy."
    )
    
    full_prompt = f"{system_prompt}\nUser Request: {prompt}"
    
    try:
        response = agent_executor.invoke({"messages": [HumanMessage(content=full_prompt)]})
        return response["messages"][-1].content
    except Exception as e:
         return f"Agent execution failed. Make sure Ollama is running. Error: {str(e)}"