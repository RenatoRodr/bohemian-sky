#!/usr/bin/env python3
"""Generic SessionStart adapter. Local roots and composer are injected by a trusted adapter."""
import json
import fcntl
import os
import re
import stat
import tempfile
from pathlib import Path

from refresh_core import RefreshError, RULE_FILES, RECOVERY_TARGETS, _file, _safe, digest, refresh
from source_verifier import REPOSITORY, github_review, verify

UPDATER_VERSION = "s39-candidate.1"
SAFE_UPDATER_VERSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,63}\Z")


def _identity(path, *, directory):
    try:
        info = path.lstat()
    except OSError:
        return None
    expected_type = stat.S_ISDIR if directory else stat.S_ISREG
    if stat.S_ISLNK(info.st_mode) or not expected_type(info.st_mode):
        return None
    return (info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode))


def _ensure_cache_root(cache_root):
    created = False
    identity = _identity(cache_root, directory=True)
    if identity is None:
        try:
            cache_root.lstat()
        except FileNotFoundError:
            try:
                cache_root.mkdir(parents=True)
                created = True
            except FileExistsError:
                pass
        identity = _identity(cache_root, directory=True)
        if identity is None:
            raise RefreshError("rules cache root is not a safe directory")
    return created, identity


def _claim_cache_entry(cache_root, name):
    """Atomically claim a new cache directory; never adopts an existing name."""
    final = cache_root / name
    final.mkdir()
    identity = _identity(final, directory=True)
    if identity is None:
        raise RefreshError("claimed rules cache entry is unsafe")
    return final, identity


def _write_cache_file(source, destination, owned_files):
    source_info = source.lstat()
    if stat.S_ISLNK(source_info.st_mode) or not stat.S_ISREG(source_info.st_mode):
        raise RefreshError(f"unsafe composed cache file: {source.name}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(destination, flags, stat.S_IMODE(source_info.st_mode))
    with os.fdopen(descriptor, "wb") as stream:
        info = os.fstat(stream.fileno())
        identity = (info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode))
        owned_files.append((destination, identity))
        with source.open("rb") as input_stream:
            while True:
                block = input_stream.read(1024 * 1024)
                if not block:
                    break
                stream.write(block)
        stream.flush()
        os.fsync(stream.fileno())


def _rollback_cache_entry(final, final_identity, owned_files):
    for path, identity in reversed(owned_files):
        if _identity(path, directory=False) == identity:
            try:
                path.unlink()
            except OSError:
                pass
    if final is not None and _identity(final, directory=True) == final_identity:
        try:
            final.rmdir()
        except OSError:
            pass


def _remove_created_cache_root(cache_root, created, identity):
    if created and _identity(cache_root, directory=True) == identity:
        try:
            cache_root.rmdir()
        except OSError:
            pass


