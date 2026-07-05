#!/usr/bin/env python3
"""Plot today's hourly temperature from Open-Meteo and save it as an image."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from fetch_hourly_weather import build_url, fetch_json


def plot_temperature(data: dict, output_path: Path, location_label: str) -> None:
    import matplotlib

    matplotlib.use("Agg")

    import matplotlib.pyplot as plt

    hourly = data["hourly"]
    units = data.get("hourly_units", {})
    times = [datetime.fromisoformat(value) for value in hourly["time"]]
    temperatures = hourly["temperature_2m"]
    temperature_unit = units.get("temperature_2m", "C")

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(times, temperatures, marker="o", linewidth=2, color="#d9480f")
    ax.fill_between(times, temperatures, min(temperatures), color="#ffe8cc", alpha=0.7)

    ax.set_title(f"Today's Hourly Temperature - {location_label}")
    ax.set_xlabel("Time")
    ax.set_ylabel(f"Temperature ({temperature_unit})")
    ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.5)

    ax.set_xticks(times[::2])
    ax.set_xticklabels([time.strftime("%H:%M") for time in times[::2]], rotation=45)

    min_temp = min(temperatures)
    max_temp = max(temperatures)
    ax.annotate(
        f"Min {min_temp}{temperature_unit}",
        xy=(times[temperatures.index(min_temp)], min_temp),
        xytext=(0, -28),
        textcoords="offset points",
        ha="center",
        arrowprops={"arrowstyle": "->", "color": "#495057"},
    )
    ax.annotate(
        f"Max {max_temp}{temperature_unit}",
        xy=(times[temperatures.index(max_temp)], max_temp),
        xytext=(0, 24),
        textcoords="offset points",
        ha="center",
        arrowprops={"arrowstyle": "->", "color": "#495057"},
    )

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Save a matplotlib chart of today's hourly temperature."
    )
    parser.add_argument("--latitude", type=float, default=37.5665, help="Latitude")
    parser.add_argument("--longitude", type=float, default=126.9780, help="Longitude")
    parser.add_argument("--timezone", default="Asia/Seoul", help="IANA timezone name")
    parser.add_argument("--location", default="Seoul", help="Label shown in the chart")
    parser.add_argument(
        "--output",
        default="today_temperature.png",
        help="Output image path",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    url = build_url(args.latitude, args.longitude, args.timezone)
    data = fetch_json(url)
    output_path = Path(args.output)
    plot_temperature(data, output_path, args.location)
    print(f"Saved graph to {output_path.resolve()}")


if __name__ == "__main__":
    main()
