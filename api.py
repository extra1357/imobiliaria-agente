from http.server import BaseHTTPRequestHandler
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.intent_router import detectar_intencao
from tools.property_search_advanced import buscar_imoveis
from tools.price_analysis import preco_medio_cidade
from tools.schedule_visit import agendar_visita
from tools.broker_info import info_corretores

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length))
        texto = body.get('texto', '')
        intencao = detectar_intencao(texto)
        if intencao == 'agendar':
            resultado = agendar_visita(texto)
        elif intencao == 'preco_medio':
            resultado = preco_medio_cidade(texto)
        elif intencao == 'corretores':
            resultado = info_corretores(texto)
        else:
            resultado = buscar_imoveis(texto=texto)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({'resultado': resultado}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
