from __future__ import annotations


class KernelError(RuntimeError):
    """Base error raised by the core kernel layer."""


class KernelConfigurationError(KernelError):
    """Raised when kernel configuration cannot be loaded or applied."""


class CapabilityNotFoundError(KernelError):
    """Raised when a required capability is not registered."""


class FeatureDisabledError(KernelError):
    """Raised when a requested feature is disabled by configuration."""


class PortContractError(KernelError):
    """Raised when a port or adapter returns a value outside its contract."""
