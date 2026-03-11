from core.db import get_connection

def preco_medio_cidade(texto: str) -> str:
    cidades = ["são paulo", "campinas", "salto", "mairinque", "sorocaba", "itu", "indaiatuba"]
    cidade_encontrada = None
    t = texto.lower()
    for c in cidades:
        if c in t:
            cidade_encontrada = c.title()
            break

    conn = get_connection()
    cur = conn.cursor()

    if cidade_encontrada:
        cur.execute("""
            SELECT cidade, AVG(preco), MIN(preco), MAX(preco), COUNT(*)
            FROM imoveis
            WHERE disponivel = true AND LOWER(cidade) = LOWER(%s)
            GROUP BY cidade
        """, (cidade_encontrada,))
    else:
        cur.execute("""
            SELECT cidade, AVG(preco), MIN(preco), MAX(preco), COUNT(*)
            FROM imoveis
            WHERE disponivel = true
            GROUP BY cidade
            ORDER BY AVG(preco) DESC
        """)

    resultados = cur.fetchall()
    cur.close()
    conn.close()

    if not resultados:
        return "Não encontrei dados de preço para essa cidade."

    resposta = "📊 Análise de preços:\n\n"
    for r in resultados:
        resposta += f"""
🏙️ {r[0]}
💰 Preço médio: R$ {r[1]:,.2f}
📉 Mínimo: R$ {r[2]:,.2f}
📈 Máximo: R$ {r[3]:,.2f}
🏠 Total de imóveis: {r[4]}
──────────────────────────────
"""
    return resposta
