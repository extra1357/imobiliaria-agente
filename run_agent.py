from core.tool_registry import ToolRegistry
from agents.simple_agent import SimpleAgent
from tools.basic_tools import hello, add

registry = ToolRegistry()
registry.register("hello", hello)
registry.register("add", add)

agent = SimpleAgent(registry)

print("Agent result:", agent.run("hello"))
print("Agent math:", agent.run("add", 5, 7))