def run(event, *, factory, package_repo, installed_commit, review_provider,
        receipt_path, rules_repo, rules_source, rules_manifest, cache_root,
        rules_composer=None, bootstrap_hashes=None, fetch_rules=True):
    if event.get('hook_event_name') != 'SessionStart':
        raise RefreshError('unexpected hook event')
    if not Path(event.get('cwd', '')).expanduser().resolve().is_relative_to(Path(factory).resolve()):
        return {'continue': True}
    receipt_path = Path(receipt_path)
    # Lock files intentionally persist: unlinking a flocked inode lets another
    # process create and lock a different inode while this lock is still held.
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    with (receipt_path.parent / (receipt_path.name + '.session.lock')).open('a+b') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            return _run_locked(event, factory=factory, package_repo=package_repo,
                               installed_commit=installed_commit, review_provider=review_provider,
                               receipt_path=receipt_path, rules_repo=rules_repo,
                               rules_source=rules_source, rules_manifest=rules_manifest,
                               cache_root=cache_root, rules_composer=rules_composer,
                               bootstrap_hashes=bootstrap_hashes, fetch_rules=fetch_rules)
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def _run_locked(event, *, factory, package_repo, installed_commit, review_provider,
                receipt_path, rules_repo, rules_source, rules_manifest, cache_root,
                rules_composer, bootstrap_hashes, fetch_rules):
    """Check package, stage rules, then commit package and publish rules cache.

    All roots and the trusted review provider are injected for fixture tests.
    The on-disk receipt owns the installed commit once a package is installed;
    bootstrap pin is only for the first run.
    """
    factory, receipt_path, cache_root = map(Path, (factory, receipt_path, cache_root))
    if event.get("hook_event_name") != "SessionStart":
        raise RefreshError("unexpected hook event")
    cwd = Path(event.get("cwd", "")).expanduser().resolve()
    if not cwd.is_relative_to(factory.resolve()):
        return {"continue": True}
    reported_updater_version = UPDATER_VERSION
    if receipt_path.exists():
        try:
            receipt = json.loads(receipt_path.read_text())
            if (not isinstance(receipt, dict) or set(receipt) != {"repository", "commit", "installed_hashes", "updater_version"} or
                    receipt["repository"] != REPOSITORY or not isinstance(receipt["commit"], str) or
                    not re.fullmatch(r"[0-9a-f]{40}", receipt["commit"]) or
                    not isinstance(receipt.get("updater_version"), str) or
                    not SAFE_UPDATER_VERSION.fullmatch(receipt["updater_version"])):
                raise ValueError("schema")
            reported_updater_version = receipt["updater_version"]
            installed_commit = receipt["commit"]
            hashes = receipt["installed_hashes"]
            if not isinstance(hashes, dict) or set(hashes) != RECOVERY_TARGETS or any(
                    not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
                    for value in hashes.values()):
                raise ValueError("target set")
            for relative, expected in hashes.items():
                if digest(_file(_safe(factory, relative))) != expected:
                    raise RefreshError(f"local installed conflict: {relative}")
        except (ValueError, KeyError, TypeError) as exc:
            raise RefreshError("installed package receipt invalid") from exc
    commit, manifest, source = verify(package_repo, installed_commit,
                                      review_provider)
    cache_root_created = False
    cache_root_identity = None
    final = None
    final_identity = None
    owned_cache_files = []
    with tempfile.TemporaryDirectory(prefix="factory-refresh-") as folder:
        stage = Path(folder)
        source_root = stage / "package"
        source_root.mkdir()
        if source is not None:
            for name, data in source.items():
                path = source_root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        rule_cache = stage / "cache"
        rule_cache.mkdir()
        if not callable(rules_composer):
            raise RefreshError("trusted local rules composer unavailable")
        composed = rules_composer(event, factory=factory, repo=rules_repo,
                                 source_dir=rules_source,
                                 manifest_path=rules_manifest,
                                 cache_root=rule_cache, fetch=fetch_rules)
        sessions = list(rule_cache.iterdir())
        if len(sessions) != 1:
            raise RefreshError("rules composer produced no unique session")
        session = sessions[0]
        rules_receipt = json.loads((session / "source-receipt.json").read_text())
        commits = [rules_receipt.get(key) for key in
                   ("loaded_commit", "observed_github_commit", "github_commit")]
        if any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value)
               for value in commits) or len(set(commits)) != 1:
            raise RefreshError("rules source commits differ or are invalid")
        if any(rules_receipt.get(key) is not None for key in
               ("degraded_reason", "fetch_error", "pending_github_commit")):
            raise RefreshError("rules source check degraded or pending")
        if set(rules_receipt.get("files", {})) != RULE_FILES:
            raise RefreshError("rules receipt file set differs")
        for name, expected in rules_receipt["files"].items():
            if digest((session / name).read_bytes()) != expected:
                raise RefreshError(f"rules receipt hash differs: {name}")
        # Match the exact SessionStart composer receipt, not a reduced fixture schema.
        required = {"loaded_commit", "observed_github_commit", "github_commit", "pinned_commit",
                    "pending_github_commit", "source", "degraded_reason", "fetch_error",
                    "created_at_utc", "files"}
        if set(rules_receipt) != required:
            raise RefreshError("rules receipt schema differs")
        for key in ("loaded_commit", "observed_github_commit", "github_commit", "pinned_commit"):
            if not isinstance(rules_receipt.get(key), str) or not re.fullmatch(r"[0-9a-f]{40}", rules_receipt[key]):
                raise RefreshError("rules receipt commit invalid")
        if rules_receipt["loaded_commit"] != rules_receipt["github_commit"] or rules_receipt["observed_github_commit"] != rules_receipt["github_commit"]:
            raise RefreshError("rules source commits differ")
        if rules_receipt["source"] not in ("GitHub online", "verified cached GitHub ref"):
            raise RefreshError("rules source is not verified and online")
        if not isinstance(rules_receipt["created_at_utc"], str) or not re.fullmatch(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?\+00:00", rules_receipt["created_at_utc"]):
            raise RefreshError("rules receipt timestamp invalid")
        try:
            from datetime import datetime
            datetime.fromisoformat(rules_receipt["created_at_utc"])
        except ValueError as exc:
            raise RefreshError("rules receipt timestamp invalid") from exc
        if not isinstance(rules_receipt["files"], dict) or set(rules_receipt["files"]) != RULE_FILES or any(
                not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
                for value in rules_receipt["files"].values()):
            raise RefreshError("rules receipt file set or hashes invalid")
        if any(rules_receipt[key] is not None for key in ("degraded_reason", "fetch_error", "pending_github_commit")):
            raise RefreshError("rules source check degraded or pending")
        try:
            cache_root_created, cache_root_identity = _ensure_cache_root(cache_root)
            try:
                final, final_identity = _claim_cache_entry(cache_root, session.name)
            except FileExistsError as exc:
                raise RefreshError("rules cache name collision") from exc
            for path in sorted(session.iterdir()):
                _write_cache_file(path, final / path.name, owned_cache_files)
            context = composed["hookSpecificOutput"]["additionalContext"]
            composed["hookSpecificOutput"]["additionalContext"] = context.replace(
                str(session), str(final))
            if source is not None:
                package_result = refresh(source_root, factory, manifest, repository=REPOSITORY,
                                         commit=commit, receipt_path=receipt_path,
                                         composer=lambda: rules_receipt, rules_root=final,
                                         bootstrap_hashes=bootstrap_hashes,
                                         updater_version=UPDATER_VERSION)
                reported_updater_version = package_result["package_receipt"]["updater_version"]
        except Exception:
            _rollback_cache_entry(final, final_identity, owned_cache_files)
            _remove_created_cache_root(cache_root, cache_root_created,
                                       cache_root_identity)
            raise
        composed["hookSpecificOutput"]["additionalContext"] += (
            f" Installed updater version: {reported_updater_version}; package commit: {commit}."
        )
        return composed
