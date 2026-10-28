#!/usr/bin/env python3
"""Append minimal Factory build-role usage events and report aggregate KPIs."""
from __future__ import annotations

import argparse
import json
import statistics
import uuid
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import session_capture  # noqa: E402


ROOT = Path(__file__).resolve().parent / "usage"
EVENTS = ROOT / "events.jsonl"
ROLES = {"factory_architect", "factory_builder", "factory_gatekeeper", "factory_auditor"}
RUNTIMES = {"codex": "codex", "chatgpt": "codex", "claude": "claude", "claude-code": "claude"}
BACKFILL_WINDOW = timedelta(hours=3)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_events() -> list[dict]:
    if not EVENTS.exists():
        return []
    return [json.loads(line) for line in EVENTS.read_text(encoding="utf-8").splitlines() if line.strip()]


def append(event: dict) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, sort_keys=True) + "\n")


def start(args: argparse.Namespace) -> None:
    if args.role not in ROLES:
        raise SystemExit(f"unsupported role: {args.role}")
    if args.runtime not in RUNTIMES:
        raise SystemExit(f"unsupported runtime: {args.runtime}")
    if (args.model or "").strip().lower() in {"unknown", "none", "n/a"}:
        raise SystemExit("--model must be a real model id; omit it and finish will read the model from the session log")
    if any(e.get("run_id") == args.run_id and e.get("event_type") == "started" for e in read_events()):
        raise SystemExit("run_id already exists")
    append({
        "schema_version": 1, "event_id": "ru-" + uuid.uuid4().hex[:12],
        "event_type": "started", "timestamp": now(), "run_id": args.run_id,
        "task_id": args.task_id, "step_id": args.step_id, "role": args.role,
        "runtime": args.runtime, "model": args.model, "attempt": args.attempt,
        "session_id": args.session_id,
    })


def finish(args: argparse.Namespace) -> None:
    events = read_events()
    opened = next((e for e in events if e.get("run_id") == args.run_id and e.get("event_type") == "started"), None)
    if opened is None:
        raise SystemExit("no matching started event")
    if any(e.get("run_id") == args.run_id and e.get("event_type") == "finished" for e in events):
        raise SystemExit("run already has a finished event")
    ended = datetime.now(timezone.utc)
    began = datetime.fromisoformat(opened["timestamp"])
    seen = session_capture.resolve(RUNTIMES.get(opened.get("runtime"), ""), began, ended, opened.get("session_id"))
    declared = opened.get("model")
    model = seen["model"] or declared
    event = {
        "schema_version": 1, "event_id": "ru-" + uuid.uuid4().hex[:12],
        "event_type": "finished", "timestamp": ended.isoformat(), "run_id": args.run_id,
        "result": args.result, "verified": args.verified,
        "duration_seconds": max(0, int((ended - began).total_seconds())),
        "input_tokens": args.input_tokens if args.input_tokens is not None else seen["input_tokens"],
        "output_tokens": args.output_tokens if args.output_tokens is not None else seen["output_tokens"],
        "cost_usd": args.cost_usd,
        "model_observed": seen["model"], "model_source": seen["source"] if seen["model"] else ("declared" if declared else "unresolved"),
        "effort_observed": seen["effort"], "session_ids": seen["session_ids"],
        "model_mismatch": bool(declared and seen["model"] and declared != seen["model"]),
    }
    if seen.get("candidate_models"):
        event["candidate_models"] = seen["candidate_models"]
    append(event)
    if not model:
        print("WARNING: model could not be determined for this run; pass --session-id at start or run `usage.py backfill`", file=sys.stderr)
        raise SystemExit(3)
    if event["model_mismatch"]:
        print(f"WARNING: declared model {declared} differs from observed {seen['model']}; observed value is used", file=sys.stderr)


