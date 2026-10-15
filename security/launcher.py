"""Fail-closed launcher boundary contract; it intentionally starts no process.

Python callers can forge these booleans. A production implementation needs a
host-owned broker and OS-enforced sandbox before this gate is meaningful.
"""
from pathlib import Path
from typing import Optional
from policy import Identity, Capability, Decision, authorize


class LauncherUnavailable(RuntimeError):
    pass


def require_production_boundary(*, trusted_runtime: bool,
                                os_sandbox_verified: bool,
                                audit_recovery_broker: bool,
                                connector_broker: bool = False) -> None:
    if not all((trusted_runtime, os_sandbox_verified, audit_recovery_broker, connector_broker)):
        raise LauncherUnavailable(
            "trusted host identity, verified OS sandbox, protected audit/recovery, "
            "and connector brokers are required; prototype will not spawn commands"
        )


def preview_authorization(identity: Identity, capability: Capability,
                          operation: str, target: Optional[Path] = None) -> Decision:
    """Evaluate policy for design/tests only. Never authorize execution."""
    return authorize(identity, capability, operation, target)
