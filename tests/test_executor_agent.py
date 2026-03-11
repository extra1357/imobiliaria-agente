from core.tool_registry import ToolRegistry
from agents.simple_agent import SimpleAgent
from agents.executor_agent import ExecutorAgent
from tools.basic_tools import hello

def test_execute_single():

    registry = ToolRegistry()
    registry.register("hello", hello)

    agent = SimpleAgent(registry)

    executor = ExecutorAgent(agent)

    results = executor.execute(["hello"])

    assert results == ["hello world"]