def backfill(args: argparse.Namespace) -> None:
    """Append model_resolved events for runs whose model is still unknown. Append-only: history is never rewritten."""
    events = read_events()
    starts = {e["run_id"]: e for e in events if e.get("event_type") == "started"}
    finishes = {e["run_id"]: e for e in events if e.get("event_type") == "finished"}
    done = {e["run_id"] for e in events if e.get("event_type") == "model_resolved"}
    fixed = unresolved = 0
    for rid, opened in starts.items():
        if rid in done or effective(opened, finishes.get(rid), None) not in (None, "unknown"):
            continue
        began = datetime.fromisoformat(opened["timestamp"])
        end = min(datetime.fromisoformat(finishes[rid]["timestamp"]) if rid in finishes else began + BACKFILL_WINDOW, began + BACKFILL_WINDOW)
        seen = session_capture.resolve(RUNTIMES.get(opened.get("runtime"), ""), began, end, opened.get("session_id"))
        if not seen["model"]:
            unresolved += 1
            continue
        fixed += 1
        if not args.dry_run:
            append({"schema_version": 1, "event_id": "ru-" + uuid.uuid4().hex[:12], "event_type": "model_resolved",
                    "timestamp": now(), "run_id": rid, "model_observed": seen["model"], "effort_observed": seen["effort"],
                    "model_source": "inferred_" + seen["source"], "session_ids": seen["session_ids"]})
    print(f"{'would resolve' if args.dry_run else 'resolved'}: {fixed} | still unresolved or ambiguous: {unresolved}")


def effective(opened: dict, closed: dict | None, resolved: dict | None) -> str | None:
    """Best-known model: observed at finish, then inferred by backfill, then declared at start."""
    for event, key in ((closed, "model_observed"), (resolved, "model_observed"), (opened, "model")):
        if event and event.get(key) and event[key] != "unknown":
            return event[key]
    return None


def report(_: argparse.Namespace) -> None:
    events = read_events()
    starts = {e["run_id"]: e for e in events if e.get("event_type") == "started"}
    finishes = {e["run_id"]: e for e in events if e.get("event_type") == "finished"}
    resolved = {e["run_id"]: e for e in events if e.get("event_type") == "model_resolved"}
    print(f"Dispatches: {len(starts)} | completed records: {len(finishes)} | missing outcomes: {len(starts) - len(finishes)}")
    by_model: dict[str, int] = {}
    for rid, opened in starts.items():
        name = effective(opened, finishes.get(rid), resolved.get(rid)) or "unresolved"
        by_model[name] = by_model.get(name, 0) + 1
    print("models: " + ", ".join(f"{m}={n}" for m, n in sorted(by_model.items(), key=lambda kv: -kv[1])))
    print(f"model mismatches (declared vs observed): {sum(bool(e.get('model_mismatch')) for e in finishes.values())}")
    for role in sorted(ROLES):
        ids = [rid for rid, event in starts.items() if event.get("role") == role]
        done = [finishes[rid] for rid in ids if rid in finishes]
        verified = [e for e in done if e.get("verified") in {"pass", "fail"}]
        pass_rate = f"{sum(e['verified'] == 'pass' for e in verified) / len(verified):.0%}" if verified else "n/a"
        durations = [e["duration_seconds"] for e in done if isinstance(e.get("duration_seconds"), int)]
        tokens = [e["input_tokens"] + e["output_tokens"] for e in done if isinstance(e.get("input_tokens"), int) and isinstance(e.get("output_tokens"), int)]
        costs = [e["cost_usd"] for e in done if isinstance(e.get("cost_usd"), (int, float))]
        med = lambda values: str(int(statistics.median(values))) if values else "n/a"
        cost = f"${sum(costs):.4f}" if costs else "n/a"
        print(f"{role}: runs={len(ids)}, verified_pass_rate={pass_rate}, median_seconds={med(durations)}, median_tokens={med(tokens)}, known_cost_total={cost}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(required=True)
    p = sub.add_parser("start"); p.add_argument("--run-id", required=True); p.add_argument("--task-id", required=True); p.add_argument("--step-id", required=True); p.add_argument("--role", required=True); p.add_argument("--runtime", required=True); p.add_argument("--model", help="optional declared model id; the observed model is read from the session log at finish"); p.add_argument("--session-id", help="Codex thread id or Claude agent/session id; makes model capture exact"); p.add_argument("--attempt", type=int, required=True); p.set_defaults(func=start)
    p = sub.add_parser("finish"); p.add_argument("--run-id", required=True); p.add_argument("--result", choices=["complete", "partial", "blocked", "failed"], required=True); p.add_argument("--verified", choices=["pass", "fail", "not_applicable", "unknown"], default="unknown"); p.add_argument("--input-tokens", type=int); p.add_argument("--output-tokens", type=int); p.add_argument("--cost-usd", type=float); p.set_defaults(func=finish)
    p = sub.add_parser("backfill"); p.add_argument("--dry-run", action="store_true"); p.set_defaults(func=backfill)
    p = sub.add_parser("report"); p.set_defaults(func=report)
    args = parser.parse_args(); args.func(args)


if __name__ == "__main__":
    main()
