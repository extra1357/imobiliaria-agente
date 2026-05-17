from http.server import BaseHTTPRequestHandler
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from groq import Groq
from core.memory import get_session, update_session
from tools.property_search_advanced import buscar_imoveis, buscar_similares, interpretar_busca
from tools.lead_capture import salvar_lead
from tools.broker_info import info_corretores

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

def _carregar_contexto_db(perfil: dict) -> str:
    """Busca imóveis e corretores do banco e formata para o prompt."""
    contexto = ""

    # Corretores disponíveis
    try:
        corretores_raw = json.loads(info_corretores())
        corretores = corretores_raw.get("corretores", [])
        if corretores:
            linhas = [f"- {c['nome']} | CRECI: {c['creci']} | Tel: {c['telefone']}" for c in corretores]
            contexto += "CORRETORES DISPONÍVEIS:\n" + "\n".join(linhas) + "\n\n"
    except Exception as e:
        contexto += f"(erro ao carregar corretores: {e})\n\n"

    # Imóveis do banco
    cidade    = perfil.get("cidade")
    tipo      = perfil.get("tipo")
    quartos   = perfil.get("quartos")
    preco_max = perfil.get("preco_max")
    finalidade = perfil.get("finalidade")

    if cidade or tipo or quartos or preco_max:
        try:
            resultado = json.loads(buscar_imoveis(
                cidade=cidade, tipo=tipo, quartos=quartos,
                preco_max=preco_max, finalidade=finalidade, limit=5
            ))

            if resultado.get("tipo") == "imoveis" and resultado.get("imoveis"):
                imoveis = resultado["imoveis"]
                linhas = []
                for im in imoveis:
                    preco = f"R$ {im['preco']:,.0f}".replace(",", ".")
                    linhas.append(
                        f"• {im['tipo'].title()} em {im['bairro'] or im['cidade']} | "
                        f"{im['quartos']}q {im['banheiros']}bh {im['vagas']}vg | "
                        f"{im['metragem']:.0f}m² | {preco} | "
                        f"Link: {im['link']}"
                    )
                contexto += f"IMÓVEIS ENCONTRADOS ({len(imoveis)}):\n" + "\n".join(linhas) + "\n\n"

            else:
                # Tenta similares
                if cidade:
                    sim = json.loads(buscar_similares(cidade, tipo, preco_max, finalidade))
                    if sim.get("tipo") == "imoveis" and sim.get("imoveis"):
                        imoveis = sim["imoveis"]
                        linhas = []
                        for im in imoveis:
                            preco = f"R$ {im['preco']:,.0f}".replace(",", ".")
                            linhas.append(
                                f"• {im['tipo'].title()} em {im['bairro'] or im['cidade']} | "
                                f"{im['quartos']}q | {im['metragem']:.0f}m² | {preco} | "
                                f"Link: {im['link']}"
                            )
                        aviso = sim.get("aviso", "Imóveis em cidades próximas:")
                        contexto += f"IMÓVEIS PRÓXIMOS ({aviso}):\n" + "\n".join(linhas) + "\n\n"
                    else:
                        contexto += "IMÓVEIS: Nenhum encontrado na cidade ou arredores.\n\n"
                else:
                    contexto += "IMÓVEIS: Cidade não informada ainda.\n\n"
        except Exception as e:
            contexto += f"(erro ao buscar imóveis: {e})\n\n"
    else:
        contexto += "IMÓVEIS: Aguardando cliente informar cidade/tipo/quartos.\n\n"

    return contexto

