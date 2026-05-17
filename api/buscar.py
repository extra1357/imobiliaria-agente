from http.server import BaseHTTPRequestHandler
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from groq import Groq
from core.memory import get_session, update_session
from tools.intent_router import rotear_intencao
from tools.property_search_advanced import buscar_imoveis, buscar_similares
from tools.lead_capture import salvar_lead
from tools.broker_info import info_corretores

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
Você é Sofia, consultora imobiliária virtual da Imobiliária Perto.
Seu objetivo é ajudar clientes a encontrar o imóvel ideal com uma conversa natural e calorosa.

REGRAS DE OURO:
1. NUNCA busque imóveis sem saber ao menos a cidade desejada.
2. Ao apresentar imóveis, descreva-os de forma envolvente e humana — nunca como lista técnica.
3. Se não houver imóveis, ofereça similares ou capture o contato para avisar quando disponível.
4. SEMPRE que não houver imóveis, peça nome e telefone para entrar em contato.
5. Colete nome e telefone um de cada vez, de forma natural.
6. Mantenha foco imobiliário. Redirecione gentilmente assuntos fora do escopo.

TOM DE VOZ:
- Caloroso, entusiasmado, profissional.
- Mensagens curtas, no máximo 3 parágrafos.
- Termine sempre com uma pergunta ou próximo passo claro.
"""

def chamar_llm(msgs: list) -> str:
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=msgs,
        temperature=0.7,
        max_tokens=600,
    )
    return completion.choices[0].message.content.strip()


def orquestrar(texto: str, session_id: str) -> dict:
    session = get_session(session_id)
    perfil = session.get("perfil", {})
    historico = session.get("historico", [])

    perfil = _atualizar_perfil(perfil, texto)
    intencao = rotear_intencao(texto)

    # ── Contexto base ────────────────────────────────────────────────────────
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    if perfil:
        msgs.append({"role": "system", "content": f"Perfil do cliente: {json.dumps(perfil, ensure_ascii=False)}"})
    for msg in historico[-8:]:
        msgs.append(msg)

    # ── Intenção: buscar imóveis ──────────────────────────────────────────────
    if intencao == "buscar_imoveis":
        cidade = perfil.get("cidade") or _extrair_cidade(texto)

        if not cidade:
            msgs.append({"role": "user", "content": texto})
            msgs.append({"role": "system", "content": "O cliente não informou a cidade. Pergunte de forma calorosa em qual cidade está procurando."})
            resposta = chamar_llm(msgs)
            _salvar(session, historico, texto, resposta, session_id)
            return {"mensagem_sofia": resposta}

        perfil["cidade"] = cidade
        session["perfil"] = perfil

        resultado_raw = buscar_imoveis(
            cidade=cidade,
            tipo=perfil.get("tipo") or _extrair_tipo(texto),
            quartos=perfil.get("quartos"),
            preco_max=perfil.get("preco_max"),
            texto=texto,
        )

        try:
            resultado = json.loads(resultado_raw)
        except Exception:
            resultado = {"tipo": "texto", "conteudo": resultado_raw}

        if resultado.get("tipo") == "imoveis" and resultado.get("total", 0) > 0:
            imoveis = resultado["imoveis"]
            descricao = _formatar_imoveis(imoveis)
            msgs.append({"role": "system", "content": f"Imóveis encontrados:\n{descricao}"})
            msgs.append({"role": "user", "content": texto})
            msgs.append({"role": "system", "content": (
                "Apresente os imóveis de forma envolvente e natural. "
                "Destaque os pontos mais atrativos de cada um. "
                "Pergunte qual deles despertou mais interesse ou se quer agendar uma visita."
            )})
        else:
            # Tenta similares
            similares_raw = buscar_similares(cidade_original=cidade, tipo=perfil.get("tipo"))
            try:
                similares = json.loads(similares_raw)
            except Exception:
                similares = {}

            if similares.get("tipo") == "imoveis" and similares.get("total", 0) > 0:
                descricao = _formatar_imoveis(similares["imoveis"])
                msgs.append({"role": "system", "content": f"Não há exatamente o que o cliente pediu, mas há similares:\n{descricao}"})
                msgs.append({"role": "user", "content": texto})
                msgs.append({"role": "system", "content": (
                    "Explique com empatia que não há imóveis exatamente como pedido, "
                    "mas apresente os similares de forma entusiasmada. "
                    "Pergunte se algum desperta interesse."
                )})
            else:
                msgs.append({"role": "user", "content": texto})
                msgs.append({"role": "system", "content": (
                    "Não há imóveis disponíveis com essas características no momento. "
                    "Explique com empatia. "
                    f"{'Peça o nome do cliente.' if not perfil.get('nome') else 'Peça o telefone para avisar quando surgir algo.' if not perfil.get('telefone') else 'Confirme que vai entrar em contato assim que surgir algo.'}"
                )})

    # ── Intenção: agendar visita ──────────────────────────────────────────────
    elif intencao == "agendar_visita":
        nome = perfil.get("nome")
        telefone = perfil.get("telefone")
        data_visita = perfil.get("data_visita")

        if not nome:
            msgs.append({"role": "user", "content": texto})
            msgs.append({"role": "system", "content": "Cliente quer agendar visita. Peça o nome completo de forma calorosa."})
        elif not telefone:
            msgs.append({"role": "user", "content": texto})
            msgs.append({"role": "system", "content": f"Cliente se chama {nome}. Peça o telefone para contato."})
        elif not data_visita:
            msgs.append({"role": "user", "content": texto})
            msgs.append({"role": "system", "content": f"Temos nome e telefone. Peça a data preferida para a visita."})
        else:
            salvar_lead(nome=nome, telefone=telefone, interesse="agendamento", cidade=perfil.get("cidade",""))
            msgs.append({"role": "user", "content": texto})
            msgs.append({"role": "system", "content": f"Confirme o agendamento para {nome} no dia {data_visita}. Seja entusiasmado e profissional."})

    # ── Intenção: corretores ──────────────────────────────────────────────────
    elif intencao == "corretores":
        try:
            corretores = info_corretores()
            msgs.append({"role": "system", "content": f"Corretores disponíveis: {json.dumps(corretores, ensure_ascii=False)}"})
        except Exception:
            pass
        msgs.append({"role": "user", "content": texto})

    # ── Captura de lead ───────────────────────────────────────────────────────
    elif intencao == "capturar_lead":
        if perfil.get("nome") and perfil.get("telefone"):
            try:
                salvar_lead(nome=perfil["nome"], telefone=perfil["telefone"],
                            interesse=texto, cidade=perfil.get("cidade",""))
            except Exception:
                pass
        msgs.append({"role": "user", "content": texto})

    # ── Fallback ──────────────────────────────────────────────────────────────
    else:
        msgs.append({"role": "user", "content": texto})

    session["perfil"] = perfil
    resposta = chamar_llm(msgs)
    _salvar(session, historico, texto, resposta, session_id)
    return {"mensagem_sofia": resposta}


def _formatar_imoveis(imoveis: list) -> str:
    linhas = []
    for i, im in enumerate(imoveis, 1):
        preco = f"R$ {im['preco']:,.0f}".replace(",", ".")
        linhas.append(
            f"{i}. {im['tipo'].title()} em {im['bairro'] or im['cidade']} — "
            f"{im['quartos']} quartos, {im.get('metragem',0):.0f}m², {preco}. "
            f"{im.get('descricao','')[:120]}. Link: {im.get('link','')}"
        )
    return "\n".join(linhas)


def _salvar(session, historico, texto, resposta, session_id):
    historico.extend([{"role": "user", "content": texto}, {"role": "assistant", "content": resposta}])
    session["historico"] = historico[-20:]
    update_session(session_id, session)


def _extrair_cidade(texto):
    cidades = ["são paulo","campinas","santos","sorocaba","ribeirão preto",
               "são bernardo","guarulhos","osasco","bauru","jundiaí",
               "salto","itu","indaiatuba"]
    t = texto.lower()
    for c in cidades:
        if c in t: return c.title()
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
    preco = re.search(r"(?:até|ate|por)\s*R?\$?\s*([\d\.]+)\s*(?:mil)?", texto, re.I)
    if preco:
        val = float(preco.group(1).replace(".", ""))
        perfil["preco_max"] = val * 1000 if val < 10000 else val
    cidade = _extrair_cidade(texto)
    if cidade: perfil["cidade"] = cidade
    tipo = _extrair_tipo(texto)
    if tipo: perfil["tipo"] = tipo
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
