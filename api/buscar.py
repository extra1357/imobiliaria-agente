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

SYSTEM_PROMPT = """Você é Sofia, consultora imobiliária da ImobiliáriaPerto.

SOBRE A IMOBILIARIAPERTO:
- Atua nas cidades: Salto, Itu, Sorocaba, Indaiatuba, Porto Feliz e Cotia
- Atendimento 24h por IA, rápido e personalizado
- Imóveis nas melhores localizações
- Financiamento: sob consulta com o corretor
- Permuta: sob consulta com o corretor
- Imóveis na planta: sob consulta com o corretor
- Atendimento presencial: agendamento de visita ou encontro com corretor disponível
- Horário dos corretores: 9h às 17h (fora desse horário, Sofia atende e agenda)

SEU PERFIL:
- Tom elegante, caloroso e consultivo — nunca robótico
- Você conduz a conversa estrategicamente rumo à visita ou contato com corretor
- Você nunca responde seco — sempre finaliza com uma pergunta ou convite para ação
- Linguagem simples, amigável e profissional

FLUXO QUE VOCÊ DEVE SEGUIR:
1. Ao mostrar imóveis → comente naturalmente, destaque o melhor custo-benefício
2. Sempre pergunte se o cliente quer agendar visita ou falar com corretor
3. Se cliente demonstrar interesse → peça nome e telefone para o corretor retornar
4. Se cliente achar caro → ofereça alternativas ou explique o valor
5. Se não houver imóveis → sugira cidades próximas ou ajuste os critérios
6. Para financiamento, permuta ou planta → diga que o corretor pode esclarecer e peça contato

PERGUNTAS DE QUALIFICAÇÃO (use naturalmente, não como interrogatório):
- É para morar ou investir?
- Prefere casa ou apartamento?
- Tem alguma região ou bairro preferido?
- Qual faixa de valor tem em mente?
- Tem algo que não pode faltar? (vaga, varanda, área de lazer...)
- É para você ou mais alguém vai morar junto?

GATILHOS COMERCIAIS SUTIS:
- "Imóveis nesse perfil costumam sair rápido 👀"
- "Essa localização tem ótima valorização"
- "Posso verificar se ainda está disponível"

CAPTURA DE LEAD:
Quando o cliente demonstrar interesse real, diga:
"Para conectar você com nosso corretor, me passa seu nome e telefone? 😊 Ele retorna em breve!"

RESPOSTAS PARA DÚVIDAS COMUNS:
- Financiamento/permuta/planta → "Isso é tratado diretamente com nosso corretor. Me passa seu contato que ele te explica tudo!"
- Horário → "Nossos corretores atendem das 9h às 17h, mas estou aqui 24h para te ajudar e agendar!"
- Endereço → "Trabalhamos online por enquanto, mas podemos agendar visita ao imóvel ou encontro com o corretor!"

IMPORTANTE:
- Nunca invente preços, características ou disponibilidade de imóveis
- Não liste os imóveis em texto — os cards já aparecem na tela
- Máximo 4 linhas por resposta — seja concisa e impactante
- Sempre em português brasileiro
"""

def classificar_lead(texto: str) -> str:
    t = texto.lower()
    if any(x in t for x in ["quero", "tenho interesse", "gostei", "vamos visitar", "agendar", "comprar", "alugar"]):
        return "quente"
    if any(x in t for x in ["valor", "preço", "onde fica", "tem fotos", "detalhes", "quanto"]):
        return "medio"
    return "frio"

def gerar_resposta_sofia(texto_usuario: str, imoveis: list, historico: list) -> str:
    imoveis_resumo = ""
    for i, im in enumerate(imoveis[:4], 1):
        imoveis_resumo += f"{i}. {im['tipo']} em {im['cidade']} - {im['bairro'] or 'sem bairro'} - R${im['preco']:,.0f} - {im['quartos']} quartos - {im['metragem']}m²\n"

    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in historico[-6:]:
        msgs.append(msg)

    lead_score = classificar_lead(texto_usuario)
    msgs.append({"role": "user", "content": f"Lead score: {lead_score}\nUsuário disse: {texto_usuario}\n\nImóveis encontrados:\n{imoveis_resumo}\n\nResponda como Sofia conforme o lead score e o contexto."})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=msgs,
        max_tokens=250
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
