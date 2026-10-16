#!/usr/bin/env python3
"""Local build evidence and contract checks. Does not run acceptance commands."""
import argparse
import hashlib
import json
import os
import re
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path

STATUSES = {"pending", "in_progress", "done", "failed", "blocked", "dropped"}
EMPTY = {"none", "-", "–", "—", ""}


def relative(root, value, subtree=False):
    value = value.removesuffix("/**") if subtree else value
    p = Path(value)
    if not value or p.is_absolute() or ".." in p.parts or any(c in value for c in "*?[]"):
        raise ValueError(f"invalid relative path: {value!r}")
    if value in {".", "./"}:
        raise ValueError("whole-project write scope is not a bounded step")
    target = (root / p).resolve()
    if not target.is_relative_to(root):
        raise ValueError(f"path escapes project: {value!r}")
    return p.as_posix()


def overlaps(a, b):
    # Only exact files and trailing /** subtrees are accepted.
    aa, bb = a.removesuffix("/**"), b.removesuffix("/**")
    return (aa == bb or (a.endswith("/**") and bb.startswith(aa + "/"))
            or (b.endswith("/**") and aa.startswith(bb + "/")))


def validate(path):
    path = Path(path).resolve()
    text = path.read_text()
    fm = re.match(r"\A---\n(.*?)\n---(?:\n|$)", text, re.S)
    if not fm:
        raise ValueError("missing frontmatter")
    values = {}
    for line in fm[1].splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        key, sep, val = line.partition(":")
        if not sep or key in values:
            raise ValueError("invalid or duplicate frontmatter field")
        values[key] = val.strip().strip('"').strip("'")
    if not values.get("goal") or not values.get("root"):
        raise ValueError("goal and absolute root are required")
    root = Path(values["root"])
    if not root.is_absolute() or root.resolve() != path.parent:
        raise ValueError("root must be the absolute directory containing PLAN.md")
    root = root.resolve()
    marks = list(re.finditer(r"^## (S\d+) [—–-] (.+)$", text, re.M))
    steps = {}
    for index, mark in enumerate(marks):
        sid = mark[1]
        if sid in steps:
            raise ValueError(f"duplicate step: {sid}")
        body = text[mark.end():marks[index+1].start() if index+1 < len(marks) else len(text)]
        body = re.split(r"^# ", body, maxsplit=1, flags=re.M)[0]
        fields, current = {}, None
        for line in body.splitlines():
            match = re.match(r"^- \*\*(\w+):\*\*\s*(.*)$", line)
            if match:
                key, val = match.groups()
                if key in fields:
                    raise ValueError(f"{sid}: duplicate {key}")
                fields[key] = val.strip("`")
                current = key
            elif current in {"write_scope", "read_manifest"} and re.match(r"^\s+- ", line):
                fields[current] += "\n" + re.sub(r"^\s+- ", "", line).strip().strip("`")
            elif current and line.startswith("    "):
                fields[current] += "\n" + line.strip()
            elif line.strip():
                current = None
        required = {"status", "depends_on", "write_scope", "read_manifest", "acceptance", "output", "gated", "milestone"}
        if required - fields.keys():
            raise ValueError(f"{sid}: missing {sorted(required-fields.keys())}")
        if fields["status"] not in STATUSES or fields["gated"] not in {"yes", "no"}:
            raise ValueError(f"{sid}: invalid status or gated flag")
        for name in ("acceptance", "output"):
            if fields[name].strip() in EMPTY | {"|"}:
                raise ValueError(f"{sid}: empty {name}")
        for name in ("write_scope", "read_manifest"):
            paths = [p for p in fields[name].splitlines() if p not in EMPTY]
            for p in paths:
                relative(root, p, subtree=(name == "write_scope"))
            fields[name] = paths
        if fields["gated"] == "no" and not fields["write_scope"]:
            raise ValueError(f"{sid}: ungated step needs a write scope")
        deps = fields["depends_on"]
        fields["depends_on"] = [] if deps in EMPTY else re.split(r"[,\s]+", deps)
        steps[sid] = fields
    if not steps:
        raise ValueError("no steps")
    ancestors = {}

    def visit(sid, trail=()):
        if sid in trail:
            raise ValueError(f"dependency cycle: {' -> '.join(trail + (sid,))}")
        if sid not in steps:
            raise ValueError(f"unknown dependency: {sid}")
        if sid not in ancestors:
            ancestors[sid] = set()
            for dep in steps[sid]["depends_on"]:
                ancestors[sid] |= {dep} | visit(dep, trail + (sid,))
        return ancestors[sid]
    for sid in steps:
        visit(sid)
    ids = list(steps)
    for i, a in enumerate(ids):
        for b in ids[i+1:]:
            if a in ancestors[b] or b in ancestors[a]:
                continue
            if any(overlaps(x, y) for x in steps[a]["write_scope"] for y in steps[b]["write_scope"]):
                raise ValueError(f"{a}/{b}: overlapping scopes need a dependency")
    ungated = [s for s in steps.values() if s["gated"] == "no"]
    if not any(s["milestone"] not in EMPTY for s in ungated):
        raise ValueError("an ungated milestone is required")
    if len(ungated) > 3 and not any(s["milestone"] not in EMPTY for s in ungated[:-1]):
        raise ValueError("an intermediate milestone is required")
    return steps


