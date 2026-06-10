from agents.role_agents import get_agent


def tool_agent(messages: list) -> str:
    """
    Call the Tool Agent.
    """
    return get_agent("tool").run(messages)
