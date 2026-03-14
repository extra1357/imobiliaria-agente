from core.db import get_connection
import re
import json

SITE_URL = "https://www.imobiliariaperto.com.br"

CIDADES_PROXIMAS = {
    "Salto": ["Itu", "Indaiatuba", "Sorocaba"],
    "Itu": ["Salto", "Sorocaba", "Indaiatuba"],
    "Indaiatuba": ["Campinas", "Itu", "Salto"],
    "Campinas": ["Indaiatuba", "Sorocaba"],
    "Sorocaba": ["Itu", "Salto", "Campinas"],
    "São Paulo": ["Campinas", "Sorocaba"],
}

def buscar_bairros_disponiveis(cidade: str, tipo: str = None, finalidade: str = None) -> str:
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT DISTINCT bairro, COUNT(*) as total
        FROM imoveis
        WHERE disponivel = true
        AND bairro IS NOT NULL
        AND LOWER(cidade) = LOWER(%s)
    """
    params = [cidade]
    if tipo:
        query += " AND tipo ILIKE %s"
        params.append(f"%{tipo}%")
    if finalidade:
        query += " AND (finalidade = %s OR finalidade = 'venda_aluguel')"
        params.append(finalidade)
    query += " GROUP BY bairro ORDER BY total DESC"
    cur.execute(query, params)
    resultados = cur.fetchall()
    cur.close()
    conn.close()
    if not resultados:
        return f"Nenhum bairro encontrado em {cidade} com esses critérios."
    bairros = [f"• {r[0]} ({r[1]} imóvel{'is' if r[1] > 1 else ''})" for r in resultados]
    return f"Bairros disponíveis em {cidade}:\n" + "\n".join(bairros)

def buscar_imoveis(cidade=None, bairro=None, tipo=None, quartos=None,
                   finalidade=None, preco_max=None, preco_min=None,
                   texto=None, limit=4):
    if texto:
        filtros = interpretar_busca(texto)
        cidade     = filtros.get("cidade") or cidade
        quartos    = filtros.get("quartos") or quartos
        finalidade = filtros.get("finalidade") or finalidade
        tipo       = filtros.get("tipo") or tipo
        preco_max  = filtros.get("preco_max") or preco_max

    if not any([cidade, quartos, finalidade, tipo, preco_max, bairro]):
        return json.dumps({"tipo": "texto", "conteudo": (
            "Não consegui identificar o que você procura. 😊\n\n"
            "Tente algo como:\n"
            "• 'apartamento em São Paulo até 500 mil'\n"
            "• 'casa em Salto com 3 quartos'\n"
            "• 'imóvel para alugar em Campinas'"
        )})

    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT tipo, endereco, bairro, cidade, estado,
               preco, quartos, banheiros, vagas, metragem,
               finalidade, descricao, codigo, slug, imagens
        FROM imoveis
        WHERE disponivel = true
    """
    params = []

    if cidade:
        query += " AND LOWER(cidade) = LOWER(%s)"
        params.append(cidade)
    if bairro:
        query += " AND LOWER(bairro) ILIKE LOWER(%s)"
        params.append(f"%{bairro}%")
    if quartos:
        query += " AND quartos = %s"
        params.append(quartos)
    if tipo:
        query += " AND tipo ILIKE %s"
        params.append(f"%{tipo}%")
    if finalidade:
        query += " AND (finalidade = %s OR finalidade = 'venda_aluguel')"
        params.append(finalidade)
    if preco_max:
        query += " AND preco <= %s"
        params.append(preco_max)
    if preco_min:
        query += " AND preco >= %s"
        params.append(preco_min)

    query += " ORDER BY bairro, preco LIMIT %s"
    params.append(limit)

    cur.execute(query, params)
    resultados = cur.fetchall()
    cur.close()
    conn.close()

    if not resultados:
        return json.dumps({"tipo": "texto", "conteudo": "SEM_RESULTADOS"})

    imoveis = []
    for r in resultados:
        slug = r[13]
        imagens = r[14] if r[14] else []
        foto = imagens[0] if imagens else None
        link = f"{SITE_URL}/imoveis/{slug}" if slug else None

        imoveis.append({
            "tipo": r[0],
            "endereco": r[1],
            "bairro": r[2] or "",
            "cidade": r[3],
            "estado": r[4],
            "preco": float(r[5]),
            "quartos": r[6],
            "banheiros": r[7],
            "vagas": r[8],
            "metragem": float(r[9]),
            "finalidade": r[10],
            "descricao": r[11] or "",
            "codigo": r[12] or "",
            "slug": slug or "",
            "foto": foto,
            "link": link,
        })

    return json.dumps({
        "tipo": "imoveis",
        "total": len(imoveis),
        "imoveis": imoveis
    }, ensure_ascii=False)

