def detectar_intencao(texto: str) -> str:
    t = texto.lower()

    agendamento = ["agendar", "visita", "visitar", "marcar", "quero ver", "conhecer", "ver o imovel", "ver o imóvel"]
    if any(p in t for p in agendamento):
        return "agendar"

    preco_medio = ["preço médio", "preco medio", "média", "media", "quanto custa em", "valor médio", "valor medio", "quanto tá", "quanto ta"]
    if any(p in t for p in preco_medio):
        return "preco_medio"

    corretores = ["corretor", "corretores", "quantos corretores", "equipe", "time de vendas", "quem atende"]
    if any(p in t for p in corretores):
        return "corretores"

    busca = ["quero", "buscar", "procuro", "procurando", "tem ", "apartamento", "casa", "terreno", "sala", "comercial", "quartos", "venda", "aluguel", "alugar"]
    if any(p in t for p in busca):
        return "buscar"

    return "buscar"
