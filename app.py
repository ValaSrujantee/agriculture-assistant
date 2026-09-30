"""
Smart Agriculture Assistant - Web Server & REST API Backend
Supports both standard Python HTTP server (zero-dependency instant run)
and FastAPI / ASGI server.
"""

import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from ml_engine import SmartAgriAdvisor
from knowledge_base import CROP_DATABASE, SOIL_DATABASE

advisor = SmartAgriAdvisor()
PORT = int(os.environ.get("PORT", 8000))
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


class AgricultureAPIHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def _send_json_response(self, data, status=200):
        response_bytes = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == "/api/crops":
            self._send_json_response({"status": "success", "crops": CROP_DATABASE})
            return
        elif path == "/api/soils":
            self._send_json_response({"status": "success", "soils": SOIL_DATABASE})
            return
        elif path == "/api/search":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            q = query_params.get("q", [""])[0]
            results = advisor.search_knowledge_base(q)
            self._send_json_response({"status": "success", "results": results})
            return

        # Serve static files or index.html
        if path == "/" or not os.path.exists(os.path.join(STATIC_DIR, path.lstrip("/"))):
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8")

        try:
            body = json.loads(post_data) if post_data else {}
        except json.JSONDecodeError:
            self._send_json_response({"error": "Invalid JSON body"}, status=400)
            return

        if path == "/api/recommend":
            try:
                nitrogen = float(body.get("nitrogen", 70))
                phosphorus = float(body.get("phosphorus", 45))
                potassium = float(body.get("potassium", 50))
                temperature = float(body.get("temperature", 25))
                rainfall = float(body.get("rainfall", 800))
                ph = float(body.get("ph", 6.5))
                soil_type = str(body.get("soil_type", "Alluvial"))
                season = str(body.get("season", "Kharif"))

                recommendations = advisor.evaluate_crop_suitability(
                    nitrogen=nitrogen,
                    phosphorus=phosphorus,
                    potassium=potassium,
                    temperature=temperature,
                    rainfall=rainfall,
                    ph=ph,
                    soil_type=soil_type,
                    season=season
                )
                soil_analysis = advisor.analyze_soil_health(nitrogen, phosphorus, potassium, ph, soil_type)

                self._send_json_response({
                    "status": "success",
                    "inputs": {
                        "nitrogen": nitrogen,
                        "phosphorus": phosphorus,
                        "potassium": potassium,
                        "temperature": temperature,
                        "rainfall": rainfall,
                        "ph": ph,
                        "soil_type": soil_type,
                        "season": season
                    },
                    "recommendations": recommendations,
                    "soil_analysis": soil_analysis
                })
            except Exception as e:
                self._send_json_response({"error": str(e)}, status=500)
            return

        elif path == "/api/diagnose":
            crop_name = body.get("crop", "all")
            symptoms = body.get("symptoms", "")
            diagnosis = advisor.diagnose_crop_issue(crop_name, symptoms)
            self._send_json_response({"status": "success", "diagnosis": diagnosis})
            return

        elif path == "/api/soil-analysis":
            nitrogen = float(body.get("nitrogen", 70))
            phosphorus = float(body.get("phosphorus", 45))
            potassium = float(body.get("potassium", 50))
            ph = float(body.get("ph", 6.5))
            soil_type = str(body.get("soil_type", "Alluvial"))
            soil_analysis = advisor.analyze_soil_health(nitrogen, phosphorus, potassium, ph, soil_type)
            self._send_json_response({"status": "success", "soil_analysis": soil_analysis})
            return

        self._send_json_response({"error": "Endpoint not found"}, status=404)


def run_server():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, AgricultureAPIHandler)
    print("=" * 60)
    print(f"🌱 Smart Agriculture Assistant Server is LIVE!")
    print(f"🔗 Local Web App URL: http://localhost:{PORT}")
    print(f"🌾 Knowledge Base Loaded: {len(CROP_DATABASE)} Crops & {len(SOIL_DATABASE)} Soil Profiles")
    print("=" * 60)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server shutting down gracefully...")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
