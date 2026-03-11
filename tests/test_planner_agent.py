from agents.planner_agent import PlannerAgent

def test_plan_report():

    planner = PlannerAgent()

    steps = planner.plan("create report")

    assert steps == [
        "collect_data",
        "analyze",
        "generate_report"
    ]


def test_plan_default():

    planner = PlannerAgent()

    steps = planner.plan("say hello")

    assert steps == ["hello"]
