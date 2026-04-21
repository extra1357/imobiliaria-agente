from http.server import BaseHTTPRequestHandler
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from groq import Groq
from tools.property_search_advanced import buscar_imoveis
from tools.price_analysis import preco_medio_cidade
from tools.schedule_visit import agendar_visita
from tools.broker_info import info_corretores

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def decidir_acao(texto: str) -> dict:
    prompt = f"""
Você é um assistente de imóveis. Analise a mensagem do usuário e retorne APENAS um JSON com a ação e os parâmetros extraídos.

Ações disponíveis:
- buscar: buscar imóveis (extraia cidade, tipo, quartos, finalidade, preco_max)
- preco_medio: preço médio em uma cidade
- agendar: agendar visita
- corretores: informações sobre corretores
- sem_filtro: mensagem muito genérica sem informações suficientes

Regras:
- Se o usuário não informar cidade nem tipo nem quartos nem finalidade nem preço, use "sem_filtro"
- Se informar apenas tipo sem cidade, use "sem_filtro"
- Extraia cidade, tipo de imóvel, quartos, finalidade (venda/aluguel), preco_max quando presentes

Retorne APENAS JSON, exemplo:
{{"acao": "buscar", "cidade": "Salto", "tipo": "casa", "quartos": 3, "finalidade": "venda", "preco_max": 400000}}

Mensagem: {texto}
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.choices[0].message.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except:
        return {"acao": "sem_filtro"}

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length))
        texto = body.get('texto', '')

        acao = decidir_acao(texto)

        if acao.get("acao") == "agendar":
            resultado = agendar_visita(texto)
        elif acao.get("acao") == "preco_medio":
            resultado = preco_medio_cidade(texto)
        elif acao.get("acao") == "corretores":
            resultado = info_corretores(texto)
        elif acao.get("acao") == "sem_filtro":
            resultado = json.dumps({"tipo": "texto", "conteudo": "Em qual cidade você procura? Me diga a cidade e posso te mostrar as opções disponíveis! 😊"})
        else:
            resultado = buscar_imoveis(
                texto=texto,
                cidade=acao.get("cidade"),
                tipo=acao.get("tipo"),
                quartos=acao.get("quartos"),
                finalidade=acao.get("finalidade"),
                preco_max=acao.get("preco_max")
            )

        if isinstance(resultado, str):
            try:
                resultado = json.loads(resultado)
            except:
                resultado = {"tipo": "texto", "conteudo": resultado}

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(resultado, ensure_ascii=False).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
