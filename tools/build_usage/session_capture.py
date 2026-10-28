#!/usr/bin/env python3
"""Resolve model, effort and token use for a build run from the runtime's own session logs.

Codex (ChatGPT) keeps one JSONL rollout per thread under ~/.codex/sessions, older days
zstd-compressed. Claude Code keeps one JSONL per session, plus one per sub-agent under
<session>/subagents. Both record the model that actually answered, so a run's model is read
from them instead of being typed by the orchestrating agent. Only metadata is read: model,
reasoning effort, token counts, timestamps, working directory and session id. No prompt or
response text leaves these files.
"""
from __future__ import annotations

import functools
import json
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

CODEX_ROOT = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "sessions"
CLAUDE_ROOT = Path.home() / ".claude" / "projects"


@dataclass
class Session:
    runtime: str
    session_id: str
    path: Path
    first: datetime
    last: datetime
    models: set[str] = field(default_factory=set)
    efforts: set[str] = field(default_factory=set)
    input_tokens: int | None = None
    output_tokens: int | None = None


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _records(path: Path) -> Iterator[dict]:
    if path.suffix == ".zst":
        proc = subprocess.run(["zstd", "-dc", str(path)], capture_output=True, check=False)
        if proc.returncode != 0:
            return
        text = proc.stdout.decode("utf-8", "replace")
    else:
        text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        try:
            yield json.loads(line)
        except ValueError:
            continue


def _days(start: datetime, end: datetime) -> list[Path]:
    day, last, out = (start - timedelta(days=1)).date(), (end + timedelta(days=1)).date(), []
    while day <= last:
        out.append(Path(f"{day:%Y}") / f"{day:%m}" / f"{day:%d}")
        day += timedelta(days=1)
    return out


@functools.lru_cache(maxsize=None)
def read_codex(path: Path) -> Session | None:
    meta, stamps, models, efforts, tokens = None, [], set(), set(), None
    for rec in _records(path):
        payload = rec.get("payload") if isinstance(rec.get("payload"), dict) else {}
        if rec.get("timestamp"):
            try:
                stamps.append(parse_ts(rec["timestamp"]))
            except ValueError:
                pass
        kind = rec.get("type")
        if kind == "session_meta":
            meta = payload
        elif kind == "turn_context":
            if payload.get("model"):
                models.add(payload["model"])
            if payload.get("effort"):
                efforts.add(payload["effort"])
        elif kind == "event_msg" and payload.get("type") == "thread_settings_applied":
            settings = payload.get("thread_settings") or {}
            if settings.get("model"):
                models.add(settings["model"])
        elif kind == "event_msg" and payload.get("type") == "token_count":
            total = (payload.get("info") or {}).get("total_token_usage")
            if total:
                tokens = total
    if not meta or not stamps:
        return None
    session = Session("codex", meta.get("id", path.stem), path, min(stamps), max(stamps), models, efforts)
    session.cwd = meta.get("cwd", "")  # type: ignore[attr-defined]
    if tokens:
        session.input_tokens, session.output_tokens = tokens.get("input_tokens"), tokens.get("output_tokens")
    return session


@functools.lru_cache(maxsize=None)
def read_claude(path: Path) -> Session | None:
    stamps, models, inp, out, sid = [], set(), 0, 0, path.stem
    for rec in _records(path):
        if rec.get("timestamp"):
            try:
                stamps.append(parse_ts(rec["timestamp"]))
            except ValueError:
                pass
        msg = rec.get("message") if isinstance(rec.get("message"), dict) else {}
        if rec.get("type") == "assistant" and msg.get("model") and not str(msg["model"]).startswith("<"):
            models.add(msg["model"])
            usage = msg.get("usage") or {}
            inp += sum(usage.get(k) or 0 for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
            out += usage.get("output_tokens") or 0
        sid = rec.get("agentId") or rec.get("sessionId") or sid
    if not stamps:
        return None
    session = Session("claude", sid, path, min(stamps), max(stamps), models, set(), inp or None, out or None)
    session.cwd = ""  # type: ignore[attr-defined]
    return session


def _name_start(path: Path) -> datetime:
    """Session start parsed from rollout-YYYY-MM-DDTHH-MM-SS-<id>; local time, so allow a day of slack."""
    try:
        stamp = path.name.split("rollout-", 1)[1][:19]
        return datetime.strptime(stamp, "%Y-%m-%dT%H-%M-%S").replace(tzinfo=timezone.utc) - timedelta(days=1)
    except (IndexError, ValueError):
        return datetime.min.replace(tzinfo=timezone.utc)


def candidates(runtime: str, start: datetime, end: datetime, session_id: str | None = None,
               root: Path | None = None) -> list[Session]:
    """Sessions of `runtime` whose activity overlaps [start, end], or the one named by session_id."""
    found: list[Session] = []
    if runtime == "codex":
        base = root or CODEX_ROOT
        files = [base / day / name for day in _days(start, end) if (base / day).is_dir()
                 for name in sorted(os.listdir(base / day)) if ".jsonl" in name]
        read = read_codex
    elif runtime == "claude":
        base = root or CLAUDE_ROOT
        files = sorted(base.glob("*/*.jsonl")) + sorted(base.glob("*/*/subagents/*.jsonl"))
        read = read_claude
    else:
        return []
    for path in files:
        if session_id and session_id not in path.name:
            continue
        if runtime == "codex" and not session_id and _name_start(path) > end:
            continue
        if not session_id and runtime == "claude" and not (start - timedelta(days=1) <= datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) <= end + timedelta(days=1)):
            continue
        session = read(path)
        if session and (session_id or (session.first <= end and session.last >= start)):
            found.append(session)
    return found


def resolve(runtime: str, start: datetime, end: datetime, session_id: str | None = None,
            root: Path | None = None) -> dict:
    """Observed model facts for one run. `source` says how much to trust them:
    session_id (exact thread), unique_model (several sessions overlapped but agree), none (nothing usable),
    ambiguous (overlapping sessions disagree, so no model is claimed)."""
    sessions = candidates(runtime, start, end, session_id, root)
    models = {m for s in sessions for m in s.models}
    result = {"session_ids": sorted(s.session_id for s in sessions), "model": None, "effort": None,
              "input_tokens": None, "output_tokens": None, "source": "none"}
    if not models:
        return result
    if len(models) > 1:
        result["source"] = "ambiguous"
        result["candidate_models"] = sorted(models)
        return result
    result["model"] = next(iter(models))
    result["source"] = "session_id" if session_id and len(sessions) == 1 else "unique_model"
    efforts = {e for s in sessions for e in s.efforts}
    result["effort"] = next(iter(efforts)) if len(efforts) == 1 else None
    if len(sessions) == 1:
        result["input_tokens"], result["output_tokens"] = sessions[0].input_tokens, sessions[0].output_tokens
    return result
