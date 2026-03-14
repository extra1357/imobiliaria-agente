from core.db import get_connection
import re

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

def buscar_imoveis(texto=None, cidade=None, quartos=None, finalidade=None, tipo=None, preco_max=None):
    if texto:
        filtros = interpretar_busca(texto)
        cidade     = filtros.get("cidade") or cidade
        quartos    = filtros.get("quartos") or quartos
        finalidade = filtros.get("finalidade") or finalidade
        tipo       = filtros.get("tipo") or tipo
        preco_max  = filtros.get("preco_max") or preco_max

    if not any([cidade, quartos, finalidade, tipo, preco_max]):
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
               finalidade, descricao
        FROM imoveis
        WHERE disponivel = true
    """
    params = []

    if cidade:
        query += " AND LOWER(cidade) = LOWER(%s)"
        params.append(cidade)
    if quartos:
        query += " AND quartos = %s"
        params.append(quartos)
    if tipo:
        query += " AND tipo ILIKE %s"
        params.append(f"%{tipo}%")
    if finalidade:
        # Busca por 'aluguel' retorna também 'venda_aluguel'
        # Busca por 'venda' retorna também 'venda_aluguel'
        query += " AND (finalidade = %s OR finalidade = 'venda_aluguel')"
        params.append(finalidade)
    if preco_max:
        query += " AND preco <= %s"
        params.append(preco_max)

    cur.execute(query, params)
    resultados = cur.fetchall()
    cur.close()
    conn.close()

    if not resultados:
        return "Nenhum imóvel encontrado com esses critérios. Tente ampliar sua busca."

    resposta = f"🔎 {len(resultados)} imóvel(is) encontrado(s):\n"
    for r in resultados:
        bairro = f"{r[2]} — " if r[2] else ""
        preco = f"R$ {float(r[5]):,.2f}"
        resposta += f"""
🏠 {r[0]} — {r[1]}
📍 {bairro}{r[3]} - {r[4]}
💰 {preco}
🛏 {r[6]} quartos | 🚿 {r[7]} banheiros | 🚗 {r[8]} vagas | 📐 {r[9]} m²
🔑 {r[10]}
📝 {r[11] or 'Sem descrição'}
──────────────────────────────
"""
    return resposta
