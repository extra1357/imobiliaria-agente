from core.tool_registry import ToolRegistry
from agents.simple_agent import SimpleAgent
from agents.executor_agent import ExecutorAgent
from agents.planner_agent import PlannerAgent
from workflows.workflow_agent import WorkflowAgent
from tools.basic_tools import hello

def test_workflow():

    registry = ToolRegistry()
    registry.register("hello", hello)

    agent = SimpleAgent(registry)

    planner = PlannerAgent()

    executor = ExecutorAgent(agent)

    workflow = WorkflowAgent(planner, executor)

    result = workflow.run("say hello")

    assert result["results"][0] == "hello world"
