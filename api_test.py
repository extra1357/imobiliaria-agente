from http.server import BaseHTTPRequestHandler
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

errors = []

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception as e:
    errors.append(f"dotenv: {e}")

try:
    from groq import Groq
except Exception as e:
    errors.append(f"groq: {e}")

try:
    from core.db import get_connection
except Exception as e:
    errors.append(f"db: {e}")

try:
    from tools.property_search_advanced import buscar_imoveis
except Exception as e:
    errors.append(f"buscar_imoveis: {e}")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"errors": errors, "status": "ok" if not errors else "fail"}).encode())