def _extrair_perfil(historico: list, texto_atual: str) -> dict:
    """Extrai perfil acumulado do cliente a partir do histórico."""
    import re
    perfil = {}
    todo_texto = " ".join(
        m["content"] for m in historico if m["role"] == "user"
    ) + " " + texto_atual

    # Cidade
    cidades = ["são paulo", "campinas", "salto", "sorocaba", "itu", "indaiatuba", "mairinque", "bauru"]
    for c in cidades:
        if c in todo_texto.lower():
            perfil["cidade"] = c.title()
            break

    # Tipo
    for tp in ["apartamento", "casa", "sobrado", "terreno", "comercial"]:
        if tp in todo_texto.lower():
            perfil["tipo"] = tp
            break

    # Finalidade
    if any(p in todo_texto.lower() for p in ["aluguel", "alugar", "locação"]):
        perfil["finalidade"] = "aluguel"
    elif any(p in todo_texto.lower() for p in ["comprar", "compra", "venda"]):
        perfil["finalidade"] = "venda"

    # Quartos
    m = re.search(r"(\d+)\s*quarto", todo_texto.lower())
    if m:
        perfil["quartos"] = int(m.group(1))

    # Preço
    m = re.search(r"(\d+[\.,]?\d*)\s*(mil|k|milhão|milhao)", todo_texto.lower())
    if m:
        val = float(m.group(1).replace(",", "."))
        perfil["preco_max"] = int(val * 1000) if m.group(2) in ["mil", "k"] else int(val * 1_000_000)

    # Nome
    m = re.search(r"(?:me chamo|meu nome[eé ]+|sou o|sou a)\s+([A-ZÀ-Ú][a-zà-ú]+(?:\s[A-ZÀ-Ú][a-zà-ú]+){0,3})", todo_texto, re.I)
    if m:
        perfil["nome"] = m.group(1)

    # Telefone
    m = re.search(r"(\(?\d{2}\)?\s?\d{4,5}[-\s]?\d{4})", todo_texto)
    if m:
        perfil["telefone"] = m.group(1)

    return perfil

def _tentar_salvar_lead(perfil: dict, sessao: dict) -> str | None:
    """Salva lead se tiver nome + telefone e ainda não salvou."""
    if sessao.get("lead_salvo"):
        return None
    nome = perfil.get("nome") or sessao.get("perfil", {}).get("nome")
    telefone = perfil.get("telefone") or sessao.get("perfil", {}).get("telefone")
    if nome and telefone:
        imovel = perfil.get("tipo", "") + " em " + perfil.get("cidade", "")
        salvar_lead(
            nome=nome,
            telefone=telefone,
            imovel_interesse=imovel.strip(" em ") or None,
            mensagem=f"Lead capturado via Sofia Chat"
        )
        return "lead_salvo"
    return None

def orquestrar(texto: str, session_id: str) -> dict:
    sessao = get_session(session_id)
    historico = sessao.get("historico", [])

    # Extrai perfil acumulado
    perfil = _extrair_perfil(historico, texto)

    # Mescla com perfil anterior da sessão
    perfil_anterior = sessao.get("perfil", {})
    perfil_merged = {**perfil_anterior, **{k: v for k, v in perfil.items() if v}}

    # Salva lead se possível
    salvou = _tentar_salvar_lead(perfil_merged, sessao)

    # Carrega contexto real do banco
    contexto_db = _carregar_contexto_db(perfil_merged)

    SYSTEM_PROMPT = f"""Você é Sofia, consultora imobiliária virtual da Imobiliária Perto.
Seu objetivo é ajudar clientes a encontrar o imóvel ideal com uma conversa natural e calorosa.

DADOS REAIS DO BANCO (use SEMPRE esses dados nas respostas):
{contexto_db}

REGRAS:
1. Use APENAS os imóveis listados acima — nunca invente imóveis.
2. Se houver imóveis, descreva-os de forma envolvente mencionando bairro, quartos, metragem e preço.
3. Sempre inclua o link do imóvel quando apresentar.
4. Se não houver imóveis, peça nome e telefone para avisar quando disponível.
5. Indique um corretor pelo nome quando o cliente quiser mais informações ou visita.
6. Colete nome e telefone um de cada vez, de forma natural.
7. Mantenha foco imobiliário. Mensagens curtas, máximo 3 parágrafos.
8. Termine sempre com uma pergunta ou próximo passo claro.

PERFIL DO CLIENTE ATÉ AGORA: {json.dumps(perfil_merged, ensure_ascii=False)}"""

    historico.append({"role": "user", "content": texto})

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=600,
        temperature=0.7,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + historico[-10:]
    )

    resposta = completion.choices[0].message.content.strip()
    historico.append({"role": "assistant", "content": resposta})

    # Atualiza sessão
    novo_estado = {
        "historico": historico[-12:],
        "perfil": perfil_merged,
        "lead_salvo": salvou == "lead_salvo" or sessao.get("lead_salvo", False)
    }
    update_session(session_id, novo_estado)

    return {"mensagem_sofia": resposta}


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
