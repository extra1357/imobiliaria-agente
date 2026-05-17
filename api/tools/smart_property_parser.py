import re
from tools.property_search_tools import search_properties


TIPOS = ["apartamento", "casa", "terreno", "sala"]

FINALIDADES = {
    "aluguel": "aluguel",
    "alugar": "aluguel",
    "locação": "aluguel",
    "venda": "venda",
    "comprar": "venda",
}


def extrair_preco(texto: str):
    match = re.search(r"até\s*(\d+)\s*(mil)?", texto)

    if not match:
        return None

    valor = int(match.group(1))

    if match.group(2):
        valor = valor * 1000

    return valor


def extrair_quartos(texto: str):
    match = re.search(r"(\d+)\s*quartos?", texto)

    if match:
        return int(match.group(1))

    return None


def extrair_tipo(texto: str):
    for t in TIPOS:
        if t in texto:
            return t
    return None


def extrair_finalidade(texto: str):
    for palavra, finalidade in FINALIDADES.items():
        if palavra in texto:
            return finalidade
    return None


def extrair_cidade(texto: str):
    match = re.search(r"em\s+([a-zA-Zãõáéíóúç\s]+)", texto)

    if match:
        cidade = match.group(1).strip()
        return cidade.title()

    return None


def parse_busca(texto: str):

    texto = texto.lower()

    filtros = {
        "tipo": extrair_tipo(texto),
        "cidade": extrair_cidade(texto),
        "finalidade": extrair_finalidade(texto),
        "preco_max": extrair_preco(texto),
        "quartos_min": extrair_quartos(texto),
    }

    filtros = {k: v for k, v in filtros.items() if v is not None}

    return filtros


def buscar_imoveis_inteligente(texto: str):

    filtros = parse_busca(texto)

    return search_properties(**filtros)
