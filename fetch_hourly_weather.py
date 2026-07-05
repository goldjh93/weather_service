#!/usr/bin/env python3
"""Fetch today's hourly weather forecast from the Open-Meteo API."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODE_LABELS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def build_url(latitude: float, longitude: float, timezone: str) -> str:
    hourly_variables = [
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation_probability",
        "precipitation",
        "weather_code",
        "wind_speed_10m",
    ]
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(hourly_variables),
        "timezone": timezone,
        "forecast_days": 1,
    }
    return f"{OPEN_METEO_FORECAST_URL}?{urlencode(params)}"


def fetch_json(url: str) -> dict:
    try:
        with urlopen(url, timeout=10) as response:
            return json.load(response)
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Open-Meteo API error: {error.code} {body}") from error
    except URLError as error:
        raise RuntimeError(f"Network error: {error.reason}") from error


def format_value(value, unit: str) -> str:
    if value is None:
        return "-"
    return f"{value}{unit}"


def print_hourly_weather(data: dict) -> None:
    hourly = data["hourly"]
    units = data.get("hourly_units", {})

    print(f"Timezone: {data.get('timezone', 'unknown')}")
    print(
        "Time              "
        "Temp      "
        "Humidity  "
        "RainProb  "
        "Precip    "
        "Wind      "
        "Weather"
    )
    print("-" * 90)

    rows = zip(
        hourly["time"],
        hourly["temperature_2m"],
        hourly["relative_humidity_2m"],
        hourly["precipitation_probability"],
        hourly["precipitation"],
        hourly["wind_speed_10m"],
        hourly["weather_code"],
    )

    for time_text, temp, humidity, rain_prob, precip, wind, weather_code in rows:
        time_label = datetime.fromisoformat(time_text).strftime("%Y-%m-%d %H:%M")
        weather_label = WEATHER_CODE_LABELS.get(weather_code, f"WMO {weather_code}")
        print(
            f"{time_label:<17} "
            f"{format_value(temp, units.get('temperature_2m', '')):<9} "
            f"{format_value(humidity, units.get('relative_humidity_2m', '')):<9} "
            f"{format_value(rain_prob, units.get('precipitation_probability', '')):<9} "
            f"{format_value(precip, units.get('precipitation', '')):<9} "
            f"{format_value(wind, units.get('wind_speed_10m', '')):<9} "
            f"{weather_label}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch today's weather at 1-hour intervals from Open-Meteo."
    )
    parser.add_argument("--latitude", type=float, default=37.5665, help="Latitude")
    parser.add_argument("--longitude", type=float, default=126.9780, help="Longitude")
    parser.add_argument(
        "--timezone",
        default="Asia/Seoul",
        help='IANA timezone name, or "auto" to let Open-Meteo infer it',
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    url = build_url(args.latitude, args.longitude, args.timezone)
    data = fetch_json(url)
    print_hourly_weather(data)


if __name__ == "__main__":
    main()
