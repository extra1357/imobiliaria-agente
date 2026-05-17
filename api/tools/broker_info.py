import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db import get_connection

def info_corretores() -> str:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nome, email, telefone, creci
        FROM corretores
        WHERE ativo = true
        ORDER BY nome
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    if not rows:
        return json.dumps({"corretores": []})
    corretores = [
        {"id": r[0], "nome": r[1], "email": r[2], "telefone": r[3], "creci": r[4]}
        for r in rows
    ]
    return json.dumps({"corretores": corretores}, ensure_ascii=False)
