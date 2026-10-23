#!/usr/bin/env python3
"""Read Codex app approval configuration and connector metadata via app-server.

This diagnostic never invokes connector tools and never writes configuration.
Running codex app-server may initialize its normal local runtime state database.
The script intentionally prints only approval-related settings and public app
and tool metadata; it does not print arbitrary configuration or credentials.
"""

from __future__ import annotations

import json
import queue
import shutil
import subprocess
import sys
import threading
from typing import Any, Optional


TIMEOUT_SECONDS = 25


class AppServer:
    def __init__(self, executable: str) -> None:
        self.process = subprocess.Popen(
            [executable, "app-server", "--listen", "stdio://"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.stdout_lines: queue.Queue = queue.Queue()
        self.stderr_lines: queue.Queue[str] = queue.Queue()
        threading.Thread(target=self._read_stdout, daemon=True).start()
        self.stderr_reader = threading.Thread(target=self._read_stderr, daemon=True)
        self.stderr_reader.start()

    def _read_stdout(self) -> None:
        assert self.process.stdout is not None
        for line in self.process.stdout:
            self.stdout_lines.put(line)
        self.stdout_lines.put(None)

    def _read_stderr(self) -> None:
        assert self.process.stderr is not None
        for line in self.process.stderr:
            self.stderr_lines.put(line.rstrip())

    def send(self, message: dict[str, Any]) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def wait_for(self, request_id: int) -> dict[str, Any]:
        while True:
            try:
                line = self.stdout_lines.get(timeout=TIMEOUT_SECONDS)
            except queue.Empty as exc:
                details = self.stderr_text()
                suffix = f" App Server stderr: {details}" if details else ""
                raise TimeoutError(f"Timed out waiting for app-server response {request_id}.{suffix}") from exc
            if line is None:
                try:
                    return_code: Optional[int] = self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    return_code = None
                self.stderr_reader.join(timeout=2)
                details = self.stderr_text()
                suffix = f" App Server stderr: {details}" if details else ""
                status = (
                    f"process exited with status {return_code}"
                    if return_code is not None
                    else "process remained running"
                )
                raise RuntimeError(
                    f"App Server closed stdout before response {request_id} ({status}).{suffix}"
                )
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            if message.get("id") == request_id:
                if "error" in message:
                    raise RuntimeError(f"App Server returned an error for request {request_id}: {message['error']}")
                return message.get("result", {})

    def stderr_text(self) -> str:
        lines: list[str] = []
        while True:
            try:
                lines.append(self.stderr_lines.get_nowait())
            except queue.Empty:
                break
        return "\n".join(lines)

    def close(self) -> None:
        if self.process.stdin and not self.process.stdin.closed:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()


def rpc(server: AppServer, request_id: int, method: str, params: dict[str, Any]) -> dict[str, Any]:
    server.send({"method": method, "id": request_id, "params": params})
    return server.wait_for(request_id)


def approval_settings(config: dict[str, Any]) -> dict[str, Any]:
    selected: dict[str, Any] = {}
    for key in ("approval_policy", "approvals_reviewer"):
        if key in config:
            selected[key] = config[key]

    apps = config.get("apps")
    if isinstance(apps, dict):
        selected_apps: dict[str, Any] = {}
        for app_id, app in apps.items():
            if not isinstance(app, dict):
                continue
            app_fields: dict[str, Any] = {
                key: app[key]
                for key in ("enabled", "approvals_reviewer", "default_tools_approval_mode")
                if key in app
            }
            tools = app.get("tools")
            if isinstance(tools, dict):
                app_fields["tools"] = {
                    tool_id: {
                        key: tool[key]
                        for key in ("enabled", "approval_mode")
                        if key in tool
                    }
                    for tool_id, tool in tools.items()
                    if isinstance(tool, dict)
                }
            if app_fields:
                selected_apps[app_id] = app_fields
        if selected_apps:
            selected["apps"] = selected_apps
    return selected


def main() -> int:
    executable = shutil.which("codex")
    if not executable:
        print("ERROR: codex executable was not found on PATH", file=sys.stderr)
        return 2

    server: Optional[AppServer] = None
    try:
        server = AppServer(executable)
        server.send({
            "method": "initialize",
            "id": 1,
            "params": {
                "clientInfo": {
                    "name": "security-v3-readonly-inspector",
                    "title": "Security v3 Read-only Inspector",
                    "version": "1.0",
                }
            },
        })
        server.wait_for(1)
        server.send({"method": "initialized", "params": {}})

        config_result = rpc(server, 2, "config/read", {"includeLayers": True})
        requirement_result = rpc(server, 3, "configRequirements/read", {})
        installed_result = rpc(server, 4, "app/installed", {"forceRefresh": False})
        installed_apps = installed_result.get("apps", [])
        app_ids = [app.get("id") for app in installed_apps if isinstance(app, dict) and app.get("id")]
        tool_metadata: list[dict[str, Any]] = []
        metadata_errors: list[str] = []
        for offset in range(0, len(app_ids), 100):
            try:
                read_result = rpc(server, 5 + offset // 100, "app/read", {
                    "appIds": app_ids[offset:offset + 100],
                    "includeTools": True,
                })
                tool_metadata.extend(read_result.get("apps", []))
            except Exception as exc:
                metadata_errors.append(str(exc))
                break

        requirements = requirement_result.get("requirements")
        if isinstance(requirements, dict):
            requirements = {
                key: requirements[key]
                for key in (
                    "allowedApprovalPolicies",
                    "allowedAppApprovalModes",
                    "allowedToolApprovalModes",
                    "apps",
                )
                if key in requirements
            }

        output = {
            "source": "standalone local Codex App Server; not the desktop's live in-memory thread state",
            "status": "complete" if not metadata_errors else "partial",
            "configuration": approval_settings(config_result.get("config", {})),
            "managed_requirements": requirements,
            "installed_runtime_apps": [
                {key: app.get(key) for key in ("id", "runtimeName", "enabled", "callable")}
                for app in installed_apps
                if isinstance(app, dict)
            ],
            "tool_summaries": [
                {
                    "app_id": app.get("id"),
                    "tools": [
                        {
                            key: tool.get(key)
                            for key in ("name", "title", "isEnabled", "disabledReason", "isReadOnly")
                        }
                        for tool in app.get("toolSummaries", [])
                        if isinstance(tool, dict)
                    ],
                }
                for app in tool_metadata
                if isinstance(app, dict)
            ],
            "tool_metadata_errors": metadata_errors,
            "limitations": [
                "No connector tool was invoked.",
                "A separate app-server process reports its resolved settings and runtime snapshot, not necessarily the desktop's current in-memory state.",
                "Available-app directory enumeration is intentionally omitted because it can wait on remote catalog loading; installed runtime apps are listed instead.",
                "A decline/no-provider-effect behavior test is not performed by this read-only inspection.",
            ],
        }
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"INSPECTION_FAILED: {exc}", file=sys.stderr)
        return 1
    finally:
        if server is not None:
            server.close()


if __name__ == "__main__":
    raise SystemExit(main())
