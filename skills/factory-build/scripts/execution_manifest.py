#!/usr/bin/env python3
"""Create and finish one Factory build-attempt execution manifest."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

FINAL_STATES = {"passed", "failed", "blocked", "interrupted"}
FAILURE_CLASSES = {"none", "hard_failure", "timeout", "malformed", "ambiguous", "partial", "scope", "blocked", "inconsistent"}


def now():
    return datetime.now(timezone.utc).isoformat()


def manifest_path(root, step_id, attempt):
    if not re.fullmatch(r"S[1-9][0-9]*", step_id) or attempt < 1:
        raise ValueError("step must be S<n> and attempt must be positive")
    root = Path(root).resolve(strict=True)
    if not (root / "control" / "PROJECT.md").is_file():
        raise ValueError("project root must contain control/PROJECT.md")
    return root / "work" / "build-evidence" / step_id / f"attempt-{attempt}" / "execution.json"


def reference(root, value):
    if not value:
        return None
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("evidence references must be project-relative paths")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("evidence reference escapes project")
    return path.as_posix()


def start(args):
    path = manifest_path(args.project_root, args.step_id, args.attempt)
    root = Path(args.project_root).resolve()
    if path.exists():
        raise ValueError("execution manifest already exists; preserve the attempt")
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "schema_version": 1,
        "project_id": args.project_id,
        "task_id": args.task_id,
        "step_id": args.step_id,
        "attempt": args.attempt,
        "started_at": now(),
        "ended_at": None,
        "state": "in_progress",
        "role": args.role,
        "runtime": args.runtime,
        "model_id": args.model_id or "unknown",
        "reasoning_effort": args.reasoning_effort or "unknown",
        "role_profile": args.role_profile,
        "snapshot_path": reference(root, args.snapshot_path),
        "change_inventory_path": None,
        "handback_path": reference(root, args.handback_path),
        "verification_refs": [],
        "failure_class": None,
        "retry_of_attempt": args.retry_of_attempt,
        "approval_ref": args.approval_ref,
    }
    if args.retry_of_attempt is not None and not 1 <= args.retry_of_attempt < args.attempt:
        raise ValueError("retry must refer to an earlier attempt")
    with path.open("x", encoding="utf-8") as stream:
        json.dump(row, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(path)


def finish(args):
    path = manifest_path(args.project_root, args.step_id, args.attempt)
    root = Path(args.project_root).resolve()
    row = json.loads(path.read_text(encoding="utf-8"))
    if row.get("step_id") != args.step_id or row.get("attempt") != args.attempt or row.get("state") != "in_progress":
        raise ValueError("manifest identity mismatch or attempt already finished")
    row.update({
        "ended_at": now(),
        "state": args.state,
        "change_inventory_path": reference(root, args.changes_path),
        "verification_refs": [reference(root, item) for item in args.verification_ref],
        "failure_class": args.failure_class,
    })
    if args.state == "passed" and args.failure_class != "none":
        raise ValueError("passed attempt cannot have a failure class")
    if args.state != "passed" and args.failure_class == "none":
        raise ValueError("non-passed attempt needs a failure class")
    fd, temporary = tempfile.mkstemp(prefix=".execution-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(row, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("start", "finish"):
        p = sub.add_parser(command)
        p.add_argument("--project-root", required=True)
        p.add_argument("--step-id", required=True)
        p.add_argument("--attempt", required=True, type=int)
    p = sub.choices["start"]
    p.add_argument("--project-id", required=True)
    p.add_argument("--task-id", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--runtime", required=True)
    p.add_argument("--model-id")
    p.add_argument("--reasoning-effort")
    p.add_argument("--role-profile", choices=["native", "instruction-fallback", "coordinator"], required=True)
    p.add_argument("--snapshot-path", required=True)
    p.add_argument("--handback-path", required=True)
    p.add_argument("--retry-of-attempt", type=int)
    p.add_argument("--approval-ref")
    p = sub.choices["finish"]
    p.add_argument("--state", choices=sorted(FINAL_STATES), required=True)
    p.add_argument("--changes-path")
    p.add_argument("--verification-ref", action="append", default=[])
    p.add_argument("--failure-class", choices=sorted(FAILURE_CLASSES), required=True)
    args = parser.parse_args(argv)
    try:
        (start if args.command == "start" else finish)(args)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.exit(2, f"EXECUTION MANIFEST ERROR: {exc}\n")


if __name__ == "__main__":
    main()
