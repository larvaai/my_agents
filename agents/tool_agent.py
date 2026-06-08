from llm import call_llm
from tools.mcp_client import build_tool_prompt
from tools.prompt_loader import render_system_prompt
from tools.skill_loader import build_skills_prompt


def tool_agent(messages: list) -> str:
    """
    Call the Tool Agent.
    """
    system_prompt = render_system_prompt(build_tool_prompt(), build_skills_prompt())
    full_messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ] + messages

    return call_llm(full_messages)
