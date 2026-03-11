from core.db import get_connection

def info_corretores(texto: str) -> str:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*) FROM corretores WHERE ativo = true
    """)
    ativos = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) FROM corretores
    """)
    total = cur.fetchone()[0]

    cur.execute("""
        SELECT nome, creci, telefone FROM corretores WHERE ativo = true ORDER BY nome
    """)
    lista = cur.fetchall()

    cur.close()
    conn.close()

    resposta = f"👥 Corretores cadastrados: {total}\n"
    resposta += f"✅ Corretores ativos: {ativos}\n\n"

    if lista:
        resposta += "📋 Lista de corretores ativos:\n\n"
        for c in lista:
            resposta += f"👤 {c[0]}\n📎 CRECI: {c[1]}\n📞 {c[2]}\n──────────────────────────────\n"

    return resposta
