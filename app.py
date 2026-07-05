from __future__ import annotations

from flask import Flask, jsonify, request, send_from_directory

from api.weather import build_weather_payload


app = Flask(__name__, static_folder=None)


@app.get("/")
def home():
    return send_from_directory(app.root_path, "index.html")


@app.get("/api")
def weather_api():
    location = request.args.get("location", "").strip()
    if not location:
        return jsonify({"error": "location query parameter is required"}), 400

    try:
        return jsonify(build_weather_payload(location))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.get("/healthz")
def healthz():
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
