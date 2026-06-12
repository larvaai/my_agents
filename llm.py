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
    base_url: str | None = None,
    api_key: str | None = None,
    timeout: float | None = None,
    max_tokens: int | None = None,
) -> str:
    messages = _build_messages(messages_or_system, user_prompt)
    selected_base_url = base_url or BASE_URL
    selected_api_key = api_key or API_KEY
    selected_model = model or MODEL
    selected_timeout = timeout if timeout is not None else TIMEOUT
    selected_max_tokens = max_tokens if max_tokens is not None else MAX_TOKENS
    selected_client = client

    if base_url is not None or api_key is not None or timeout is not None:
        selected_client = OpenAI(
            base_url=selected_base_url,
            api_key=selected_api_key,
            timeout=selected_timeout,
        )

    try:
        response = selected_client.chat.completions.create(
            model=selected_model,
            messages=messages,
            temperature=temperature,
            max_tokens=selected_max_tokens,
        )
    except Exception as exc:
        raise RuntimeError(
            f"LLM request failed. Check OpenAI-compatible server at {selected_base_url} "
            f"and loaded model {selected_model!r}. Details: {exc}"
        ) from exc

    return response.choices[0].message.content or ""
