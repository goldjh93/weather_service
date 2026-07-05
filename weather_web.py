#!/usr/bin/env python3
"""Run a small weather search web page backed by Open-Meteo."""

from __future__ import annotations

import argparse
import html
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

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


def weather_rows(data: dict) -> list[dict]:
    hourly = data["hourly"]
    rows = []
    for index, time_text in enumerate(hourly["time"]):
        weather_code = hourly["weather_code"][index]
        rows.append(
            {
                "time": datetime.fromisoformat(time_text),
                "temperature": hourly["temperature_2m"][index],
                "humidity": hourly["relative_humidity_2m"][index],
                "rain_probability": hourly["precipitation_probability"][index],
                "precipitation": hourly["precipitation"][index],
                "wind_speed": hourly["wind_speed_10m"][index],
                "weather": WEATHER_CODE_LABELS.get(weather_code, f"WMO {weather_code}"),
            }
        )
    return rows


def render_temperature_svg(rows: list[dict], temperature_unit: str) -> str:
    width = 1040
    height = 430
    left = 58
    right = 24
    top = 28
    bottom = 54
    chart_width = width - left - right
    chart_height = height - top - bottom
    temperatures = [row["temperature"] for row in rows]
    min_temp = min(temperatures)
    max_temp = max(temperatures)
    padding = max((max_temp - min_temp) * 0.12, 1)
    y_min = min_temp - padding
    y_max = max_temp + padding
    span = y_max - y_min

    def point(index: int, temp: float) -> tuple[float, float]:
        x = left + (chart_width * index / (len(rows) - 1))
        y = top + chart_height - ((temp - y_min) / span * chart_height)
        return x, y

    points = [point(index, temp) for index, temp in enumerate(temperatures)]
    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    area_points = (
        f"{left},{top + chart_height} "
        + polyline
        + f" {left + chart_width},{top + chart_height}"
    )
    y_ticks = [y_min + ((y_max - y_min) * index / 4) for index in range(5)]
    grid = "\n".join(
        f"""
        <g>
          <line x1="{left}" y1="{top + chart_height - ((tick - y_min) / span * chart_height):.1f}" x2="{left + chart_width}" y2="{top + chart_height - ((tick - y_min) / span * chart_height):.1f}" />
          <text x="{left - 10}" y="{top + chart_height - ((tick - y_min) / span * chart_height) + 4:.1f}" text-anchor="end">{tick:.1f}{html.escape(temperature_unit)}</text>
        </g>
        """
        for tick in y_ticks
    )
    hour_labels = "\n".join(
        f"""
        <g>
          <line x1="{points[index][0]:.1f}" y1="{top + chart_height}" x2="{points[index][0]:.1f}" y2="{top + chart_height + 6}" />
          <text x="{points[index][0]:.1f}" y="{top + chart_height + 26}" text-anchor="middle">{rows[index]["time"].strftime("%H")}</text>
        </g>
        """
        for index in range(0, len(rows), 3)
    )
    markers = "\n".join(
        f"""
        <circle cx="{x:.1f}" cy="{y:.1f}" r="4">
          <title>{rows[index]["time"].strftime("%H:%M")} - {temperatures[index]}{html.escape(temperature_unit)}</title>
        </circle>
        """
        for index, (x, y) in enumerate(points)
    )

    return f"""
    <svg class="temperature-chart" viewBox="0 0 {width} {height}" role="img" aria-label="오늘 시간별 기온 그래프">
      <rect x="0" y="0" width="{width}" height="{height}" rx="8" />
      <g class="grid">{grid}</g>
      <g class="axis">
        <line x1="{left}" y1="{top + chart_height}" x2="{left + chart_width}" y2="{top + chart_height}" />
        {hour_labels}
      </g>
      <polygon class="area" points="{area_points}" />
      <polyline class="line" points="{polyline}" />
      <g class="markers">{markers}</g>
      <text class="x-label" x="{left + chart_width / 2}" y="{height - 10}" text-anchor="middle">Hour</text>
    </svg>
    """


