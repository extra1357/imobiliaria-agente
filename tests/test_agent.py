from core.tool_registry import ToolRegistry
from agents.simple_agent import SimpleAgent
from tools.basic_tools import hello, add

def test_agent_hello():
    registry = ToolRegistry()
    registry.register("hello", hello)

    agent = SimpleAgent(registry)

    assert agent.run("hello") == "hello world"

def test_agent_add():
    registry = ToolRegistry()
    registry.register("add", add)

    agent = SimpleAgent(registry)

    assert agent.run("add",2,3) == 5
