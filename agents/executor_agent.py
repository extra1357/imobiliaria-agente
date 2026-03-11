from agents.simple_agent import SimpleAgent

class ExecutorAgent:

    def __init__(self, agent: SimpleAgent):
        self.agent = agent

    def execute(self, steps:list):

        results = []

        for step in steps:
            try:
                result = self.agent.run(step)
                results.append(result)
            except Exception as e:
                results.append(str(e))

        return results
