"""Fixture-testable private package transaction; provenance is caller-owned."""
import hashlib
import fcntl
import json
import os
import re
import stat
import tempfile
from pathlib import Path, PurePosixPath

HEX = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
EXPECTED = frozenset({
    "agents/factory-architect.toml", "agents/factory-auditor.toml",
    "agents/factory-builder.toml", "agents/factory-gatekeeper.toml",
    "skills/factory-build/SKILL.md", "skills/factory-build/references/PLAN.md",
    "skills/factory-build/scripts/build_check.py",
    "skills/factory-build/scripts/execution_manifest.py",
})
RULE_FILES = frozenset({"AGENTS.md", "CHATGPT-SETUP.md", "FACTORY-BLUEPRINT.md",
                        "MASTER-PROMPTS.md", "MEMORY-CONTRACT.md",
                        "PORTFOLIO-SPECIFICATION.md", "PROJECT-ARCHETYPES.md",
                        "SECURITY-AND-AUTHORITY.md"})
SOURCE_ONLY = frozenset({
    "updater/refresh/refresh_core.py",
    "updater/refresh/source_verifier.py",
})
MANIFEST_REQUIRED = frozenset({"schema_version", "selected_repository", "selected_ref",
                               "source_commit", "files"})
MANIFEST_TEMPLATE_METADATA = frozenset({"status", "source_commit_note", "source_only"})


