#!/usr/bin/env python3
"""Fail-closed core for direct, reviewed Codex JSONL conversation export.

This module never creates a transcript file. A caller supplies private target
configuration, a live Drive folder verifier, and a writer that sends bytes
directly to the target folder.
"""

import hashlib
import json
import os
import re
import stat
import time
import ctypes
from dataclasses import dataclass
from pathlib import Path

REDACTED = "[REDACTED_CREDENTIAL]"
MAX_SOURCE_BYTES = 100 * 1024 * 1024


@dataclass(frozen=True)
class ArchiveTarget:
    folder_id: str
    owner_email: str
    mount: Path

PATTERNS = (
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----", re.S),
    re.compile(r"(?i)\b(?:authorization\s*[:=]\s*)?bearer\s+[A-Za-z0-9._~+/-]{8,}"),
    re.compile(r'''(?i)\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|password|passwd|recovery[_-]?code)\b["']?\s*[:=]\s*(?:"[^"]+"|'[^']+')'''),
    re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|password|passwd|recovery[_-]?code)\b\s*[:=]\s*[\"']?[^\s\"',;}{]{4,}"),
    re.compile(r"(?i)[\"'](?:api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|password|passwd|recovery[_-]?code)[\"']\s*[:=]\s*[\"']?[^\s\"',;}{]{4,}"),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16})\b"),
    re.compile(r"(?i)https?://[^\s/@:]+:[^\s/@]+@"),
)
SECRET_KEY = re.compile(r"(?i)^(?:api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|password|passwd|recovery[_-]?code|authorization|private[_-]?key)$")


class CaptureError(RuntimeError):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def redact(value):
    if isinstance(value, str):
        for pattern in PATTERNS:
            value = pattern.sub(REDACTED, value)
        return value
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            safe_key = redact(key)
            if safe_key in result:
                raise CaptureError("redaction would collapse distinct JSON keys")
            result[safe_key] = REDACTED if SECRET_KEY.fullmatch(key) else redact(item)
        return result
    return value


def prepare(source, record_limit=None, start_record=1):
    """Return in-memory bytes and content-free receipt; never print content."""
    source = Path(source)
    fd = os.open(str(source), os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_SOURCE_BYTES:
            raise CaptureError("source is not a bounded regular file")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            raw = stream.read(MAX_SOURCE_BYTES + 1)
    finally:
        os.close(fd)
    if not raw or len(raw) > MAX_SOURCE_BYTES:
        raise CaptureError("source is empty or too large")
    if not isinstance(start_record, int) or start_record < 1:
        raise CaptureError("invalid start record")
    if record_limit is not None:
        if not isinstance(record_limit, int) or record_limit < start_record:
            raise CaptureError("invalid record limit")
        lines = raw.splitlines(keepends=True)
        if len(lines) < record_limit or not lines[record_limit - 1].endswith(b"\n"):
            raise CaptureError("reviewed record range is unavailable or incomplete")
        raw = b"".join(lines[start_record - 1:record_limit])
    elif start_record != 1:
        raise CaptureError("a range start requires an end record")
    records = []
    try:
        for line in raw.splitlines():
            item = json.loads(line)
            if not isinstance(item, dict):
                raise CaptureError("source has a non-object record")
            records.append(redact(item))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CaptureError("source has a malformed JSONL record") from exc
    payload = b"".join((json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8") for item in records)
    # Pattern scans are triage only. Unknown or fragmented secrets need review.
    scan_text = payload.decode("utf-8").replace(REDACTED, "")
    if any(pattern.search(scan_text) for pattern in PATTERNS):
        raise CaptureError("known credential pattern remained after redaction")
    return payload, {"source_sha256": sha(raw), "output_sha256": sha(payload),
                     "records": len(records), "bytes": len(payload),
                     "review_required": True, "source_is_prefix": record_limit is not None and start_record == 1,
                     "source_start_record": start_record,
                     "source_end_record": record_limit if record_limit is not None else len(records)}


def verify_destination(metadata, target, now=None):
    """Validate a fresh, explicit Drive metadata response, including ACL."""
    now = time.time() if now is None else now
    if not isinstance(metadata, dict) or metadata.get("id") != target.folder_id:
        raise CaptureError("destination folder identity is unverified")
    if metadata.get("mime_type") != "application/vnd.google-apps.folder":
        raise CaptureError("destination is not a Drive folder")
    if metadata.get("account_email") != target.owner_email:
        raise CaptureError("Drive account identity is unverified")
    checked = metadata.get("checked_at_epoch")
    if not isinstance(checked, (int, float)) or not 0 <= now - checked <= 30:
        raise CaptureError("destination check is not fresh")
    permissions = metadata.get("permissions")
    if not isinstance(permissions, list) or len(permissions) != 1 or permissions[0] != {"type": "user", "role": "owner", "emailAddress": target.owner_email}:
        raise CaptureError("destination is not confirmed owner-only")


def export(source, target, review, verify_folder, write_direct, now=None, record_limit=None, start_record=1):
    """Write once to the verified folder; no retry or intermediate file.

    review must be an explicit human review of the exact native source and
    prepared output. The caller must supply a live verifier and direct writer.
    Neither function may persist the payload outside the restricted folder.
    """
    payload, receipt = prepare(source, record_limit=record_limit, start_record=start_record)
    if not isinstance(review, dict) or review.get("reviewer") != target.owner_email or review.get("decision") != "APPROVED" or review.get("source_sha256") != receipt["source_sha256"] or review.get("output_sha256") != receipt["output_sha256"]:
        raise CaptureError("exact source and output have not been reviewed")
    metadata = verify_folder()
    verify_destination(metadata, target, now=now)
    result = write_direct(target.folder_id, payload)
    if not isinstance(result, dict) or result.get("parent_id") != target.folder_id or not (result.get("id") or result.get("local_name")):
        raise CaptureError("direct archive write was not confirmed")
    if result.get("id"):
        return {**receipt, "status": "REMOTE_WRITTEN", "file_id": result["id"]}
    return {**receipt, "status": "LOCAL_WRITTEN_PENDING_SYNC", "local_name": result["local_name"]}


def write_mounted(folder_id, payload, name, target):
    """Create one file directly inside the owner-only Drive mount.

    The caller must have just verified the live Drive account and effective
    folder permissions. This function independently verifies the mounted
    folder's Drive ID, Unix owner and permissions before opening the file.
    """
    if folder_id != target.folder_id or not re.fullmatch(r"project-factory-chat--[a-zA-Z0-9_-]{1,100}\.jsonl", name):
        raise CaptureError("unsafe archive target")
    fd = os.open(str(target.mount), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise CaptureError("mounted folder ownership or permissions changed")
        libc = ctypes.CDLL(None, use_errno=True)
        item_id = ctypes.create_string_buffer(256)
        length = libc.fgetxattr(fd, b"com.google.drivefs.item-id#S", item_id, len(item_id), 0, 0)
        if length < 0 or item_id.raw[:length].decode("utf-8") != target.folder_id:
            raise CaptureError("mounted Drive folder ID changed")
        out = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
        try:
            with os.fdopen(out, "wb", closefd=False) as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(out)
        finally:
            os.close(out)
        return {"local_name": name, "parent_id": target.folder_id, "local_written": True}
    finally:
        os.close(fd)
