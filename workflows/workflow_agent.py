from agents.planner_agent import PlannerAgent
from agents.executor_agent import ExecutorAgent

class WorkflowAgent:

    def __init__(self, planner: PlannerAgent, executor: ExecutorAgent):
        self.planner = planner
        self.executor = executor

    def run(self, task:str):

        steps = self.planner.plan(task)

        results = self.executor.execute(steps)

        return {
            "task": task,
            "steps": steps,
            "results": results
        }