class RefreshError(RuntimeError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _file(path):
    if path.is_symlink() or not path.is_file():
        raise RefreshError(f"missing or unsafe file: {path}")
    return path.read_bytes()


def _safe(root, relative):
    if not isinstance(relative, str) or not relative or PurePosixPath(relative).is_absolute() or any(part in ("", ".", "..") for part in relative.split("/")):
        raise RefreshError(f"unsafe path: {relative}")
    path = root
    for part in relative.split("/"):
        path = path / part
        if path.is_symlink():
            raise RefreshError(f"symlink in path: {path}")
    return path


def _atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    old_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else None
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".refresh-", delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
    try:
        if old_mode is not None: os.chmod(temporary, old_mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _manifest(manifest, repository, commit, target_map=None):
    if not isinstance(manifest, dict):
        raise RefreshError("malformed manifest schema")
    if "hooks_registration" in manifest:
        raise RefreshError("hook registration is outside updater ownership")
    keys = set(manifest)
    if not MANIFEST_REQUIRED <= keys or not keys <= MANIFEST_REQUIRED | MANIFEST_TEMPLATE_METADATA:
        raise RefreshError("malformed manifest schema")
    if manifest.get("schema_version") != 1 or manifest.get("selected_repository") != repository or manifest.get("selected_ref") != "main" or manifest.get("source_commit") != commit or not COMMIT.fullmatch(commit or ""):
        raise RefreshError("malformed manifest or wrong source identity")
    files = manifest.get("files")
    if not isinstance(files, dict) or set(files) != EXPECTED: raise RefreshError("malformed manifest file set")
    source_only = manifest.get("source_only")
    if source_only is not None:
        if not isinstance(source_only, dict) or set(source_only) != SOURCE_ONLY:
            raise RefreshError("malformed source-only manifest section")
        for name, entry in source_only.items():
            if (not isinstance(entry, dict) or set(entry) != {"sha256"} or
                    not isinstance(entry["sha256"], str) or not HEX.fullmatch(entry["sha256"])):
                raise RefreshError(f"malformed source-only manifest entry: {name}")
    if target_map is not None and (not isinstance(target_map, dict) or set(target_map) != EXPECTED):
        raise RefreshError("malformed local target mapping")
    targets = set()
    for name, entry in files.items():
        if not isinstance(entry, dict) or set(entry) != {"sha256"} or not isinstance(entry["sha256"], str) or not HEX.fullmatch(entry["sha256"]):
            raise RefreshError(f"malformed manifest entry: {name}")
        if target_map is not None:
            target = target_map[name]
            expected_prefix = ".codex/agents/" if name.startswith("agents/") else ".agents/skills/"
            if (not isinstance(target, str) or not target or target.startswith("/") or
                    any(part in ("", ".", "..") for part in target.split("/")) or
                    not target.startswith(expected_prefix) or target in targets):
                raise RefreshError(f"unsafe or duplicate local target: {target}")
            targets.add(target)
    return files


def _source(source_root, files):
    actual = set()
    for path in source_root.rglob("*"):
        if path.is_symlink(): raise RefreshError(f"unexpected source symlink: {path}")
        if path.is_file(): actual.add(path.relative_to(source_root).as_posix())
    if actual != set(files): raise RefreshError(f"source file set differs: missing={sorted(set(files)-actual)}, extra={sorted(actual-set(files))}")
    output = {}
    for name, entry in files.items():
        data = _file(_safe(source_root, name))
        if digest(data) != entry["sha256"]: raise RefreshError(f"source hash differs: {name}")
        output[name] = data
    return output


def _compose(composer, rules_root):
    if composer is None: return None
    if rules_root is None: raise RefreshError("rules root required for composer receipt verification")
    receipt = composer()
    if not isinstance(receipt, dict) or not isinstance(receipt.get("loaded_commit"), str) or not COMMIT.fullmatch(receipt["loaded_commit"]) or not isinstance(receipt.get("files"), dict) or set(receipt["files"]) != RULE_FILES: raise RefreshError("invalid rules receipt")
    for name, claimed in receipt["files"].items():
        if not isinstance(claimed, str) or not HEX.fullmatch(claimed) or digest(_file(_safe(Path(rules_root), name))) != claimed: raise RefreshError(f"rules receipt hash differs: {name}")
    return receipt


def _installed_receipt(raw, repository, recovery_targets):
    try:
        value = json.loads(raw)
        if (not isinstance(value, dict) or set(value) != {"repository", "commit", "installed_hashes", "updater_version"} or
                value["repository"] != repository or not isinstance(value["commit"], str) or
                not COMMIT.fullmatch(value["commit"]) or not isinstance(value["installed_hashes"], dict) or
                not isinstance(value["updater_version"], str) or
                not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,63}", value["updater_version"]) or
                set(value["installed_hashes"]) != recovery_targets or
                any(not isinstance(d, str) or not HEX.fullmatch(d) for d in value["installed_hashes"].values())):
            raise ValueError()
        return value
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise RefreshError("invalid installed receipt") from exc


def refresh(source_root, installed_root, manifest, *, repository, commit, receipt_path, target_map, composer=None, rules_root=None, fail_after=None, bootstrap_hashes=None, updater_version="s44-candidate.1"):
    if not isinstance(updater_version, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,63}", updater_version):
        raise RefreshError("invalid updater version")
    source_root, installed_root, receipt_path = map(Path, (source_root, installed_root, receipt_path))
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    with (receipt_path.parent / (receipt_path.name + ".lock")).open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try: return _refresh_locked(source_root, installed_root, manifest, repository=repository, commit=commit, receipt_path=receipt_path, target_map=target_map, composer=composer, rules_root=rules_root, fail_after=fail_after, bootstrap_hashes=bootstrap_hashes, updater_version=updater_version)
        finally: fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def _refresh_locked(source_root, installed_root, manifest, *, repository, commit, receipt_path, target_map, composer, rules_root, fail_after, bootstrap_hashes, updater_version):
    journal = receipt_path.parent / (receipt_path.name + ".journal")
    if not isinstance(target_map, dict) or set(target_map) != EXPECTED:
        raise RefreshError("malformed local target mapping")
    recovery_targets = frozenset(target_map.values())
    if journal.exists(): recover(installed_root, receipt_path, target_map=target_map)
    files = _manifest(manifest, repository, commit, target_map); source = _source(source_root, files)
    targets = {name: _safe(installed_root, target_map[name]) for name in files}
    old = {}
    for name, entry in files.items():
        path = targets[name]; target = target_map[name]
        if path.exists(): old[target] = _file(path)
        else: old[target] = None
    prior_receipt = _file(receipt_path) if receipt_path.exists() else None
    if prior_receipt is None:
        expected_hashes = bootstrap_hashes
        if not isinstance(expected_hashes, dict) or set(expected_hashes) != recovery_targets or any(not isinstance(value, str) or not HEX.fullmatch(value) for value in expected_hashes.values()):
            raise RefreshError("malformed bootstrap installed baseline")
        for target, value in old.items():
            if value is None or digest(value) != expected_hashes[target]: raise RefreshError(f"local installed conflict: {target}")
    else:
        previous = _installed_receipt(prior_receipt, repository, recovery_targets); expected = previous["installed_hashes"]
        for target, data in old.items():
            if data is None or digest(data) != expected[target]: raise RefreshError(f"local installed conflict: {target}")
    if prior_receipt and previous["commit"] == commit:
        return {"status": "noop", "package_receipt": previous, "rules_receipt": _compose(composer, rules_root)}
    new = {target_map[name]: source[name] for name in files}
    rules_receipt = _compose(composer, rules_root)
    package_receipt = {"repository": repository, "commit": commit, "updater_version": updater_version, "installed_hashes": {path: digest(data) for path, data in new.items()}}
    journal_data = {"old": {path: (value.hex() if value is not None else None) for path, value in old.items()}, "receipt": prior_receipt.hex() if prior_receipt else None}
    _atomic(journal, json.dumps(journal_data).encode())
    try:
        writes = list(new.items()) + [("__receipt__", (json.dumps(package_receipt, indent=2) + "\n").encode())]
        for index, (target, data) in enumerate(writes, 1):
            if target == "__receipt__": _atomic(receipt_path, data)
            else: _atomic(_safe(installed_root, target), data)
            if fail_after == index: raise RefreshError(f"injected interruption after {target}")
        for target, data in new.items():
            if _file(_safe(installed_root, target)) != data: raise RefreshError(f"post-install verification failed: {target}")
    except Exception:
        recover(installed_root, receipt_path, target_map=target_map); raise
    journal.unlink()
    return {"status": "updated", "package_receipt": package_receipt, "rules_receipt": rules_receipt}


def recover(installed_root, receipt_path, *, target_map):
    installed_root, receipt_path = Path(installed_root), Path(receipt_path); journal = receipt_path.parent / (receipt_path.name + ".journal")
    if not journal.exists(): return False
    if not isinstance(target_map, dict) or set(target_map) != EXPECTED:
        raise RefreshError("malformed local target mapping")
    recovery_targets = frozenset(target_map.values())
    data = json.loads(_file(journal))
    if not isinstance(data, dict) or set(data) != {"old", "receipt"} or not isinstance(data["old"], dict) or set(data["old"]) != recovery_targets or not all(value is None or isinstance(value, str) for value in data["old"].values()) or (data["receipt"] is not None and not isinstance(data["receipt"], str)): raise RefreshError("invalid recovery journal target set")
    for relative, encoded in data["old"].items():
        path = _safe(installed_root, relative)
        if encoded is None: path.unlink(missing_ok=True)
        else: _atomic(path, bytes.fromhex(encoded))
    if data["receipt"] is None: receipt_path.unlink(missing_ok=True)
    else: _atomic(receipt_path, bytes.fromhex(data["receipt"]))
    for relative, encoded in data["old"].items():
        path = _safe(installed_root, relative)
        if encoded is None:
            if path.exists(): raise RefreshError(f"rollback verification failed: {relative}")
        elif _file(path) != bytes.fromhex(encoded): raise RefreshError(f"rollback verification failed: {relative}")
    journal.unlink(); return True
