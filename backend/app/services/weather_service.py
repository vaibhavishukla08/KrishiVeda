"""Weather data from OpenWeather (when an API key is configured) or Open-Meteo (free, no key).

Both providers are normalised to the same structure so the rest of the app does not care
which one answered. Values returned here are *measured/forecast* data from the provider.
"""

import time
from collections import defaultdict
from datetime import datetime, timezone

import httpx

from app.api.errors import AppError
from app.config import get_settings
from app.services.http_client import make_client

# WMO weather interpretation codes used by Open-Meteo
WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snowfall", 73: "Moderate snowfall", 75: "Heavy snowfall", 77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


def active_provider() -> str:
    return "openweather" if get_settings().openweather_api_key else "open-meteo"


CACHE_SECONDS = 600  # avoid calling the provider again for the same place within 10 minutes
_cache: dict[tuple, tuple[float, dict]] = {}


def get_weather(city: str | None = None, lat: float | None = None, lon: float | None = None) -> dict:
    if not city and (lat is None or lon is None):
        raise AppError(400, "LOCATION_REQUIRED", "Provide a city name or both latitude and longitude.")
    key = (active_provider(), (city or "").strip().lower(), lat, lon)
    hit = _cache.get(key)
    if hit and time.monotonic() - hit[0] < CACHE_SECONDS:
        return hit[1]
    try:
        with make_client() as client:
            if get_settings().openweather_api_key:
                data = _openweather(client, city, lat, lon)
            else:
                data = _open_meteo(client, city, lat, lon)
        _cache[key] = (time.monotonic(), data)
        return data
    except AppError:
        raise
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise AppError(
            503,
            "WEATHER_UNAVAILABLE",
            "Weather service is not reachable right now. Please try again later.",
            {"provider": active_provider(), "reason": type(exc).__name__},
        ) from exc


# ---------------------------------------------------------------- Open-Meteo
def _open_meteo(client: httpx.Client, city, lat, lon) -> dict:
    name = city
    if lat is None or lon is None:
        geo = client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
        )
        geo.raise_for_status()
        results = geo.json().get("results") or []
        if not results:
            raise AppError(404, "LOCATION_NOT_FOUND", f"Could not find a place called '{city}'.")
        place = results[0]
        lat, lon = place["latitude"], place["longitude"]
        name = ", ".join(p for p in [place.get("name"), place.get("admin1"), place.get("country")] if p)

    resp = client.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,"
            "precipitation_probability_max,et0_fao_evapotranspiration,weather_code",
            "timezone": "auto",
            "forecast_days": 5,
        },
    )
    resp.raise_for_status()
    data = resp.json()
    cur, daily = data["current"], data["daily"]
    forecast = [
        {
            "date": daily["time"][i],
            "temp_max_c": daily["temperature_2m_max"][i],
            "temp_min_c": daily["temperature_2m_min"][i],
            "rain_mm": daily["precipitation_sum"][i],
            "rain_probability_pct": daily["precipitation_probability_max"][i],
            "et0_mm": daily["et0_fao_evapotranspiration"][i],
            "condition": WMO_CODES.get(daily["weather_code"][i], "Unknown"),
        }
        for i in range(len(daily["time"]))
    ]
    return {
        "location": {"name": name or f"{lat:.2f}, {lon:.2f}", "latitude": lat, "longitude": lon},
        "current": {
            "observed_at": cur["time"],
            "temperature_c": cur["temperature_2m"],
            "humidity_pct": cur["relative_humidity_2m"],
            "precipitation_mm": cur["precipitation"],
            "wind_speed_kmh": cur["wind_speed_10m"],
            "condition": WMO_CODES.get(cur["weather_code"], "Unknown"),
        },
        "daily": forecast,
        "source": {"provider": "open-meteo", "name": "Open-Meteo.com (CC BY 4.0)", "url": "https://open-meteo.com/"},
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------- OpenWeather
def _openweather(client: httpx.Client, city, lat, lon) -> dict:
    key = get_settings().openweather_api_key
    name = city
    if lat is None or lon is None:
        geo = client.get("https://api.openweathermap.org/geo/1.0/direct", params={"q": city, "limit": 1, "appid": key})
        if geo.status_code == 401:
            raise AppError(503, "WEATHER_KEY_INVALID", "The OpenWeather API key was rejected. Check OPENWEATHER_API_KEY.")
        geo.raise_for_status()
        results = geo.json()
        if not results:
            raise AppError(404, "LOCATION_NOT_FOUND", f"Could not find a place called '{city}'.")
        lat, lon = results[0]["lat"], results[0]["lon"]
        name = ", ".join(p for p in [results[0].get("name"), results[0].get("state"), results[0].get("country")] if p)

    params = {"lat": lat, "lon": lon, "appid": key, "units": "metric"}
    cur_resp = client.get("https://api.openweathermap.org/data/2.5/weather", params=params)
    if cur_resp.status_code == 401:
        raise AppError(503, "WEATHER_KEY_INVALID", "The OpenWeather API key was rejected. Check OPENWEATHER_API_KEY.")
    cur_resp.raise_for_status()
    cur = cur_resp.json()
    fc_resp = client.get("https://api.openweathermap.org/data/2.5/forecast", params=params)
    fc_resp.raise_for_status()

    # Aggregate the 3-hourly forecast into days
    days: dict[str, dict] = defaultdict(lambda: {"tmax": -99.0, "tmin": 99.0, "rain": 0.0, "pop": 0.0, "cond": None})
    for item in fc_resp.json()["list"]:
        day = item["dt_txt"][:10]
        d = days[day]
        d["tmax"] = max(d["tmax"], item["main"]["temp_max"])
        d["tmin"] = min(d["tmin"], item["main"]["temp_min"])
        d["rain"] += item.get("rain", {}).get("3h", 0.0)
        d["pop"] = max(d["pop"], item.get("pop", 0.0))
        d["cond"] = d["cond"] or item["weather"][0]["description"].capitalize()

    forecast = [
        {
            "date": day,
            "temp_max_c": round(d["tmax"], 1),
            "temp_min_c": round(d["tmin"], 1),
            "rain_mm": round(d["rain"], 1),
            "rain_probability_pct": round(d["pop"] * 100),
            "et0_mm": None,  # not provided by the free OpenWeather endpoints
            "condition": d["cond"],
        }
        for day, d in sorted(days.items())
    ]
    return {
        "location": {"name": name or f"{lat:.2f}, {lon:.2f}", "latitude": lat, "longitude": lon},
        "current": {
            "observed_at": datetime.fromtimestamp(cur["dt"], timezone.utc).isoformat(),
            "temperature_c": cur["main"]["temp"],
            "humidity_pct": cur["main"]["humidity"],
            "precipitation_mm": cur.get("rain", {}).get("1h", 0.0),
            "wind_speed_kmh": round(cur["wind"]["speed"] * 3.6, 1),
            "condition": cur["weather"][0]["description"].capitalize(),
        },
        "daily": forecast,
        "source": {"provider": "openweather", "name": "OpenWeather", "url": "https://openweathermap.org/"},
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
