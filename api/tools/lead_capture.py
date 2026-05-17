import json
import os
import sys
import uuid
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db import get_connection

def salvar_lead(nome: str, telefone: str, email: str = None,
                imovel_interesse: str = None, data_preferencia: str = None,
                mensagem: str = None, corretor_id: str = None) -> str:
    if not nome or not telefone:
        return json.dumps({"sucesso": False, "erro": "Nome e telefone obrigatórios."})
    conn = get_connection()
    cur = conn.cursor()
    lead_id = str(uuid.uuid4())
    now = datetime.utcnow()
    cur.execute("""
        INSERT INTO leads (id, nome, email, telefone, origem, status,
                          "imovelInteresse", "dataPreferencia", mensagem,
                          "corretorId", "dataCaptcha", "createdAt", "updatedAt")
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        lead_id, nome, email, telefone, "sofia_chat", "novo",
        imovel_interesse, data_preferencia, mensagem,
        corretor_id, now, now, now
    ))
    conn.commit()
    cur.close()
    conn.close()
    return json.dumps({"sucesso": True, "lead_id": lead_id}, ensure_ascii=False)
