import re

CIDADES = ["são paulo", "campinas", "salto", "mairinque"]

def extrair_cidade(texto):

    texto = texto.lower()

    for cidade in CIDADES:
        if cidade in texto:
            return cidade.title()

    return None


def extrair_preco(texto):

    texto = texto.lower()

    match = re.search(r'(\d+)\s*mil', texto)

    if match:
        valor = int(match.group(1)) * 1000
        return valor

    match = re.search(r'(\d+)\s*milhões?', texto)

    if match:
        valor = int(match.group(1)) * 1000000
        return valor

    return None


def extrair_quartos(texto):

    texto = texto.lower()

    match = re.search(r'(\d+)\s*quartos?', texto)

    if match:
        return int(match.group(1))

    return None


def extrair_tipo(texto):

    texto = texto.lower()

    if "apartamento" in texto:
        return "Apartamento"

    if "casa" in texto:
        return "Casa"

    return None
