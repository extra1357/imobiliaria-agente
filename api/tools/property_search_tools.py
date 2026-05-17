from core.db import get_connection


def _format_imovel(row) -> str:
    (codigo, tipo, finalidade, endereco, bairro, cidade, estado,
     preco, preco_aluguel, metragem, quartos, suites, banheiros,
     vagas, destaque, disponivel, status, descricao) = row

    finalidade = (finalidade or "").upper()

    lines = [
        f"📍 {tipo or 'Imóvel'} — {finalidade}",
        f"   Código   : {codigo or 'N/A'}",
        f"   Endereço : {endereco or ''}, {bairro or ''}, {cidade or ''}/{estado or ''}",
        f"   Preço    : R$ {preco:,.2f}" if preco else "",
    ]

    if preco_aluguel:
        lines.append(f"   Aluguel  : R$ {preco_aluguel:,.2f}/mês")

    lines += [
        f"   Área     : {metragem or 0} m²",
        f"   Quartos  : {quartos or 0} | Suítes: {suites or 0} | Banheiros: {banheiros or 0} | Vagas: {vagas or 0}",
        f"   Status   : {status or 'N/A'} | Disponível: {'Sim' if disponivel else 'Não'}",
    ]

    if destaque:
        lines.append("   ⭐ Imóvel em destaque")

    if descricao:
        resumo = descricao[:120]
        if len(descricao) > 120:
            resumo += "..."
        lines.append(f"   Descrição: {resumo}")

    return "\n".join(l for l in lines if l)


_SELECT = """
SELECT
    codigo,
    tipo,
    finalidade,
    endereco,
    bairro,
    cidade,
    estado,
    preco,
    "precoAluguel",
    metragem,
    quartos,
    suites,
    banheiros,
    vagas,
    destaque,
    disponivel,
    status,
    descricao
FROM imoveis
"""


def search_properties(
    cidade: str = None,
    estado: str = None,
    bairro: str = None,
    tipo: str = None,
    finalidade: str = None,
    preco_min: float = None,
    preco_max: float = None,
    quartos_min: int = None,
    suites_min: int = None,
    banheiros_min: int = None,
    vagas_min: int = None,
    metragem_min: float = None,
    metragem_max: float = None,
    disponivel: bool = True,
    destaque: bool = None,
    status: str | None = None,
    limite: int = 10,
) -> str:

    conn = get_connection()
    cur = conn.cursor()

    try:
        conditions = []
        params = []

        if disponivel is not None:
            conditions.append("disponivel = %s")
            params.append(disponivel)

        if status:
            conditions.append("status = %s")
            params.append(status)

        if cidade:
            conditions.append("cidade ILIKE %s")
            params.append(f"%{cidade}%")

        if estado:
            conditions.append("estado ILIKE %s")
            params.append(f"%{estado}%")

        if bairro:
            conditions.append("bairro ILIKE %s")
            params.append(f"%{bairro}%")

        if tipo:
            conditions.append("tipo ILIKE %s")
            params.append(f"%{tipo}%")

        if finalidade:
            conditions.append("finalidade ILIKE %s")
            params.append(f"%{finalidade}%")

        if preco_min is not None:
            conditions.append("preco >= %s")
            params.append(preco_min)

        if preco_max is not None:
            conditions.append("preco <= %s")
            params.append(preco_max)

        if quartos_min is not None:
            conditions.append("quartos >= %s")
            params.append(quartos_min)

        if suites_min is not None:
            conditions.append("suites >= %s")
            params.append(suites_min)

        if banheiros_min is not None:
            conditions.append("banheiros >= %s")
            params.append(banheiros_min)

        if vagas_min is not None:
            conditions.append("vagas >= %s")
            params.append(vagas_min)

        if metragem_min is not None:
            conditions.append("metragem >= %s")
            params.append(metragem_min)

        if metragem_max is not None:
            conditions.append("metragem <= %s")
            params.append(metragem_max)

        if destaque is not None:
            conditions.append("destaque = %s")
            params.append(destaque)

        query = _SELECT

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY destaque DESC, preco ASC LIMIT %s"
        params.append(limite)

        cur.execute(query, params)
        rows = cur.fetchall()

    finally:
        cur.close()
        conn.close()

    if not rows:
        return "Nenhum imóvel encontrado com os filtros informados."

    resultado = f"🏠 {len(rows)} imóvel(is) encontrado(s):\n\n"
    resultado += "\n\n---\n\n".join(_format_imovel(row) for row in rows)

    return resultado


def list_all_properties(limite: int = 10) -> str:
    return search_properties(limite=limite)


def search_by_city(cidade: str, limite: int = 10) -> str:
    return search_properties(cidade=cidade, limite=limite)


def search_by_price_range(preco_min: float = None, preco_max: float = None, limite: int = 10) -> str:
    return search_properties(preco_min=preco_min, preco_max=preco_max, limite=limite)


def search_by_type(tipo: str, limite: int = 10) -> str:
    return search_properties(tipo=tipo, limite=limite)


def search_for_rent(cidade: str = None, preco_max: float = None, limite: int = 10) -> str:
    return search_properties(finalidade="aluguel", cidade=cidade, preco_max=preco_max, limite=limite)


def search_for_sale(cidade: str = None, preco_max: float = None, limite: int = 10) -> str:
    return search_properties(finalidade="venda", cidade=cidade, preco_max=preco_max, limite=limite)


def search_featured_properties(limite: int = 10) -> str:
    return search_properties(destaque=True, limite=limite)


def search_by_bedrooms(quartos_min: int, cidade: str = None, limite: int = 10) -> str:
    return search_properties(quartos_min=quartos_min, cidade=cidade, limite=limite)