def render_page(
    query: str = "",
    location: dict | None = None,
    forecast: dict | None = None,
    error: str | None = None,
) -> str:
    escaped_query = html.escape(query)
    content = ""

    if error:
        content = f"""
        <section class="status error">
          <strong>검색 실패</strong>
          <span>{html.escape(error)}</span>
        </section>
        """
    elif location and forecast:
        rows = weather_rows(forecast)
        units = forecast.get("hourly_units", {})
        temp_unit = units.get("temperature_2m", "C")
        humidity_unit = units.get("relative_humidity_2m", "%")
        rain_prob_unit = units.get("precipitation_probability", "%")
        precip_unit = units.get("precipitation", "mm")
        wind_unit = units.get("wind_speed_10m", "km/h")
        temps = [row["temperature"] for row in rows]
        current = rows[min(datetime.now().hour, len(rows) - 1)]
        label = html.escape(location_label(location))
        timezone = html.escape(location.get("timezone", forecast.get("timezone", "")))
        chart_svg = render_temperature_svg(rows, temp_unit)
        table_rows = "\n".join(
            f"""
            <tr>
              <td>{row["time"].strftime("%H:%M")}</td>
              <td>{row["temperature"]}{html.escape(temp_unit)}</td>
              <td>{row["humidity"]}{html.escape(humidity_unit)}</td>
              <td>{row["rain_probability"]}{html.escape(rain_prob_unit)}</td>
              <td>{row["precipitation"]}{html.escape(precip_unit)}</td>
              <td>{row["wind_speed"]}{html.escape(wind_unit)}</td>
              <td>{html.escape(row["weather"])}</td>
            </tr>
            """
            for row in rows
        )
        content = f"""
        <section class="summary-band">
          <div>
            <p class="eyebrow">오늘 날씨</p>
            <h2>{label}</h2>
            <p class="muted">시간대: {timezone}</p>
          </div>
          <dl class="metrics">
            <div>
              <dt>현재 기온</dt>
              <dd>{current["temperature"]}{html.escape(temp_unit)}</dd>
            </div>
            <div>
              <dt>최저 / 최고</dt>
              <dd>{min(temps)} / {max(temps)}{html.escape(temp_unit)}</dd>
            </div>
            <div>
              <dt>강수 확률</dt>
              <dd>{current["rain_probability"]}{html.escape(rain_prob_unit)}</dd>
            </div>
            <div>
              <dt>상태</dt>
              <dd>{html.escape(current["weather"])}</dd>
            </div>
          </dl>
        </section>

        <section class="chart-section">
          <h2>시간별 기온 그래프</h2>
          {chart_svg}
        </section>

        <section class="table-section">
          <h2>시간별 상세 예보</h2>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>시간</th>
                  <th>기온</th>
                  <th>습도</th>
                  <th>강수 확률</th>
                  <th>강수량</th>
                  <th>풍속</th>
                  <th>날씨</th>
                </tr>
              </thead>
              <tbody>{table_rows}</tbody>
            </table>
          </div>
        </section>
        """

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Open-Meteo 날씨 검색</title>
  <style>
    :root {{
      --bg: #f7f7f2;
      --ink: #202124;
      --muted: #666f7a;
      --line: #d8ddd4;
      --panel: #ffffff;
      --accent: #0f766e;
      --accent-dark: #115e59;
      --warn-bg: #fff4e6;
      --warn-line: #ffc078;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    header {{
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }}
    .container {{
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
    }}
    .topbar {{
      padding: 28px 0 24px;
    }}
    h1, h2, p {{ margin: 0; }}
    h1 {{
      font-size: 30px;
      line-height: 1.2;
      letter-spacing: 0;
    }}
    .lead {{
      margin-top: 8px;
      color: var(--muted);
      line-height: 1.5;
    }}
    .search-band {{
      padding: 22px 0;
      border-bottom: 1px solid var(--line);
      background: #eef6f4;
    }}
    form {{
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
      align-items: center;
    }}
    input[type="search"] {{
      width: 100%;
      min-height: 48px;
      border: 1px solid #b8c7c3;
      border-radius: 6px;
      padding: 0 14px;
      font-size: 16px;
      background: #fff;
      color: var(--ink);
    }}
    button {{
      min-height: 48px;
      border: 0;
      border-radius: 6px;
      padding: 0 18px;
      font-size: 16px;
      font-weight: 700;
      color: #fff;
      background: var(--accent);
      cursor: pointer;
    }}
    button:hover {{ background: var(--accent-dark); }}
    main {{ padding: 28px 0 44px; }}
    .summary-band {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(360px, 1.4fr);
      gap: 24px;
      align-items: start;
      padding: 24px 0 30px;
      border-bottom: 1px solid var(--line);
    }}
    .eyebrow {{
      margin-bottom: 6px;
      color: var(--accent-dark);
      font-size: 13px;
      font-weight: 800;
    }}
    .summary-band h2, .chart-section h2, .table-section h2 {{
      font-size: 22px;
      line-height: 1.25;
      letter-spacing: 0;
    }}
    .muted {{
      margin-top: 8px;
      color: var(--muted);
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin: 0;
    }}
    .metrics div {{
      min-height: 88px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      background: var(--panel);
    }}
    dt {{
      color: var(--muted);
      font-size: 13px;
    }}
    dd {{
      margin: 8px 0 0;
      font-size: 20px;
      font-weight: 800;
      overflow-wrap: anywhere;
    }}
    .chart-section, .table-section {{
      padding: 30px 0 0;
    }}
    .temperature-chart {{
      display: block;
      width: 100%;
      height: auto;
      margin-top: 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
    }}
    .temperature-chart rect {{
      fill: #fff;
    }}
    .temperature-chart .grid line {{
      stroke: #dde3df;
      stroke-dasharray: 4 6;
    }}
    .temperature-chart .grid text, .temperature-chart .axis text, .temperature-chart .x-label {{
      fill: #65707a;
      font-size: 13px;
    }}
    .temperature-chart .axis line {{
      stroke: #9aa6a1;
    }}
    .temperature-chart .area {{
      fill: #d6f3ee;
      opacity: 0.78;
    }}
    .temperature-chart .line {{
      fill: none;
      stroke: #0f766e;
      stroke-width: 4;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}
    .temperature-chart .markers circle {{
      fill: #fff;
      stroke: #0f766e;
      stroke-width: 3;
    }}
    .table-wrap {{
      margin-top: 14px;
      overflow-x: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 760px;
    }}
    th, td {{
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      white-space: nowrap;
    }}
    th {{
      background: #f0f3ef;
      font-size: 13px;
      color: #3f474f;
    }}
    tr:last-child td {{ border-bottom: 0; }}
    .status {{
      border: 1px solid var(--warn-line);
      border-radius: 8px;
      padding: 16px;
      background: var(--warn-bg);
      display: grid;
      gap: 6px;
    }}
    @media (max-width: 820px) {{
      form, .summary-band, .metrics {{
        grid-template-columns: 1fr;
      }}
      button {{
        width: 100%;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="container topbar">
      <h1>Open-Meteo 날씨 검색</h1>
      <p class="lead">도시나 지역명을 입력하면 오늘의 시간별 날씨와 기온 그래프를 불러옵니다.</p>
    </div>
  </header>
  <section class="search-band">
    <div class="container">
      <form method="get" action="/">
        <input
          type="search"
          name="location"
          value="{escaped_query}"
          placeholder="예: Seoul, Busan, New York, Tokyo"
          aria-label="위치 검색"
          required
        >
        <button type="submit">검색</button>
      </form>
    </div>
  </section>
  <main class="container">
    {content}
  </main>
</body>
</html>"""


class WeatherRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/":
            self.send_error(404)
            return

        query = parse_qs(parsed.query).get("location", [""])[0].strip()
        if not query:
            self.send_html(render_page())
            return

        try:
            location = geocode_location(query)
            label = location_label(location)
            forecast_url = build_url(
                float(location["latitude"]),
                float(location["longitude"]),
                location.get("timezone", "auto"),
            )
            forecast = fetch_json(forecast_url)
            self.send_html(
                render_page(
                    query=query,
                    location=location,
                    forecast=forecast,
                )
            )
        except Exception as exc:
            self.send_html(render_page(query=query, error=str(exc)), status=500)

    def send_html(self, body: str, status: int = 200) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the weather search web page.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), WeatherRequestHandler)
    print(f"Weather web page running at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
