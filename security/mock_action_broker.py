"""Offline reference broker. It has no credentials, sockets, or live provider."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re
from typing import Mapping, Optional


ACTION = "github.create_pull_request"
REQUEST_FIELDS = frozenset({
    "request_id", "action", "account", "owner", "repository", "head",
    "base", "title", "body", "expires_at",
})
SAFE_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")
SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
SAFE_BRANCH = re.compile(r"^[A-Za-z0-9._/-]{1,200}$")


@dataclass(frozen=True)
class PullRequestRequest:
    request_id: str
    action: str
    account: str
    owner: str
    repository: str
    head: str
    base: str
    title: str
    body: str
    expires_at: int

    def digest(self) -> str:
        raw = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PreparedAction:
    request: PullRequestRequest
    digest: str


@dataclass(frozen=True)
class ApprovalReceipt:
    request_id: str
    digest: str
    approver: str
    approved: bool
    issued_at: int
    expires_at: int


class SimulatedApprovalPanel:
    """Test fixture for displaying a preview and issuing fake approval receipts."""

    def __init__(self) -> None:
        self.last_preview: Optional[dict[str, str]] = None

    def issue(self, prepared: PreparedAction, *, approver: str, approved: bool,
              now: int) -> ApprovalReceipt:
        request = prepared.request
        self.last_preview = {
            "action": request.action,
            "account": request.account,
            "target": f"{request.owner}/{request.repository}:{request.base}",
            "head": request.head,
            "title": request.title,
            "body": request.body,
            "digest": prepared.digest,
        }
        return ApprovalReceipt(
            request_id=request.request_id,
            digest=prepared.digest,
            approver=approver,
            approved=approved,
            issued_at=now,
            expires_at=request.expires_at,
        )


@dataclass(frozen=True)
class BrokerResult:
    outcome: str  # execution, denial, host_failure
    reason: str
    provider_id: Optional[str] = None


@dataclass(frozen=True)
class AuditEvent:
    sequence: int
    request_id: str
    request_digest: str
    action: str
    target: str
    approver: str
    decision: str
    timestamp: int
    provider_id: Optional[str]
    outcome: str
    previous_hash: str
    event_hash: str


class MockAuditLog:
    """In-memory hash chain for behavior tests; not protected durable storage."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    @property
    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)

    def append(self, *, request_id: str, request_digest: str, action: str,
               target: str, approver: str, decision: str, timestamp: int,
               provider_id: Optional[str], outcome: str) -> None:
        previous_hash = self._events[-1].event_hash if self._events else "0" * 64
        sequence = len(self._events) + 1
        fields = {
            "sequence": sequence,
            "request_id": request_id,
            "request_digest": request_digest,
            "action": action,
            "target": target,
            "approver": approver,
            "decision": decision,
            "timestamp": timestamp,
            "provider_id": provider_id,
            "outcome": outcome,
            "previous_hash": previous_hash,
        }
        event_hash = _hash_json(fields)
        self._events.append(AuditEvent(**fields, event_hash=event_hash))

    def verify(self) -> bool:
        previous_hash = "0" * 64
        for expected_sequence, event in enumerate(self._events, start=1):
            fields = asdict(event)
            event_hash = fields.pop("event_hash")
            if event.sequence != expected_sequence or event.previous_hash != previous_hash:
                return False
            if _hash_json(fields) != event_hash:
                return False
            previous_hash = event_hash
        return True


class MockProviderFailure(RuntimeError):
    """Injected failure in the offline provider fixture."""


class MockPullRequestProvider:
    """Stores results in memory and never makes network calls."""

    def __init__(self, *, fail_next: bool = False) -> None:
        self.created: list[dict[str, str]] = []
        self.fail_next = fail_next

    def create_pull_request(self, request: PullRequestRequest) -> str:
        if self.fail_next:
            self.fail_next = False
            raise MockProviderFailure("injected mock provider failure")
        provider_id = f"mock-pr-{len(self.created) + 1}"
        self.created.append({
            "id": provider_id,
            "account": request.account,
            "owner": request.owner,
            "repository": request.repository,
            "head": request.head,
            "base": request.base,
            "title": request.title,
            "body": request.body,
        })
        return provider_id


