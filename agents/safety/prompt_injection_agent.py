from __future__ import annotations

from dataclasses import dataclass


INJECTION_PATTERNS = (
    "ignore previous instructions",
    "ignore all previous",
    "developer message",
    "system prompt",
    "reveal secrets",
    "exfiltrate",
    "override policy",
    "disable safety",
)


@dataclass
class PromptInjectionAgent:
    """Lightweight prompt-injection scanner for user/external text."""

    def run(self, text: str) -> dict:
        folded = (text or "").lower()
        hits = [pattern for pattern in INJECTION_PATTERNS if pattern in folded]
        return {
            "agent": "prompt_injection_agent",
            "status": "blocked" if hits else "pass",
            "hits": hits,
            "reason": (
                "Potential prompt-injection language detected."
                if hits
                else "No prompt-injection indicators detected."
            ),
        }
