from http.server import BaseHTTPRequestHandler
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

errors = []

try:
    import psycopg2
except Exception as e:
    errors.append(f"psycopg2: {str(e)}")

try:
    from groq import Groq
except Exception as e:
    errors.append(f"groq: {str(e)}")

try:
    from core.db import get_connection
except Exception as e:
    errors.append(f"db: {str(e)}")

try:
    from tools.property_search_advanced import buscar_imoveis
except Exception as e:
    errors.append(f"buscar_imoveis: {str(e)}")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"errors": errors, "status": "ok" if not errors else "fail"}).encode())
    def do_GET(self):
        self.do_POST()
