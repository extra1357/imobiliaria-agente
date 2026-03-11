import os
from groq import Groq
from tools.property_tools import (
    count_properties,
    available_properties,
    average_price,
    most_expensive_property,
    cheapest_property,
    properties_by_city,
    properties_by_bairro,
)

client = Groq()

TOOLS = {
    "count_properties": count_properties,
    "available_properties": available_properties,
    "average_price": average_price,
    "most_expensive_property": most_expensive_property,
    "cheapest_property": cheapest_property,
    "properties_by_city": properties_by_city,
    "properties_by_bairro": properties_by_bairro,
}


def _choose_tool(question: str) -> str:
    """Usa o LLM para decidir qual ferramenta chamar com base na pergunta."""

    prompt = f"""
Você é um assistente de imóveis. O usuário fez uma pergunta e você deve escolher
a ferramenta mais adequada para respondê-la.

Ferramentas disponíveis:
- count_properties       → quantidade total de imóveis
- available_properties   → imóveis disponíveis
- average_price          → preço médio dos imóveis
- most_expensive_property → imóvel mais caro
- cheapest_property      → imóvel mais barato
- properties_by_city     → imóveis agrupados por cidade
- properties_by_bairro   → imóveis agrupados por bairro

Retorne APENAS o nome exato de uma ferramenta da lista acima, sem explicações.

Pergunta: {question}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
    )

    tool_name = response.choices[0].message.content.strip()
    return tool_name


def run_agent(question: str) -> str:
    """Recebe uma pergunta em linguagem natural e retorna a resposta."""

    tool_name = _choose_tool(question)

    if tool_name not in TOOLS:
        return (
            f"Não entendi a pergunta. Ferramenta sugerida '{tool_name}' não existe.\n"
            f"Ferramentas disponíveis: {', '.join(TOOLS.keys())}"
        )

    try:
        result = TOOLS[tool_name]()
        return result
    except Exception as e:
        return f"Erro ao executar '{tool_name}': {e}"
