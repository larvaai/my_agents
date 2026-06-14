from planner import PlannerAgent


def run_app(question: str) -> str:
    planner = PlannerAgent()
    steps = planner.plan(question)
    return " -> ".join(steps)


if __name__ == "__main__":
    print(run_app("ship the feature"))

