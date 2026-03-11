from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tools.property_search_advanced import buscar_imoveis
from tools.schedule_visit import agendar_visita
from tools.price_analysis import preco_medio_cidade
from tools.broker_info import info_corretores
from tools.intent_router import detectar_intencao

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/buscar")
def buscar(dados: dict):
    texto = dados.get("texto") or " ".join(str(v) for v in dados.values())
    if not texto.strip():
        return {"resultado": "Por favor, descreva o que você está procurando."}

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
