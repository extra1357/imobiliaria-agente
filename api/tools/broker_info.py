from core.db import get_connection

def info_corretores(texto: str = "") -> str:
    conn = get_connection()
    cur = conn.cursor()

    # tenta buscar por nome se o texto tiver algum nome
    nome_busca = None
    palavras_ignorar = ["corretor", "corretores", "quem", "atende", "tem", "vocês", "voces", "buscar", "encontrar", "me", "mostra"]
    palavras = [p for p in texto.lower().split() if p not in palavras_ignorar and len(p) > 2]

    if palavras:
        nome_busca = " ".join(palavras)

    if nome_busca:
        cur.execute("""
            SELECT nome, creci, telefone, email FROM corretores
            WHERE ativo = true AND LOWER(nome) ILIKE %s
            ORDER BY nome
        """, (f"%{nome_busca}%",))
        lista = cur.fetchall()
        cur.close()
        conn.close()

        if lista:
            resposta = f"🔍 Resultado para '{nome_busca}':\n\n"
            for c in lista:
                resposta += f"👤 {c[0]}\n📎 CRECI: {c[1]}\n📞 {c[2]}\n"
                if c[3]:
                    resposta += f"✉️ {c[3]}\n"
                resposta += "──────────────────────────────\n"
            return resposta
        else:
            return f"❌ Nenhum corretor encontrado com o nome '{nome_busca}'."

    # sem nome — lista todos
    cur.execute("SELECT COUNT(*) FROM corretores WHERE ativo = true")
    ativos = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM corretores")
    total = cur.fetchone()[0]
    cur.execute("SELECT nome, creci, telefone FROM corretores WHERE ativo = true ORDER BY nome")
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
