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
from core.db import get_connection

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def salvar_lead(nome, telefone, email, mensagem, imovel_interesse=None):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO leads (id, nome, telefone, email, mensagem, origem, status, "createdAt", "updatedAt")
            VALUES (gen_random_uuid(), %s, %s, %s, %s, 'chat_ia', 'novo', NOW(), NOW())
        """, (nome, telefone, email or '', mensagem, ))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        return False

def decidir_acao(texto: str, historico: list) -> dict:
    prompt = f"""
Você é Sofia, consultora de imóveis da STR Imobiliária. Analise a mensagem do usuário e retorne APENAS um JSON.

Ações disponíveis:
- buscar: buscar imóveis (extraia cidade, tipo, quartos, finalidade, preco_max)
- preco_medio: SOMENTE quando perguntar explicitamente "preço médio", "quanto custa em média"
- agendar: agendar visita
- corretores: informações sobre corretores
- salvar_lead: quando usuário fornecer nome e telefone para contato
- sem_filtro: mensagem genérica sem informações suficientes

Regras:
- Se informar apenas tipo sem cidade → sem_filtro
- Se o usuário der nome e telefone → salvar_lead com campos nome, telefone, email
- Extraia cidade, tipo, quartos, finalidade (venda/aluguel), preco_max quando presentes

Exemplos:
{{"acao": "buscar", "cidade": "Salto", "tipo": "casa", "quartos": 3, "finalidade": "venda", "preco_max": 400000}}
{{"acao": "salvar_lead", "nome": "João Silva", "telefone": "11999999999", "email": ""}}
{{"acao": "sem_filtro"}}

Mensagem atual: {texto}
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

def gerar_resposta_sofia(texto_usuario: str, imoveis: list, historico: list) -> str:
    imoveis_resumo = ""
    for i, im in enumerate(imoveis[:4], 1):
        imoveis_resumo += f"{i}. {im['tipo']} em {im['cidade']} - {im['bairro'] or 'sem bairro'} - R${im['preco']:,.0f} - {im['quartos']} quartos - {im['metragem']}m²\n"

    msgs = [{"role": "system", "content": """Você é Sofia, consultora de imóveis da STR Imobiliária.
Seu tom é elegante, caloroso e profissional. Você conhece bem o mercado imobiliário.
Comente os imóveis encontrados de forma natural, destaque o melhor custo-benefício,
pergunte sobre as preferências do cliente e ofereça agendar visita ou conectar com corretor.
Seja concisa — máximo 3 linhas. Não liste os imóveis, apenas comente-os pois os cards já aparecem."""}]

    for msg in historico[-6:]:
        msgs.append(msg)

    msgs.append({"role": "user", "content": f"Usuário perguntou: {texto_usuario}\n\nImóveis encontrados:\n{imoveis_resumo}"})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=msgs,
        max_tokens=200
    )
    return response.choices[0].message.content.strip()

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length))
            texto = body.get('texto', '')
            historico = body.get('historico', [])

            acao = decidir_acao(texto, historico)

            if acao.get("acao") == "salvar_lead":
                nome = acao.get("nome", "")
                telefone = acao.get("telefone", "")
                email = acao.get("email", "")
                salvar_lead(nome, telefone, email, texto)
                resultado = {
                    "tipo": "texto",
                    "conteudo": f"Perfeito, {nome}! 😊 Recebi seus dados. Um de nossos corretores vai entrar em contato pelo número {telefone} em breve. Posso te ajudar com mais alguma coisa?"
                }
            elif acao.get("acao") == "agendar":
                res = agendar_visita(texto)
                resultado = json.loads(res) if isinstance(res, str) else res
            elif acao.get("acao") == "preco_medio":
                res = preco_medio_cidade(texto)
                resultado = json.loads(res) if isinstance(res, str) else res
            elif acao.get("acao") == "corretores":
                res = info_corretores(texto)
                resultado = {"tipo": "texto", "conteudo": res}
            elif acao.get("acao") == "sem_filtro":
                resultado = {"tipo": "texto", "conteudo": "Em qual cidade você procura? Me diga a cidade e posso te mostrar as opções disponíveis! 😊"}
            else:
                res = buscar_imoveis(
                    texto=texto,
                    cidade=acao.get("cidade"),
                    tipo=acao.get("tipo"),
                    quartos=acao.get("quartos"),
                    finalidade=acao.get("finalidade"),
                    preco_max=acao.get("preco_max")
                )
                if isinstance(res, str):
                    res = json.loads(res)

                if res.get("tipo") == "imoveis" and res.get("imoveis"):
                    comentario = gerar_resposta_sofia(texto, res["imoveis"], historico)
                    res["texto_intro"] = comentario
                resultado = res

        except Exception as e:
            resultado = {"tipo": "texto", "conteudo": f"Erro: {str(e)}"}

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
