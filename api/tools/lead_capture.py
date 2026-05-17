from core.db import get_connection
from datetime import datetime

def salvar_lead(nome: str, telefone: str, email: str = None, interesse: str = None) -> str:
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Verifica se lead já existe pelo telefone
        cur.execute("SELECT id FROM leads WHERE telefone = %s", (telefone,))
        existente = cur.fetchone()

        if existente:
            # Atualiza interesse se já cadastrado
            cur.execute("""
                UPDATE leads SET
                    imovelInteresse = %s,
                    updatedAt = %s
                WHERE telefone = %s
            """, (interesse, datetime.now(), telefone))
            conn.commit()
            cur.close()
            conn.close()
            return f"LEAD_ATUALIZADO:{nome}"

        # Email padrão se não fornecido
        email_final = email or f"{telefone.replace(' ', '')}@sem-email.com"

        cur.execute("""
            INSERT INTO leads (id, nome, email, telefone, origem, status,
                               imovelInteresse, createdAt, updatedAt, dataCaptcha)
            VALUES (gen_random_uuid(), %s, %s, %s, 'sofia-ia', 'novo', %s,
                    NOW(), NOW(), NOW())
        """, (nome, email_final, telefone, interesse))

        conn.commit()
        cur.close()
        conn.close()
        return f"LEAD_SALVO:{nome}"

    except Exception as e:
        return f"ERRO_LEAD:{str(e)}"
