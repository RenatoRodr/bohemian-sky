"""Security v3 policy prototype. Not a sandbox or trusted launcher."""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Identity:
    """Identity fields are expected from a trusted host in production."""
    principal: str
    parent_principal: Optional[str] = None
    trusted: bool = False


@dataclass(frozen=True)
class Capability:
    read_roots: tuple[Path, ...] = ()
    write_roots: tuple[Path, ...] = ()
    cross_project: bool = False
    governance_write: bool = False
    network_read: bool = False
    git_push: bool = False
    external_effects: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str


GOVERNANCE = {
    "AGENTS.md", "FACTORY-BLUEPRINT.md", "POLICY.md", "PLAN.md",
    "DECISIONS.md", "RESOURCES.md", "MEMORY-CONTRACT.md",
}
EXTERNAL = {"email_send", "message_send", "deploy", "publish", "purchase",
            "payment", "trade", "access_grant", "calendar_change", "paid_api"}


def _inside(path: Path, roots: tuple[Path, ...]) -> bool:
    resolved = path.resolve()
    return any(resolved.is_relative_to(root.resolve()) for root in roots)


def authorize(identity: Identity, capability: Capability, operation: str,
              target: Optional[Path] = None, *, other_target: Optional[Path] = None,
              session_created_fixture: bool = False) -> Decision:
    """Check a requested capability; callers must supply trusted identity data."""
    if not identity.trusted:
        return Decision(False, "untrusted_identity")
    if operation in {"read", "write", "create", "rename", "delete"}:
        if target is None:
            return Decision(False, "missing_target")
        if operation == "read":
            ok = _inside(target, capability.read_roots + capability.write_roots)
            return Decision(ok, "workspace_read" if ok else "outside_workspace")
        ok = _inside(target, capability.write_roots)
        if not ok:
            return Decision(False, "outside_workspace")
        if target.name in GOVERNANCE and not capability.governance_write:
            return Decision(False, "governance_capability_required")
        if other_target is not None:
            if not capability.cross_project or not _inside(other_target, capability.write_roots):
                return Decision(False, "cross_project_capability_required")
        if operation == "delete" and not session_created_fixture:
            return Decision(False, "recovery_required")
        return Decision(True, "workspace_write")
    if operation == "git_fetch":
        return Decision(capability.network_read, "network_read" if capability.network_read else "network_read_denied")
    if operation == "git_push":
        return Decision(capability.git_push, "git_push_capability_required" if not capability.git_push else "git_push")
    if operation in EXTERNAL:
        ok = operation in capability.external_effects
        return Decision(ok, "external_capability" if ok else "approval_required")
    if operation in {"secret_read", "secret_write", "new_session_escalate", "identity_change", "exec_escalate"}:
        return Decision(False, "broker_only_or_denied")
    return Decision(False, "unknown_operation")


def child_capability(parent: Capability, requested: Capability) -> Capability:
    """Return a subset; never add roots or booleans not held by the parent."""
    return Capability(
        read_roots=tuple(r for r in requested.read_roots if _inside(r, parent.read_roots + parent.write_roots)),
        write_roots=tuple(r for r in requested.write_roots if _inside(r, parent.write_roots)),
        cross_project=requested.cross_project and parent.cross_project,
        governance_write=requested.governance_write and parent.governance_write,
        network_read=requested.network_read and parent.network_read,
        git_push=requested.git_push and parent.git_push,
        external_effects=frozenset(requested.external_effects & parent.external_effects),
    )
