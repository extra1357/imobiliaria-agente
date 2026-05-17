"""
tools/schedule_visit.py
Listagem de imóveis disponíveis para visita e confirmação de agendamento.
Guard Rails: nome, telefone e data são obrigatórios para confirmar.
"""
from datetime import datetime

try:
    from core.db import get_connection
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False


def listar_imoveis_para_visita(cidade: str = None, tipo: str = None) -> list:
    """Retorna imóveis disponíveis, filtrando por cidade e/ou tipo se informados."""
    if not DB_AVAILABLE:
        return _imoveis_mock(cidade, tipo)

    try:
        conn = get_connection()
        cur = conn.cursor()
        query = """
            SELECT id, titulo, cidade, tipo, preco, quartos, endereco, descricao
            FROM imoveis
            WHERE disponivel = true
        """
        params = []
        if cidade:
            query += " AND LOWER(cidade) = LOWER(%s)"
            params.append(cidade)
        if tipo:
            query += " AND LOWER(tipo) = LOWER(%s)"
            params.append(tipo)
        query += " ORDER BY created_at DESC LIMIT 10"
        cur.execute(query, params)
        colunas = [d[0] for d in cur.description]
        return [dict(zip(colunas, row)) for row in cur.fetchall()]
    except Exception as e:
        print(f"[schedule_visit] Erro ao listar: {e}")
        return []


def confirmar_agendamento(nome: str, telefone: str, data: str,
                          imovel_id: int = None, corretor_id: int = None) -> dict:
    """
    Confirma agendamento de visita.
    Guard Rail: rejeita se nome, telefone ou data estiverem ausentes/inválidos.
    """
    erros = []
    if not nome or len(nome.strip()) < 3:
        erros.append("nome completo")
    if not telefone or len(telefone.strip()) < 8:
        erros.append("telefone válido")
    if not data or len(data.strip()) < 4:
        erros.append("data preferida")

    if erros:
        return {
            "sucesso": False,
            "mensagem": f"Para confirmar o agendamento ainda preciso do(a): {', '.join(erros)}.",
        }

    if DB_AVAILABLE:
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO agendamentos
                    (nome, telefone, data_preferida, imovel_id, corretor_id, criado_em)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (nome.strip(), telefone.strip(), data.strip(),
                 imovel_id, corretor_id, datetime.utcnow()),
            )
            conn.commit()
            agendamento_id = cur.fetchone()[0]
        except Exception as e:
            print(f"[schedule_visit] Erro ao salvar agendamento: {e}")
            agendamento_id = None
    else:
        agendamento_id = "mock-" + datetime.utcnow().strftime("%Y%m%d%H%M%S")

    return {
        "sucesso": True,
        "agendamento_id": agendamento_id,
        "mensagem": (
            f"Perfeito, {nome}! Visita confirmada para {data}. "
            f"Nosso corretor entrará em contato pelo {telefone} para confirmar os detalhes. 🏡"
        ),
    }


def _imoveis_mock(cidade=None, tipo=None) -> list:
    imoveis = [
        {
            "id": 1,
            "titulo": "Apartamento 2 quartos no Centro",
            "cidade": "Campinas",
            "tipo": "apartamento",
            "preco": 320000,
            "quartos": 2,
            "endereco": "Rua das Flores, 123 - Centro",
            "descricao": "Apto reformado, 65m², 1 vaga, próximo ao metrô.",
        },
        {
            "id": 2,
            "titulo": "Casa 3 quartos com piscina",
            "cidade": "Campinas",
            "tipo": "casa",
            "preco": 680000,
            "quartos": 3,
            "endereco": "Rua Verde, 456 - Jardim das Palmeiras",
            "descricao": "Casa ampla, 180m², piscina, churrasqueira, 2 vagas.",
        },
        {
            "id": 3,
            "titulo": "Kitnet mobiliada perto da USP",
            "cidade": "São Paulo",
            "tipo": "kitnet",
            "preco": 120000,
            "quartos": 1,
            "endereco": "Av. Prof. Luciano Gualberto, 78 - Butantã",
            "descricao": "Kitnet de 25m², totalmente mobiliada, ideal para estudantes.",
        },
    ]
    if cidade:
        imoveis = [i for i in imoveis if i["cidade"].lower() == cidade.lower()]
    if tipo:
        imoveis = [i for i in imoveis if i["tipo"].lower() == tipo.lower()]
    return imoveis
