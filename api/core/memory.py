"""
core/memory.py
Gerenciamento de sessão em memória (thread-safe).
Para produção substitua por Redis ou banco de dados.
"""
from threading import Lock
from copy import deepcopy

_store: dict = {}
_lock = Lock()


def get_session(session_id: str) -> dict:
    """Retorna a sessão existente ou cria uma nova."""
    with _lock:
        if session_id not in _store:
            _store[session_id] = {
                "historico": [],
                "perfil": {},
            }
        return deepcopy(_store[session_id])


def update_session(session_id: str, session: dict) -> None:
    """Persiste a sessão atualizada."""
    with _lock:
        _store[session_id] = deepcopy(session)


def clear_session(session_id: str) -> None:
    """Remove a sessão (reset explícito ou testes)."""
    with _lock:
        _store.pop(session_id, None)


def list_sessions() -> list:
    """Lista todos os session_ids ativos (debug)."""
    with _lock:
        return list(_store.keys())
