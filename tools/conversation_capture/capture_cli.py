#!/usr/bin/env python3
"""Operator interface for reviewed, direct-mounted Factory transcript capture."""

import argparse
import json
import os
import subprocess
import sys

from pathlib import Path

from safe_export import ArchiveTarget, CaptureError, export, prepare, write_mounted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for action in ("summary", "review", "write"):
        command = sub.add_parser(action)
        command.add_argument("source", help="native Codex JSONL path")
        command.add_argument("--records", type=int, help="fixed, complete JSONL prefix to review and export")
        command.add_argument("--start-record", type=int, default=1,
                             help="first record of a nonoverlapping export range; requires --records")
        if action == "write":
            command.add_argument("--config", required=True, help="private local target JSON")
            command.add_argument("--name", required=True)
            command.add_argument("--reviewed-source-sha256", required=True)
            command.add_argument("--reviewed-output-sha256", required=True)
            command.add_argument("--folder-metadata-json", required=True,
                                 help="fresh connector metadata plus checked_at_epoch and account_email")
    args = parser.parse_args()
    try:
        if args.action in ("summary", "review"):
            payload, receipt = prepare(args.source, record_limit=args.records,
                                       start_record=args.start_record)
            if args.action == "review":
                # Pager receives bytes through a pipe. No transcript file or
                # pager search history is created by this command.
                env = dict(os.environ, LESSHISTFILE="/dev/null")
                with subprocess.Popen(["less", "-R"], stdin=subprocess.PIPE, env=env) as pager:
                    pager.communicate(payload)
                    if pager.returncode:
                        raise CaptureError("review pager did not finish normally")
            print(json.dumps(receipt, sort_keys=True))
        else:
            config = json.loads(Path(args.config).read_text())
            target = ArchiveTarget(config["folder_id"], config["owner_email"], Path(config["mount"]))
            metadata = json.loads(args.folder_metadata_json)
            review = {"reviewer": target.owner_email, "decision": "APPROVED",
                      "source_sha256": args.reviewed_source_sha256,
                      "output_sha256": args.reviewed_output_sha256}
            result = export(args.source, target, review, lambda: metadata,
                            lambda folder, payload: write_mounted(folder, payload, args.name, target),
                            record_limit=args.records, start_record=args.start_record)
            print(json.dumps(result, sort_keys=True))
    except (CaptureError, OSError, json.JSONDecodeError) as exc:
        print("CAPTURE_NOT_WRITTEN: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
