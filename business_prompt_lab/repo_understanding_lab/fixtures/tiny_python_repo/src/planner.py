DEFAULT_STEPS = ["understand", "plan", "verify"]


class PlannerAgent:
    """Creates a simple ordered plan for a user task."""

    def plan(self, task: str) -> list[str]:
        if not task.strip():
            return ["ask for task"]
        return [*DEFAULT_STEPS, f"answer: {task}"]

