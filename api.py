from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tools.property_search_advanced import buscar_imoveis, buscar_bairros_disponiveis
from tools.schedule_visit import agendar_visita
from tools.price_analysis import preco_medio_cidade
from tools.broker_info import info_corretores
from tools.lead_capture import salvar_lead
from tools.intent_router import detectar_intencao
from groq import Groq
from dotenv import load_dotenv
import os
import json

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq()

# Memória de conversa por sessão
conversas: dict[str, list] = {}

SYSTEM_PROMPT = """Você é Sofia, consultora de imóveis da STR Imobiliária.
Você é simpática, objetiva e profissional.

FLUXO DE BUSCA INTELIGENTE:
Quando o usuário pedir imóveis, siga SEMPRE esta ordem antes de buscar:

1. Se não souber a CIDADE → pergunte
2. Se não souber a FINALIDADE (venda ou aluguel) → pergunte
3. Se souber cidade e finalidade → use a tool 'buscar_bairros' para ver quais bairros têm imóveis disponíveis
4. Pergunte se tem preferência de bairro, mostrando as opções disponíveis
5. Se não souber a FAIXA DE PREÇO → pergunte (ex: "Qual seu orçamento aproximado?")
6. Com todas as informações → use 'buscar_imoveis' com limit=4
7. Após mostrar os imóveis → pergunte se quer agendar visita ou saber mais
8. Ao final → capture o lead: "Para te manter informado sobre novidades, posso anotar seu nome e telefone?"

CAPTURA DE LEAD:
- Quando o usuário fornecer nome e telefone → use a tool 'salvar_lead' imediatamente
- Confirme o cadastro e diga que a equipe entrará em contato

REGRAS GERAIS:
- Máximo 4 imóveis por resposta
- Se não encontrar resultados → use 'buscar_similares' para sugerir cidades próximas
- Mantenha contexto da conversa — lembre cidade, bairro, preço discutidos antes
- Respostas em português brasileiro
- Use emojis com moderação
- Para agendamento, corretores e preço médio use as tools correspondentes
- Nunca invente imóveis — use sempre as tools para buscar dados reais
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "buscar_bairros",
            "description": "Busca quais bairros têm imóveis disponíveis em uma cidade. Use ANTES de buscar imóveis para perguntar ao usuário a preferência de bairro.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cidade": {"type": "string", "description": "Nome da cidade"},
                    "tipo": {"type": "string", "description": "Tipo do imóvel (opcional)"},
                    "finalidade": {"type": "string", "description": "venda ou aluguel (opcional)"}
                },
                "required": ["cidade"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_imoveis",
            "description": "Busca imóveis no banco com filtros. Sempre use limit=4. Use após coletar cidade, bairro, finalidade e faixa de preço do usuário.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cidade": {"type": "string", "description": "Cidade do imóvel"},
                    "bairro": {"type": "string", "description": "Bairro do imóvel"},
                    "tipo": {"type": "string", "description": "casa, apartamento, terreno, comercial, sala, sobrado"},
                    "quartos": {"type": "integer", "description": "Número de quartos"},
                    "preco_max": {"type": "number", "description": "Preço máximo em reais"},
                    "preco_min": {"type": "number", "description": "Preço mínimo em reais"},
                    "finalidade": {"type": "string", "description": "venda ou aluguel"},
                    "limit": {"type": "integer", "description": "Limite de resultados, sempre use 4"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_similares",
            "description": "Busca imóveis similares em cidades próximas quando não há resultados na cidade desejada.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cidade_original": {"type": "string", "description": "Cidade que não teve resultados"},
                    "tipo": {"type": "string", "description": "Tipo do imóvel"},
                    "preco_max": {"type": "number", "description": "Preço máximo"},
                    "finalidade": {"type": "string", "description": "venda ou aluguel"}
                },
                "required": ["cidade_original"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "salvar_lead",
            "description": "Salva o contato do usuário no CRM. Use quando o usuário fornecer nome e telefone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string", "description": "Nome completo do interessado"},
                    "telefone": {"type": "string", "description": "Telefone ou WhatsApp"},
                    "email": {"type": "string", "description": "Email (opcional)"},
                    "interesse": {"type": "string", "description": "Resumo do que o usuário procura"}
                },
                "required": ["nome", "telefone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "preco_medio_cidade",
            "description": "Retorna análise de preço médio, mínimo e máximo por cidade.",
            "parameters": {
                "type": "object",
                "properties": {
                    "texto": {"type": "string", "description": "Texto com a cidade para análise"}
                },
                "required": ["texto"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "agendar_visita",
            "description": "Lista imóveis disponíveis para agendar visita.",
            "parameters": {
                "type": "object",
                "properties": {
                    "texto": {"type": "string", "description": "Mensagem do usuário"}
                },
                "required": ["texto"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "info_corretores",
            "description": "Lista os corretores ativos com CRECI e contato.",
            "parameters": {
                "type": "object",
                "properties": {
                    "texto": {"type": "string", "description": "Mensagem do usuário"}
                },
                "required": ["texto"]
            }
        }
    }
]

def executar_tool(nome: str, inputs: dict) -> str:
    try:
        if nome == "buscar_imoveis":
            return buscar_imoveis(**inputs)
        elif nome == "buscar_bairros":
            return buscar_bairros_disponiveis(**inputs)
        elif nome == "buscar_similares":
            from tools.property_search_advanced import buscar_similares
            return buscar_similares(**inputs)
        elif nome == "salvar_lead":
            return salvar_lead(**inputs)
        elif nome == "preco_medio_cidade":
            return preco_medio_cidade(inputs.get("texto", ""))
        elif nome == "agendar_visita":
            return agendar_visita(inputs.get("texto", ""))
        elif nome == "info_corretores":
            return info_corretores(inputs.get("texto", ""))
        else:
            return f"Ferramenta '{nome}' não encontrada."
    except Exception as e:
        return f"Erro ao executar {nome}: {str(e)}"

@app.post("/buscar")
def buscar(dados: dict):
    texto = dados.get("texto", "").strip()
    session_id = dados.get("session_id", "default")

    if not texto:
        return {"resultado": "Por favor, descreva o que você está procurando."}

    if session_id not in conversas:
        conversas[session_id] = []

    conversas[session_id].append({"role": "user", "content": texto})

    historico = conversas[session_id][-20:]
    mensagens = [{"role": "system", "content": SYSTEM_PROMPT}] + historico

    try:
        response = client.chat.completions.create(
            model="llama3-groq-70b-8192-tool-use-preview",
            messages=mensagens,
            tools=TOOLS,
            tool_choice="auto",
        )

        msg = response.choices[0].message

        max_iteracoes = 5
        iteracao = 0

        while msg.tool_calls and iteracao < max_iteracoes:
            iteracao += 1
            mensagens.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in msg.tool_calls
                ]
            })

            for tool_call in msg.tool_calls:
                inputs = json.loads(tool_call.function.arguments)
                resultado = executar_tool(tool_call.function.name, inputs)
                mensagens.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": resultado
                })

            response = client.chat.completions.create(
                model="llama3-groq-70b-8192-tool-use-preview",
                messages=mensagens,
                tools=TOOLS,
            )
            msg = response.choices[0].message

        resposta_final = msg.content or "Não consegui processar sua solicitação."
        conversas[session_id].append({"role": "assistant", "content": resposta_final})

        return {"resultado": resposta_final}

    except Exception as e:
        print(f"Erro na API Groq: {e}")
        intencao = detectar_intencao(texto)
        if intencao == "agendar":
            resultado = agendar_visita(texto)
        elif intencao == "preco_medio":
            resultado = preco_medio_cidade(texto)
        elif intencao == "corretores":
            resultado = info_corretores(texto)
        else:
            resultado = buscar_imoveis(texto=texto)
        return {"resultado": resultado}

@app.delete("/conversa/{session_id}")
def limpar_conversa(session_id: str):
    if session_id in conversas:
        del conversas[session_id]
    return {"ok": True}

@app.get("/health")
def health():
    return {"status": "ok"}
