"""Unactivated launcher contract / safe prototype.

This prototype deliberately refuses to spawn commands: Python process-local
identity is forgeable and there is no OS sandbox or durable recovery broker.
"""
from pathlib import Path
from typing import Optional
from policy import Identity, Capability, Decision, authorize


class LauncherUnavailable(RuntimeError):
    pass


def require_production_boundary(*, trusted_runtime: bool,
                                os_sandbox_verified: bool,
                                audit_recovery_broker: bool) -> None:
    if not (trusted_runtime and os_sandbox_verified and audit_recovery_broker):
        raise LauncherUnavailable(
            "trusted runtime, verified OS sandbox, and protected audit/recovery broker required"
        )


def preview_authorization(identity: Identity, capability: Capability,
                          operation: str, target: Optional[Path] = None) -> Decision:
    """Evaluate policy for tests/design review. Never execute the operation."""
    return authorize(identity, capability, operation, target)
