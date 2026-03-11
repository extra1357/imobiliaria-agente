from core.db import get_connection


def count_properties():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM imoveis")
    total = cur.fetchone()[0]

    cur.close()
    conn.close()

    return f"Total de imóveis: {total}"


def available_properties():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM imoveis WHERE disponivel = true")
    total = cur.fetchone()[0]

    cur.close()
    conn.close()

    return f"Imóveis disponíveis: {total}"


def average_price():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT AVG(preco) FROM imoveis")
    avg = cur.fetchone()[0]

    cur.close()
    conn.close()

    if avg is None:
        return "Nenhum preço encontrado."

    return f"Preço médio dos imóveis: R$ {avg:,.2f}"


def most_expensive_property():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT codigo, preco FROM imoveis ORDER BY preco DESC LIMIT 1")
    result = cur.fetchone()

    cur.close()
    conn.close()

    if result:
        codigo, preco = result
        return f"Imóvel mais caro: código {codigo} — R$ {preco:,.2f}"

    return "Nenhum imóvel encontrado."


def cheapest_property():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT codigo, preco FROM imoveis ORDER BY preco ASC LIMIT 1")
    result = cur.fetchone()

    cur.close()
    conn.close()

    if result:
        codigo, preco = result
        return f"Imóvel mais barato: código {codigo} — R$ {preco:,.2f}"

    return "Nenhum imóvel encontrado."


def properties_by_city():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT cidade, COUNT(*)
    FROM imoveis
    GROUP BY cidade
    ORDER BY COUNT(*) DESC
    """)

    results = cur.fetchall()

    cur.close()
    conn.close()

    response = "Imóveis por cidade:\n"

    for cidade, total in results:
        response += f"{cidade}: {total}\n"

    return response


def properties_by_bairro():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT bairro, COUNT(*)
    FROM imoveis
    GROUP BY bairro
    ORDER BY COUNT(*) DESC
    """)

    results = cur.fetchall()

    cur.close()
    conn.close()

    response = "Imóveis por bairro:\n"

    for bairro, total in results:
        response += f"{bairro}: {total}\n"

    return response
