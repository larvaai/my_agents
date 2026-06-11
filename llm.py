import os
from typing import Any

from openai import OpenAI

from tools.env_loader import load_project_env


load_project_env()

DEFAULT_BASE_URL = "http://localhost:1234/v1"
DEFAULT_API_KEY = "lm-studio"
DEFAULT_MODEL = "qwen3.5-9b-claude-4.6-opus-uncensored-distilled"
# DEFAULT_MODEL = "google/gemma-4-26b-a4b-qat"
DEFAULT_TIMEOUT = 600.0
DEFAULT_MAX_TOKENS = 2048

BASE_URL = os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL)
API_KEY = os.getenv("LLM_API_KEY", DEFAULT_API_KEY)
MODEL = os.getenv("LLM_MODEL", DEFAULT_MODEL)
TIMEOUT = float(os.getenv("LLM_TIMEOUT", str(DEFAULT_TIMEOUT)))
MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", str(DEFAULT_MAX_TOKENS)))


client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
    timeout=TIMEOUT,
)


def _build_messages(messages_or_system: Any, user_prompt: str | None) -> list[dict[str, str]]:
    if user_prompt is None:
        if not isinstance(messages_or_system, list):
            raise TypeError("call_llm(messages) expects a list of chat messages.")
        return messages_or_system

    return [
        {"role": "system", "content": str(messages_or_system)},
        {"role": "user", "content": user_prompt},
    ]


def call_llm(
    messages_or_system: Any,
    user_prompt: str | None = None,
    model: str | None = None,
    temperature: float = 0.2,
) -> str:
    messages = _build_messages(messages_or_system, user_prompt)

    try:
        response = client.chat.completions.create(
            model=model or MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=MAX_TOKENS,
        )
    except Exception as exc:
        raise RuntimeError(
            f"LLM request failed. Check LM Studio at {BASE_URL} and loaded model "
            f"{model or MODEL!r}. Details: {exc}"
        ) from exc

    return response.choices[0].message.content or ""
