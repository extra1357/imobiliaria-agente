import json
import os
import sys
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db import get_connection

SITE_URL = "https://www.imobiliariaperto.com.br"

def _cidades_do_banco():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT LOWER(cidade) FROM imoveis WHERE disponivel = true AND cidade IS NOT NULL")
        cidades = [r[0].strip() for r in cur.fetchall()]
        cur.close(); conn.close()
        return cidades
    except:
        return []

def _tipos_do_banco():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT LOWER(tipo) FROM imoveis WHERE disponivel = true AND tipo IS NOT NULL")
        tipos = [r[0].strip() for r in cur.fetchall()]
        cur.close(); conn.close()
        return tipos
    except:
        return []

def _cidades_proximas_do_banco(cidade):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT cidade FROM imoveis WHERE disponivel = true AND cidade IS NOT NULL AND LOWER(cidade) != LOWER(%s) ORDER BY cidade", (cidade,))
        cidades = [r[0] for r in cur.fetchall()]
        cur.close(); conn.close()
        return cidades
    except:
        return []

def interpretar_busca(texto):
    t = texto.lower()
    cidades_banco = _cidades_do_banco()
    cidade = None
    for c in sorted(cidades_banco, key=len, reverse=True):
        if c in t:
            cidade = c.title()
            break
    tipos_banco = _tipos_do_banco()
    tipo = None
    for tp in sorted(tipos_banco, key=len, reverse=True):
        if tp in t:
            tipo = tp
            break
    finalidade = None
    if any(p in t for p in ["aluguel", "alugar", "locacao", "locar"]):
        finalidade = "aluguel"
    elif any(p in t for p in ["venda", "comprar", "compra", "adquirir"]):
        finalidade = "venda"
    quartos = None
    m = re.search(r"(\d+)\s*quarto", t)
    if m:
        quartos = int(m.group(1))
    preco_max = None
    m = re.search(r"(\d+[\.,]?\d*)\s*(mil|k|milhao)", t)
    if m:
        val = float(m.group(1).replace(",", "."))
        preco_max = int(val * 1000) if m.group(2) in ["mil", "k"] else int(val * 1000000)
    return {"cidade": cidade, "tipo": tipo, "finalidade": finalidade, "quartos": quartos, "preco_max": preco_max}

def buscar_imoveis(cidade=None, bairro=None, tipo=None, quartos=None,
                   finalidade=None, preco_max=None, preco_min=None,
                   texto=None, limit=5):
    if texto:
        filtros = interpretar_busca(texto)
        cidade     = filtros.get("cidade") or cidade
        quartos    = filtros.get("quartos") or quartos
        finalidade = filtros.get("finalidade") or finalidade
        tipo       = filtros.get("tipo") or tipo
        preco_max  = filtros.get("preco_max") or preco_max
    if not any([cidade, quartos, finalidade, tipo, preco_max, bairro]):
        return json.dumps({"tipo": "texto", "conteudo": "Tente: casa em Salto com 3 quartos."})
    conn = get_connection()
    cur = conn.cursor()
    query = """SELECT tipo, endereco, bairro, cidade, estado, preco, quartos, banheiros, vagas, metragem, finalidade, descricao, codigo, slug, imagens, id FROM imoveis WHERE disponivel = true"""
    params = []
    if cidade:
        query += " AND LOWER(cidade) = LOWER(%s)"
        params.append(cidade)
    if bairro:
        query += " AND LOWER(bairro) ILIKE LOWER(%s)"
        params.append("%" + bairro + "%")
    if quartos:
        query += " AND quartos = %s"
        params.append(quartos)
    if tipo:
        query += " AND LOWER(tipo) ILIKE LOWER(%s)"
        params.append("%" + tipo + "%")
    if finalidade:
        query += " AND (finalidade = %s OR finalidade = 'venda_aluguel')"
        params.append(finalidade)
    if preco_max:
        query += " AND preco <= %s"
        params.append(preco_max)
    if preco_min:
        query += " AND preco >= %s"
        params.append(preco_min)
    query += " ORDER BY destaque DESC NULLS LAST, preco LIMIT %s"
    params.append(limit)
    cur.execute(query, params)
    resultados = cur.fetchall()
    cur.close(); conn.close()
    if not resultados:
        return json.dumps({"tipo": "sem_resultados"})
    imoveis = []
    for r in resultados:
        imagens = r[14] if r[14] else []
        imoveis.append({
            "tipo": r[0], "endereco": r[1], "bairro": r[2] or "",
            "cidade": r[3], "estado": r[4], "preco": float(r[5]),
            "quartos": r[6], "banheiros": r[7], "vagas": r[8],
            "metragem": float(r[9]) if r[9] else 0,
            "finalidade": r[10], "descricao": r[11] or "",
            "codigo": r[12] or "", "slug": r[13] or "",
            "foto": imagens[0] if imagens else None,
            "link": "https://www.imobiliariaperto.com.br/imoveis/" + r[15],
        })
    return json.dumps({"tipo": "imoveis", "total": len(imoveis), "imoveis": imoveis}, ensure_ascii=False)