def inventory(root, exclude):
    found, total = {}, 0
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d != ".git")
        links = [d for d in dirs if (Path(directory)/d).is_symlink()]
        dirs[:] = [d for d in dirs if d not in links]
        for name in sorted(files + links):
            path = Path(directory)/name
            rel = path.relative_to(root).as_posix()
            if rel == exclude:
                continue
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                content = os.readlink(path).encode()
                kind = "symlink"
            elif stat.S_ISREG(info.st_mode):
                total += info.st_size
                if total > 512 * 1024 * 1024 or len(found) >= 20000:
                    raise ValueError("snapshot cap reached; split the workspace or choose a reviewed evidence strategy")
                content = path.read_bytes()
                kind = "file"
            else:
                raise ValueError(f"unsupported special file: {rel}")
            found[rel] = [kind, stat.S_IMODE(info.st_mode), hashlib.sha256(content).hexdigest()]
    return found


def evidence_path(root, supplied):
    path = Path(supplied).resolve()
    if not path.is_relative_to(root):
        raise ValueError("evidence must be inside the project")
    return path, path.relative_to(root).as_posix()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["validate", "snapshot", "changes", "lock", "unlock"])
    parser.add_argument("path")
    parser.add_argument("argument", nargs="?")
    args = parser.parse_args()
    if args.action == "validate":
        steps = validate(args.path)
        print(f"Valid plan: {len(steps)} steps. Acceptance and goal verification still required.")
        return
    root = Path(args.path).resolve(strict=True)
    if not args.argument:
        raise ValueError("second argument required")
    if args.action in {"lock", "unlock"}:
        lock = root / ".factory-build.lock"
        if args.action == "lock":
            with lock.open("x") as stream:
                json.dump({"owner": args.argument, "created": datetime.now(timezone.utc).isoformat()}, stream)
            print("Lock acquired")
        else:
            if json.loads(lock.read_text())["owner"] != args.argument:
                raise ValueError("lock belongs to another coordinator")
            lock.unlink()  # Ephemeral lock only; never a material artifact.
            print("Lock released")
        return
    path, exclude = evidence_path(root, args.argument)
    if args.action == "snapshot":
        if path.exists():
            raise ValueError("evidence already exists; use a new attempt path")
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {"root": str(root), "excluded": exclude, "files": inventory(root, exclude)}
        with path.open("x") as stream:
            json.dump(data, stream, indent=2, sort_keys=True)
        print(f"Snapshot: {len(data['files'])} paths; excludes .git metadata and {exclude}")
    else:
        data = json.loads(path.read_text())
        if data["root"] != str(root) or data["excluded"] != exclude:
            raise ValueError("snapshot root/path mismatch")
        before, after = data["files"], inventory(root, exclude)
        changes = [{"path": name, "change": "added" if name not in before else "deleted" if name not in after else "modified"}
                   for name in sorted(before.keys() | after.keys()) if before.get(name) != after.get(name)]
        print(json.dumps(changes, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"BUILD CHECK ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
