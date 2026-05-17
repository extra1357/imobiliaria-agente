from http.server import BaseHTTPRequestHandler
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from groq import Groq
from core.memory import get_session, update_session
from tools.intent_router import rotear_intencao
from tools.property_search_advanced import buscar_imoveis
from tools.schedule_visit import listar_imoveis_para_visita, confirmar_agendamento
from tools.lead_capture import salvar_lead
from tools.broker_info import info_corretores

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
Você é Sofia, assistente virtual da Imobiliária Perto.
Seu objetivo é ajudar clientes a encontrar o imóvel ideal, qualificar o interesse
e agendar visitas — sempre de forma simpática, objetiva e humana.

REGRAS DE OURO (Guard Rails):
1. NUNCA busque imóveis sem saber ao menos a cidade desejada.
   → Se faltar a cidade, pergunte antes de qualquer busca.
2. NUNCA confirme um agendamento sem coletar: nome completo, telefone e data preferida.
   → Colete um dado por vez, de forma natural.
3. NUNCA invente imóveis, preços ou informações que não estejam nos dados retornados.
4. Se não souber algo, diga "Vou verificar isso para você" e oriente o cliente.
5. Mantenha o foco imobiliário. Para assuntos fora do escopo, redirecione gentilmente.

TOM DE VOZ:
- Caloroso, profissional, direto ao ponto.
- Use "você" (nunca "tu" ou "senhor/senhora" a menos que o cliente use).
- Mensagens curtas, máximo 3 parágrafos por resposta.
- Termine com uma pergunta ou próximo passo claro.

ESCOPO:
- Busca de imóveis por cidade, tipo, faixa de preço, quartos.
- Informações sobre imóveis listados.
- Agendamento de visitas.
- Informações sobre corretores.
- Captação de leads interessados.
"""

def orquestrar(texto: str, session_id: str) -> dict:
    session = get_session(session_id)
    perfil = session.get("perfil", {})
    historico = session.get("historico", [])

    intencao = rotear_intencao(texto)
    dados_extras = ""
    imoveis = []
    imoveis_agenda = []

    if intencao == "buscar_imoveis":
        cidade = perfil.get("cidade") or _extrair_cidade(texto)
        if not cidade:
            resposta_sofia = (
                "Para encontrar os melhores imóveis para você, preciso saber: "
                "em qual cidade você está procurando? 🏙️"
            )
            _atualizar_historico(session, historico, texto, resposta_sofia, session_id)
            return {"mensagem_sofia": resposta_sofia, "imoveis": []}

        perfil["cidade"] = cidade
        tipo = perfil.get("tipo") or _extrair_tipo(texto)
        imoveis = buscar_imoveis(
            cidade=cidade, tipo=tipo,
            preco_max=perfil.get("preco_max"),
            quartos=perfil.get("quartos"),
        )
        dados_extras = f"Imóveis encontrados:\n{json.dumps(imoveis, ensure_ascii=False, indent=2)}"

    elif intencao == "agendar_visita":
        imoveis_agenda = listar_imoveis_para_visita()
        dados_extras = f"Imóveis disponíveis:\n{json.dumps(imoveis_agenda, ensure_ascii=False, indent=2)}"

        nome, telefone, data_visita = perfil.get("nome"), perfil.get("telefone"), perfil.get("data_visita")

        if not nome:
            r = "Ótimo! Para agendar a visita, preciso do seu nome completo. Como posso chamar você? 😊"
            _atualizar_historico(session, historico, texto, r, session_id)
            return {"mensagem_sofia": r, "imoveis": imoveis_agenda}
        if not telefone:
            r = f"Perfeito, {nome}! Qual é o melhor número de telefone para contato? 📱"
            _atualizar_historico(session, historico, texto, r, session_id)
            return {"mensagem_sofia": r, "imoveis": imoveis_agenda}
        if not data_visita:
            r = "Que data você prefere para a visita? (ex: próxima terça, 25/06) 📅"
            _atualizar_historico(session, historico, texto, r, session_id)
            return {"mensagem_sofia": r, "imoveis": imoveis_agenda}

        confirmacao = confirmar_agendamento(nome=nome, telefone=telefone, data=data_visita)
        dados_extras = f"Resultado: {confirmacao}"

    elif intencao == "corretores":
        dados_extras = f"Corretores:\n{json.dumps(info_corretores(), ensure_ascii=False, indent=2)}"

    elif intencao == "capturar_lead":
        salvar_lead(nome=perfil.get("nome",""), telefone=perfil.get("telefone",""),
                    interesse=texto, cidade=perfil.get("cidade",""))

    perfil = _atualizar_perfil(perfil, texto)
    session["perfil"] = perfil

    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    if perfil:
        msgs.append({"role": "system", "content": f"Perfil: {json.dumps(perfil, ensure_ascii=False)}"})
    if dados_extras:
        msgs.append({"role": "system", "content": dados_extras})
    for msg in historico[-8:]:
        msgs.append(msg)
    msgs.append({"role": "user", "content": texto})

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=msgs,
        temperature=0.7,
        max_tokens=600,
    )
    resposta_sofia = completion.choices[0].message.content.strip()
    _atualizar_historico(session, historico, texto, resposta_sofia, session_id)

    return {
        "mensagem_sofia": resposta_sofia,
        "imoveis": imoveis if intencao == "buscar_imoveis" else imoveis_agenda,
    }


def _atualizar_historico(session, historico, tu, rs, sid):
    historico.extend([{"role": "user", "content": tu}, {"role": "assistant", "content": rs}])
    session["historico"] = historico[-20:]
    update_session(sid, session)

def _extrair_cidade(texto):
    cidades = ["são paulo","campinas","santos","sorocaba","ribeirão preto",
               "são bernardo","guarulhos","osasco","bauru","jundiaí"]
    t = texto.lower()
    for c in cidades:
        if c in t:
            return c.title()
    return None

def _extrair_tipo(texto):
    tipos = {"apartamento":"apartamento","apto":"apartamento","casa":"casa",
             "kitnet":"kitnet","comercial":"comercial","sala":"comercial","terreno":"terreno"}
    t = texto.lower()
    for k, v in tipos.items():
        if k in t: return v
    return None

def _atualizar_perfil(perfil, texto):
    import re
    tel = re.search(r"\(?\d{2}\)?\s*\d{4,5}[-\s]?\d{4}", texto)
    if tel: perfil["telefone"] = tel.group()
    data = re.search(r"\d{1,2}/\d{1,2}(?:/\d{2,4})?", texto)
    if data: perfil["data_visita"] = data.group()
    q = re.search(r"(\d)\s*quarto", texto, re.I)
    if q: perfil["quartos"] = int(q.group(1))
    nm = re.search(r"(?:me chamo|meu nome[eé ]+|sou o|sou a)\s+([A-ZÀ-Ú][a-zà-ú]+(?: [A-ZÀ-Ú][a-zà-ú]+)*)", texto, re.I)
    if nm: perfil["nome"] = nm.group(1)
    return perfil


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
            texto = data.get("texto", "").strip()
            session_id = data.get("session_id", "default")
            if not texto:
                self._responder(400, {"erro": "Campo 'texto' obrigatório."})
                return
            self._responder(200, orquestrar(texto, session_id))
        except Exception as e:
            self._responder(500, {"erro": str(e)})

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def _responder(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
