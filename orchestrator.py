import json
import re

from agents.tool_agent import tool_agent
from tools.tool_registry import call_tool


def parse_json(text: str) -> dict:
    """
    Try to parse a JSON object from the model output.
    Fenced JSON and surrounding text are tolerated as a recovery path.
    """
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```json", "", text)
        text = re.sub(r"^```", "", text)
        text = re.sub(r"```$", "", text)
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()

        for match in re.finditer(r"\{", text):
            try:
                parsed, _ = decoder.raw_decode(text[match.start():])
            except json.JSONDecodeError:
                continue

            if isinstance(parsed, dict):
                return parsed

        raise ValueError(f"Could not parse JSON from agent output:\n{text}")


def _json_retry_message(error: Exception, agent_output: str) -> str:
    return (
        "You returned invalid JSON, so the orchestrator could not read it.\n"
        "Return exactly one valid JSON object.\n"
        "No markdown. No explanation. Do not use ```json.\n\n"
        "Valid format when using a tool:\n"
        "{\n"
        '  "action": "tool",\n'
        '  "tool": "tool_name",\n'
        '  "args": {}\n'
        "}\n\n"
        "Valid format when the task is complete:\n"
        "{\n"
        '  "action": "final",\n'
        '  "message": "response text"\n'
        "}\n\n"
        f"Parse error: {str(error)}\n\n"
        f"Your invalid output was:\n{agent_output}"
    )


def _invalid_action_retry_message() -> str:
    return (
        "Your JSON parsed successfully, but the action is invalid.\n"
        "The action must be exactly 'tool' or 'final'.\n"
        "Return corrected JSON only."
    )


def run_orchestrator(
    user_task: str,
    max_steps: int = 80,
    max_parse_errors: int = 3,
) -> str:
    """
    Main orchestration loop:
    User -> Agent -> Tool -> Agent -> Final.
    """
    messages = [
        {
            "role": "user",
            "content": user_task,
        }
    ]
    parse_error_count = 0

    for step in range(max_steps):
        print(f"\n--- STEP {step + 1} ---")

        try:
            agent_output = tool_agent(messages)
        except Exception as exc:
            return f"Agent/LLM call failed: {exc}"

        print("AGENT RAW OUTPUT:")
        print(agent_output)

        try:
            action = parse_json(agent_output)
            parse_error_count = 0
        except Exception as exc:
            parse_error_count += 1

            print("JSON PARSE ERROR:")
            print(exc)

            if parse_error_count >= max_parse_errors:
                return f"Agent returned invalid JSON too many times. Last error: {exc}"

            messages.append({
                "role": "user",
                "content": _json_retry_message(exc, agent_output),
            })
            continue

        if action.get("action") == "final":
            return action.get("message", "")

        if action.get("action") == "tool":
            tool_name = action.get("tool")
            args = action.get("args", {})

            print(f"CALL TOOL: {tool_name}")
            print(f"ARGS: {args}")

            tool_result = call_tool(tool_name, args)

            print("TOOL RESULT:")
            print(tool_result)

            messages.append({
                "role": "assistant",
                "content": agent_output,
            })

            messages.append({
                "role": "user",
                "content": json.dumps({
                    "tool_result": tool_result,
                }, ensure_ascii=False),
            })
            continue

        messages.append({
            "role": "user",
            "content": _invalid_action_retry_message(),
        })
        continue

    return "Agent exceeded the maximum number of allowed steps."
