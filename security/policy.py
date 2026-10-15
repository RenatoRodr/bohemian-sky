"""Fail-closed reference authorization policy; this is not an OS sandbox."""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Identity:
    principal: str
    role: str = "builder"
    parent_principal: Optional[str] = None
    trusted: bool = False  # Must be issued by a trusted host in a real runtime.


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


# Protected by basename at any depth and by directory name. Production policy
# should use host-issued resource IDs rather than rely on names alone.
GOVERNANCE = frozenset({
    "AGENTS.md", "FACTORY-BLUEPRINT.md", "POLICY.md", "PLAN.md",
    "WORK-PLAN.md", "DECISIONS.md", "RESOURCES.md", "MEMORY-CONTRACT.md",
    "SECURITY-AND-AUTHORITY.md", "PROJECT.md", "INSTRUCTIONS.md",
})
EXTERNAL = frozenset({"email_send", "message_send", "deploy", "publish",
    "purchase", "payment", "trade", "access_grant", "calendar_change",
    "paid_api", "github_write"})
FORBIDDEN = frozenset({"secret_read", "secret_write", "new_session_escalate",
    "identity_change", "exec_escalate", "approval_forge"})


def _resolved(path: Path) -> Path:
    # strict=False still resolves existing symlink ancestors, preventing a
    # lexical in-root path from escaping via a symlink.
    return path.expanduser().resolve(strict=False)


def _inside(path: Path, roots: tuple[Path, ...]) -> bool:
    resolved = _resolved(path)
    for root in roots:
        try:
            if resolved.is_relative_to(_resolved(root)):
                return True
        except (OSError, RuntimeError):
            continue
    return False


def _subset_roots(requested: tuple[Path, ...], allowed: tuple[Path, ...]) -> tuple[Path, ...]:
    """Keep only requested roots wholly contained in a single parent root."""
    result = []
    for candidate in requested:
        candidate_path = _resolved(candidate)
        if any(candidate_path.is_relative_to(_resolved(parent)) for parent in allowed):
            result.append(candidate_path)
    return tuple(result)


def authorize(identity: Identity, capability: Capability, operation: str,
              target: Optional[Path] = None, *, other_target: Optional[Path] = None,
              session_created_fixture: bool = False) -> Decision:
    if not identity.trusted or not identity.principal:
        return Decision(False, "untrusted_identity")
    if operation in FORBIDDEN:
        return Decision(False, "broker_only_or_denied")
    if operation in {"read", "write", "create", "rename", "delete"}:
        if target is None:
            return Decision(False, "missing_target")
        if operation == "read":
            ok = _inside(target, capability.read_roots + capability.write_roots)
            return Decision(ok, "workspace_read" if ok else "outside_workspace")
        if not _inside(target, capability.write_roots):
            return Decision(False, "outside_workspace")
        if target.name in GOVERNANCE and not capability.governance_write:
            return Decision(False, "governance_capability_required")
        if other_target is not None:
            if not capability.cross_project or not _inside(other_target, capability.write_roots):
                return Decision(False, "cross_project_capability_required")
        if operation == "delete" and not session_created_fixture:
            return Decision(False, "recovery_required")
        return Decision(True, "workspace_write")
    if operation in {"email_send", "message_send"}:
        granted = "email_send" in capability.external_effects or operation in capability.external_effects
        return Decision(granted, "external_capability" if granted else "approval_required")
    if operation in EXTERNAL:
        granted = operation in capability.external_effects
        return Decision(granted, "external_capability" if granted else "approval_required")
    if operation in {"git_fetch", "git_clone", "git_pull", "network_read"}:
        return Decision(capability.network_read, "network_read" if capability.network_read else "network_read_denied")
    if operation == "git_push":
        granted = capability.git_push and "git_push" in capability.external_effects
        return Decision(granted, "git_push" if granted else "git_push_capability_required")
    return Decision(False, "unknown_operation")


def child_capability(parent: Capability, requested: Capability) -> Capability:
    """Return a strict subset of the parent's authority."""
    return Capability(
        read_roots=_subset_roots(requested.read_roots, parent.read_roots + parent.write_roots),
        write_roots=_subset_roots(requested.write_roots, parent.write_roots),
        cross_project=requested.cross_project and parent.cross_project,
        governance_write=requested.governance_write and parent.governance_write,
        network_read=requested.network_read and parent.network_read,
        git_push=requested.git_push and parent.git_push,
        external_effects=frozenset(requested.external_effects & parent.external_effects),
    )
