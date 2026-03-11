class PlannerAgent:

    def plan(self, task:str):

        task = task.lower()

        if "report" in task:
            return [
                "collect_data",
                "analyze",
                "generate_report"
            ]

        if "math" in task:
            return [
                "add"
            ]

        return ["hello"]
