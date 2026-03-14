from core.db import get_connection
import re

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
    # Interpreta texto livre se fornecido
    if texto:
        filtros = interpretar_busca(texto)
        cidade     = filtros.get("cidade") or cidade
        quartos    = filtros.get("quartos") or quartos
        finalidade = filtros.get("finalidade") or finalidade
        tipo       = filtros.get("tipo") or tipo
        preco_max  = filtros.get("preco_max") or preco_max

    if not any([cidade, quartos, finalidade, tipo, preco_max, bairro]):
        return (
            "Não consegui identificar o que você procura. 😊\n\n"
            "Tente algo como:\n"
            "• 'apartamento em São Paulo até 500 mil'\n"
            "• 'casa em Salto com 3 quartos'\n"
            "• 'imóvel para alugar em Campinas'"
        )

    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT tipo, endereco, bairro, cidade, estado,
               preco, quartos, banheiros, vagas, metragem,
               finalidade, descricao, codigo
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

    # Ordena por bairros diferentes para variedade
    query += " ORDER BY bairro, preco LIMIT %s"
    params.append(limit)

    cur.execute(query, params)
    resultados = cur.fetchall()
    cur.close()
    conn.close()

    if not resultados:
        return "SEM_RESULTADOS"

    resposta = f"🔎 Encontrei {len(resultados)} imóvel(is) para você:\n"
    for r in resultados:
        bairro_txt = f"{r[2]} — " if r[2] else ""
        codigo_txt = f" | Ref: {r[12]}" if r[12] else ""
        resposta += f"""
🏠 {r[0]} — {r[1]}
📍 {bairro_txt}{r[3]} - {r[4]}{codigo_txt}
💰 R$ {float(r[5]):,.2f}
🛏 {r[6]} quartos | 🚿 {r[7]} banheiros | 🚗 {r[8]} vagas | 📐 {r[9]} m²
🔑 {r[10]}
📝 {r[11] or 'Sem descrição'}
──────────────────────────────
"""
    return resposta

def buscar_similares(cidade_original: str, tipo: str = None,
                     preco_max: float = None, finalidade: str = None) -> str:
    cidades = CIDADES_PROXIMAS.get(cidade_original, [])
    if not cidades:
        return f"Não encontrei cidades próximas de {cidade_original} no momento."

    conn = get_connection()
    cur = conn.cursor()

    placeholders = ",".join(["%s"] * len(cidades))
    query = f"""
        SELECT tipo, endereco, bairro, cidade, estado,
               preco, quartos, banheiros, vagas, metragem,
               finalidade, descricao, codigo
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
        params.append(preco_max * 1.2)  # 20% de tolerância

    query += " ORDER BY preco LIMIT 4"

    cur.execute(query, params)
    resultados = cur.fetchall()
    cur.close()
    conn.close()

    if not resultados:
        return f"Também não encontrei imóveis similares nas cidades próximas de {cidade_original}."

    cidades_str = ", ".join(cidades)
    resposta = f"Não encontrei em {cidade_original}, mas encontrei opções próximas ({cidades_str}):\n"
    for r in resultados:
        bairro_txt = f"{r[2]} — " if r[2] else ""
        codigo_txt = f" | Ref: {r[12]}" if r[12] else ""
        resposta += f"""
🏠 {r[0]} — {r[1]}
📍 {bairro_txt}{r[3]} - {r[4]}{codigo_txt}
💰 R$ {float(r[5]):,.2f}
🛏 {r[6]} quartos | 🚿 {r[7]} banheiros | 🚗 {r[8]} vagas | 📐 {r[9]} m²
🔑 {r[10]}
📝 {r[11] or 'Sem descrição'}
──────────────────────────────
"""
    return resposta

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
