from coordinates import get_coordinates
from weather import get_weather
from places import get_top_50_attractions
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import os

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        city = qs.get("city", [""])[0]

        if parsed.path.startswith("/api/weather"):
            coords = get_coordinates(city)
            if not coords:
                self.respond({"error": "City not found"})
                return
            lat, lon = coords
            data = get_weather(lat, lon, None)
            self.respond({"city": city, "weather": data})

        elif parsed.path.startswith("/api/places"):
            places = get_top_50_attractions(city, SERPAPI_KEY)
            self.respond({"city": city, "places": places})

        else:
            self.respond({"status": "TravelAI running"})

    def respond(self, data):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