def buscar_similares(cidade_original: str, tipo: str = None,
                     preco_max: float = None, finalidade: str = None) -> str:
    cidades = CIDADES_PROXIMAS.get(cidade_original, [])
    if not cidades:
        return json.dumps({"tipo": "texto", "conteudo": f"Não encontrei cidades próximas de {cidade_original}."})

    conn = get_connection()
    cur = conn.cursor()

    placeholders = ",".join(["%s"] * len(cidades))
    query = f"""
        SELECT tipo, endereco, bairro, cidade, estado,
               preco, quartos, banheiros, vagas, metragem,
               finalidade, descricao, codigo, slug, imagens
        FROM imoveis
        WHERE disponivel = true
        AND LOWER(cidade) IN ({placeholders})
    """
    params = [c.lower() for c in cidades]

    if tipo:
        query += " AND tipo ILIKE %s"
        params.append(f"%{tipo}%")
    if finalidade:
        query += " AND (finalidade = %s OR finalidade = 'venda_aluguel')"
        params.append(finalidade)
    if preco_max:
        query += " AND preco <= %s"
        params.append(preco_max * 1.2)

    query += " ORDER BY preco LIMIT 4"

    cur.execute(query, params)
    resultados = cur.fetchall()
    cur.close()
    conn.close()

    if not resultados:
        return json.dumps({"tipo": "texto", "conteudo": f"Também não encontrei imóveis similares nas cidades próximas de {cidade_original}."})

    imoveis = []
    for r in resultados:
        slug = r[13]
        imagens = r[14] if r[14] else []
        foto = imagens[0] if imagens else None
        link = f"{SITE_URL}/imoveis/{slug}" if slug else None
        imoveis.append({
            "tipo": r[0], "endereco": r[1], "bairro": r[2] or "",
            "cidade": r[3], "estado": r[4], "preco": float(r[5]),
            "quartos": r[6], "banheiros": r[7], "vagas": r[8],
            "metragem": float(r[9]), "finalidade": r[10],
            "descricao": r[11] or "", "codigo": r[12] or "",
            "slug": slug or "", "foto": foto, "link": link,
        })

    cidades_str = ", ".join(cidades)
    return json.dumps({
        "tipo": "imoveis",
        "total": len(imoveis),
        "aviso": f"Não encontrei em {cidade_original}, mas encontrei em cidades próximas ({cidades_str}):",
        "imoveis": imoveis
    }, ensure_ascii=False)

def interpretar_busca(texto: str) -> dict:
    t = texto.lower()
    cidades = ["são paulo", "campinas", "salto", "mairinque", "sorocaba", "itu", "indaiatuba"]
    cidade = next((c.title() for c in cidades if c in t), None)
    tipos = ["apartamento", "casa", "sobrado", "terreno", "comercial", "sala"]
    tipo = next((tp for tp in tipos if tp in t), None)
    finalidade = None
    if any(p in t for p in ["aluguel", "alugar", "locação"]):
        finalidade = "aluguel"
    elif any(p in t for p in ["venda", "comprar", "compra"]):
        finalidade = "venda"
    quartos = None
    match_q = re.search(r'(\d+)\s*quarto', t)
    if match_q:
        quartos = int(match_q.group(1))
    preco_max = None
    match_p = re.search(r'(\d+[\.,]?\d*)\s*(mil|milhão|milhao|k)', t)
    if match_p:
        valor = float(match_p.group(1).replace(',', '.'))
        unidade = match_p.group(2)
        preco_max = int(valor * 1000) if unidade in ["mil", "k"] else int(valor * 1000000)
    return {"cidade": cidade, "tipo": tipo, "finalidade": finalidade,
            "quartos": quartos, "preco_max": preco_max}
