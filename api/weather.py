from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fetch_hourly_weather import WEATHER_CODE_LABELS, build_url, fetch_json


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


def geocode_location(location: str) -> dict:
    params = {
        "name": location,
        "count": 1,
        "language": "ko",
        "format": "json",
    }
    data = fetch_json(f"{GEOCODING_URL}?{urlencode(params)}")
    results = data.get("results", [])
    if not results:
        raise ValueError(f"No location found for '{location}'.")
    return results[0]


def location_label(location: dict) -> str:
    parts = [
        location.get("name"),
        location.get("admin1"),
        location.get("country"),
    ]
    return ", ".join(part for part in parts if part)


def current_index_for_timezone(timezone: str, row_count: int) -> int:
    try:
        now = datetime.now(ZoneInfo(timezone))
    except ZoneInfoNotFoundError:
        now = datetime.utcnow()
    return min(max(now.hour, 0), row_count - 1)


def build_weather_payload(query: str) -> dict:
    location = geocode_location(query)
    timezone = location.get("timezone", "auto")
    forecast_url = build_url(
        float(location["latitude"]),
        float(location["longitude"]),
        timezone,
    )
    forecast = fetch_json(forecast_url)
    hourly = forecast["hourly"]
    units = forecast.get("hourly_units", {})
    rows = []

    for index, time_text in enumerate(hourly["time"]):
        weather_code = hourly["weather_code"][index]
        rows.append(
            {
                "time": time_text,
                "temperature": hourly["temperature_2m"][index],
                "humidity": hourly["relative_humidity_2m"][index],
                "rainProbability": hourly["precipitation_probability"][index],
                "precipitation": hourly["precipitation"][index],
                "windSpeed": hourly["wind_speed_10m"][index],
                "weather": WEATHER_CODE_LABELS.get(weather_code, f"WMO {weather_code}"),
            }
        )

    temperatures = [row["temperature"] for row in rows]
    current_index = current_index_for_timezone(timezone, len(rows))

    return {
        "query": query,
        "location": {
            "name": location.get("name"),
            "label": location_label(location),
            "country": location.get("country"),
            "admin1": location.get("admin1"),
            "latitude": location.get("latitude"),
            "longitude": location.get("longitude"),
            "timezone": timezone,
        },
        "units": {
            "temperature": units.get("temperature_2m", "C"),
            "humidity": units.get("relative_humidity_2m", "%"),
            "rainProbability": units.get("precipitation_probability", "%"),
            "precipitation": units.get("precipitation", "mm"),
            "windSpeed": units.get("wind_speed_10m", "km/h"),
        },
        "summary": {
            "currentIndex": current_index,
            "minTemperature": min(temperatures),
            "maxTemperature": max(temperatures),
        },
        "rows": rows,
    }
