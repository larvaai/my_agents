from __future__ import annotations

from typing import Any, Protocol

from core.kernel import AgentKernel
from core.schemas import FeatureDescriptor


class FeatureModule(Protocol):
    descriptor: FeatureDescriptor

    def install(self, kernel: AgentKernel, settings: dict[str, Any]) -> None:
        ...
