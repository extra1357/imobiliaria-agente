import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.prompt import checar_guard, GUARD_BUSCA, proxima_etapa_faltando

def decidir_acao(perfil: dict, texto: str) -> str:
    t = texto.lower()
    if any(p in t for p in ["agendar", "visita", "visitar", "ver o imovel", "conhecer"]):
        return "agendar"
    if not checar_guard(perfil, GUARD_BUSCA):
        return "buscar"
    return "qualificar"

def montar_instrucao_acao(acao: str, perfil: dict) -> str:
    if acao == "agendar":
        falta = [f for f in ["nome", "telefone"] if not perfil.get(f)]
        if falta:
            campo = falta[0]
            pergunta = "seu nome completo" if campo == "nome" else "seu telefone de contato"
            return f"\nINSTRUCAO: Cliente quer agendar visita. Colete agora: {pergunta}."
        return "\nINSTRUCAO: Cliente quer agendar. Voce ja tem nome e telefone. Sugira horarios e confirme a data."
    if acao == "qualificar":
        proxima = proxima_etapa_faltando(perfil)
        if proxima:
            return f'\nINSTRUCAO: Faca APENAS esta pergunta agora: "{proxima[1]}"'
    return ""
