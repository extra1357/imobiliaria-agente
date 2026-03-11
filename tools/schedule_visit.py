from core.db import get_connection

def agendar_visita(texto: str) -> str:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT codigo, tipo, endereco, cidade 
        FROM imoveis 
        WHERE disponivel = true 
        ORDER BY "createdAt" DESC 
        LIMIT 5
    """)
    imoveis = cur.fetchall()
    cur.close()
    conn.close()

    if not imoveis:
        return "Não encontrei imóveis disponíveis para agendar visita."

    resposta = "📅 Para agendar uma visita escolha um dos imóveis abaixo e entre em contato pelo WhatsApp:\n\n"
    for i in imoveis:
        codigo = i[0] if i[0] else "sem código"
        resposta += f"🏠 {i[1]} — {i[2]}, {i[3]} (ref: {codigo})\n"

    resposta += "\n📞 Informe a referência do imóvel e nossa equipe entrará em contato!"
    return resposta