class MockActionBroker:
    """Models exact-action approval and execution against an injected mock."""

    def __init__(self, provider: MockPullRequestProvider, *, now,
                 allowed_account: str = "fixture-account",
                 allowed_owner: str = "example",
                 allowed_repository: str = "sandbox",
                 allowed_base: str = "main",
                 audit: Optional[MockAuditLog] = None) -> None:
        self.provider = provider
        self.now = now
        self.allowed_account = allowed_account
        self.allowed_owner = allowed_owner
        self.allowed_repository = allowed_repository
        self.allowed_base = allowed_base
        self.audit = audit or MockAuditLog()
        self._consumed: set[str] = set()

    def prepare(self, raw: Mapping[str, object]) -> PreparedAction | BrokerResult:
        request, reason = _parse_request(raw)
        try:
            digest = _hash_json(dict(raw))
        except (TypeError, ValueError):
            digest = hashlib.sha256(b"unserializable-action-request").hexdigest()
        if request is None:
            self._audit_invalid(raw, digest, reason)
            return BrokerResult("denial", reason)
        prepared = PreparedAction(request=request, digest=request.digest())
        if request.request_id in self._consumed:
            self._record(prepared, "", "duplicate_request", "denial")
            return BrokerResult("denial", "duplicate_request")
        if request.action != ACTION:
            self._record(prepared, "", "unknown_action", "denial")
            return BrokerResult("denial", "unknown_action")
        if (request.account, request.owner, request.repository, request.base) != (
            self.allowed_account, self.allowed_owner, self.allowed_repository, self.allowed_base
        ):
            self._record(prepared, "", "target_not_allowed", "denial")
            self._consumed.add(request.request_id)
            return BrokerResult("denial", "target_not_allowed")
        if request.expires_at <= self.now():
            self._record(prepared, "", "request_expired", "denial")
            self._consumed.add(request.request_id)
            return BrokerResult("denial", "request_expired")
        return prepared

    def execute(self, prepared: PreparedAction,
                receipt: Optional[ApprovalReceipt]) -> BrokerResult:
        request = prepared.request
        if request.request_id in self._consumed:
            self._record(prepared, "", "duplicate_request", "denial")
            return BrokerResult("denial", "duplicate_request")
        self._consumed.add(request.request_id)
        if request.expires_at <= self.now():
            self._record(prepared, "", "request_expired", "denial")
            return BrokerResult("denial", "request_expired")
        if receipt is None:
            self._record(prepared, "", "approval_missing", "denial")
            return BrokerResult("denial", "approval_missing")
        if (prepared.digest != request.digest() or
                receipt.request_id != request.request_id or
                receipt.digest != prepared.digest or
                receipt.expires_at != request.expires_at or
                receipt.issued_at > self.now() or
                receipt.expires_at <= self.now() or
                not receipt.approver):
            self._record(prepared, receipt.approver, "approval_invalid", "denial")
            return BrokerResult("denial", "approval_invalid")
        if not receipt.approved:
            self._record(prepared, receipt.approver, "approval_rejected", "denial")
            return BrokerResult("denial", "approval_rejected")
        try:
            provider_id = self.provider.create_pull_request(request)
        except MockProviderFailure:
            self._record(prepared, receipt.approver, "mock_provider_failure", "host_failure")
            return BrokerResult("host_failure", "mock_provider_failure")
        self._record(prepared, receipt.approver, "approved", "execution", provider_id)
        return BrokerResult("execution", "created", provider_id)

    def _record(self, prepared: PreparedAction, approver: str, decision: str,
                outcome: str, provider_id: Optional[str] = None) -> None:
        request = prepared.request
        self.audit.append(
            request_id=request.request_id,
            request_digest=prepared.digest,
            action=request.action,
            target=f"{request.owner}/{request.repository}:{request.base}",
            approver=approver,
            decision=decision,
            timestamp=self.now(),
            provider_id=provider_id,
            outcome=outcome,
        )

    def _audit_invalid(self, raw: Mapping[str, object], digest: str, reason: str) -> None:
        request_id = raw.get("request_id")
        action = raw.get("action")
        self.audit.append(
            request_id=request_id if isinstance(request_id, str) else "invalid",
            request_digest=digest,
            action=action if isinstance(action, str) else "unknown",
            target="unparsed",
            approver="",
            decision=reason,
            timestamp=self.now(),
            provider_id=None,
            outcome="denial",
        )


def _parse_request(raw: Mapping[str, object]) -> tuple[Optional[PullRequestRequest], str]:
    if not isinstance(raw, Mapping):
        return None, "invalid_schema"
    try:
        if frozenset(raw) != REQUEST_FIELDS:
            return None, "invalid_schema"
    except TypeError:
        return None, "invalid_schema"
    if any(not isinstance(raw[name], str) for name in REQUEST_FIELDS - {"expires_at"}):
        return None, "invalid_field_type"
    if type(raw["expires_at"]) is not int:
        return None, "invalid_expiry_type"
    if not SAFE_REQUEST_ID.fullmatch(raw["request_id"]):
        return None, "invalid_request_id"
    if raw["action"] != ACTION:
        return None, "unknown_action"
    for name in ("account", "owner", "repository"):
        if not SAFE_NAME.fullmatch(raw[name]) or raw[name] in {".", ".."}:
            return None, "invalid_target"
    if (not SAFE_BRANCH.fullmatch(raw["head"]) or
            not SAFE_BRANCH.fullmatch(raw["base"]) or
            any(part in {"", ".", ".."} for branch in (raw["head"], raw["base"])
                for part in branch.split("/")) or
            "@{" in raw["head"] + raw["base"] or
            any(branch.endswith((".", ".lock", "/")) for branch in (raw["head"], raw["base"]))):
        return None, "invalid_branch"
    if not raw["title"] or len(raw["title"]) > 200 or len(raw["body"]) > 20_000:
        return None, "invalid_content"
    if any(ord(c) == 0 for c in raw["title"] + raw["body"]):
        return None, "invalid_content"
    return PullRequestRequest(**raw), "ok"


def _hash_json(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
