import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather(location: str) -> str:
    """The only function in this entire codebase that is allowed to make a
    network call for reasoning support (Open-Meteo needs no API key). It
    returns a raw fact string; all phrasing/reasoning about it still happens
    locally in src/llm/reasoning.py. Keeping this isolated in its own module
    is what makes the online/offline boundary demoable and auditable."""
    geo = requests.get(GEOCODE_URL, params={"name": location, "count": 1}, timeout=5).json()
    results = geo.get("results")
    if not results:
        return f"No weather data found for '{location}'."

    lat, lon = results[0]["latitude"], results[0]["longitude"]
    forecast = requests.get(
        FORECAST_URL,
        params={"latitude": lat, "longitude": lon, "current": "temperature_2m,weather_code"},
        timeout=5,
    ).json()

    temp = forecast.get("current", {}).get("temperature_2m")
    if temp is None:
        return f"Weather data unavailable for {location}."
    return f"Current temperature in {location} is {temp}°C."
