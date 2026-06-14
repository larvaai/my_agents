from src.planner import PlannerAgent


def test_planner_adds_answer_step():
    planner = PlannerAgent()
    assert planner.plan("demo")[-1] == "answer: demo"