def buscar_similares(cidade_original, tipo=None, preco_max=None, finalidade=None):
    cidades = _cidades_proximas_do_banco(cidade_original)
    if not cidades:
        return json.dumps({"tipo": "sem_resultados"})
    conn = get_connection()
    cur = conn.cursor()
    placeholders = ",".join(["%s"] * len(cidades))
    query = "SELECT tipo, endereco, bairro, cidade, estado, preco, quartos, banheiros, vagas, metragem, finalidade, descricao, codigo, slug, imagens, id FROM imoveis WHERE disponivel = true AND LOWER(cidade) IN (" + placeholders + ")"
    params = [c.lower() for c in cidades]
    if tipo:
        query += " AND LOWER(tipo) ILIKE LOWER(%s)"
        params.append("%" + tipo + "%")
    if finalidade:
        query += " AND (finalidade = %s OR finalidade = 'venda_aluguel')"
        params.append(finalidade)
    if preco_max:
        query += " AND preco <= %s"
        params.append(preco_max * 1.3)
    query += " ORDER BY preco LIMIT 4"
    cur.execute(query, params)
    resultados = cur.fetchall()
    cur.close(); conn.close()
    if not resultados:
        return json.dumps({"tipo": "sem_resultados"})
    imoveis = []
    for r in resultados:
        imagens = r[14] if r[14] else []
        imoveis.append({
            "tipo": r[0], "endereco": r[1], "bairro": r[2] or "",
            "cidade": r[3], "estado": r[4], "preco": float(r[5]),
            "quartos": r[6], "banheiros": r[7], "vagas": r[8],
            "metragem": float(r[9]) if r[9] else 0,
            "finalidade": r[10], "descricao": r[11] or "",
            "foto": imagens[0] if imagens else None,
            "link": "https://www.imobiliariaperto.com.br/imoveis/" + r[15],
        })
    cidades_str = ", ".join(set(im["cidade"] for im in imoveis))
    return json.dumps({"tipo": "imoveis", "total": len(imoveis), "aviso": "Nao encontrei em " + cidade_original + ", mas encontrei em: " + cidades_str, "imoveis": imoveis}, ensure_ascii=False)

def buscar_bairros_disponiveis(cidade, tipo=None, finalidade=None):
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT DISTINCT bairro, COUNT(*) as total FROM imoveis WHERE disponivel = true AND bairro IS NOT NULL AND LOWER(cidade) = LOWER(%s)"
    params = [cidade]
    if tipo:
        query += " AND LOWER(tipo) ILIKE %s"
        params.append("%" + tipo + "%")
    if finalidade:
        query += " AND (finalidade = %s OR finalidade = 'venda_aluguel')"
        params.append(finalidade)
    query += " GROUP BY bairro ORDER BY total DESC"
    cur.execute(query, params)
    resultados = cur.fetchall()
    cur.close(); conn.close()
    if not resultados:
        return "Nenhum bairro encontrado em " + cidade
    bairros = ["- " + r[0] + " (" + str(r[1]) + " imovel)" for r in resultados]
    return "Bairros em " + cidade + ":\n" + "\n".join(bairros)
