#!/bin/bash
set -u

# Disposable native Codex permission-profile probe.
# It writes only under a temporary directory and a uniquely named cache fixture,
# then removes both. It never edits the user's Codex configuration.

fail() {
    printf 'RESULT: FAIL — %s\n' "$1" >&2
    exit 1
}

report_startup_failure() {
    label=$1
    rc=$2
    stderr_path=$3
    if /usr/bin/grep -Eiq 'sandbox_apply|sandbox.*(apply|initializ|start).*failed|Operation not permitted|invalid active developer path|xcrun: error' "$stderr_path"; then
        printf '%s: HOST_FAILURE (exit %s)\n' "$label" "$rc" >&2
    else
        printf '%s: STARTUP_FAILURE (exit %s)\n' "$label" "$rc" >&2
    fi
    sed -e "s|$HOME|<HOME>|g" -e "s|$scratch|<SCRATCH>|g" "$stderr_path" >&2
}

command -v codex >/dev/null 2>&1 || fail 'codex CLI was not found in PATH'
command -v python3 >/dev/null 2>&1 || fail 'python3 was not found in PATH'

scratch=$(mktemp -d "${TMPDIR:-/tmp}/codex-native-profile.XXXXXX") || fail 'could not create disposable scratch directory'
cache_root="$HOME/Library/Caches"
cache_fixture="$cache_root/codex-native-profile-$(basename "$scratch")"
isolated_home="$scratch/codex-home"
workspace="$scratch/workspace"
stdout_file="$scratch/profile.stdout"
stderr_file="$scratch/profile.stderr"

cleanup() {
    rm -rf "$scratch" "$cache_fixture"
}
trap cleanup EXIT HUP INT TERM

[ -d "$cache_root" ] || fail 'the existing ~/Library/Caches directory is unavailable'
mkdir -p "$isolated_home" "$workspace" "$cache_fixture" || fail 'could not create disposable fixtures'
printf 'outside sentinel\n' > "$cache_fixture/sentinel.txt" || fail 'could not create the external read fixture'

cat > "$isolated_home/config.toml" <<'TOML'
default_permissions = "workspace-only"

[permissions.workspace-only]
extends = ":workspace"

[permissions.workspace-only.filesystem]
":root" = "deny"
":minimal" = "read"

[permissions.workspace-only.filesystem.":workspace_roots"]
"." = "write"

[permissions.workspace-only.network]
enabled = false
TOML

printf '%s\n' '=== Codex workspace profile diagnostic ==='
printf 'Codex CLI: %s\n' "$(command -v codex)"
printf 'Temporary config and workspace: <SCRATCH>\n'
printf '%s\n' 'Live ~/.codex configuration: unchanged'

# First establish that the sandbox helper can launch a simple command.
if CODEX_HOME="$isolated_home" codex sandbox \
    --permission-profile workspace-only --cd "$workspace" -- \
    /bin/sh -c 'printf "BASELINE_STARTED\\n"; exec /usr/bin/true' \
    >"$stdout_file" 2>"$stderr_file"; then
    if /usr/bin/grep -q '^BASELINE_STARTED$' "$stdout_file"; then
        printf '%s\n' 'BASELINE_TRUE: PASS (shell started, /usr/bin/true exit 0)'
    else
        report_startup_failure BASELINE_TRUE 0 "$stderr_file"
        fail 'sandboxed baseline command returned 0 without starting the marker shell'
    fi
else
    rc=$?
    if /usr/bin/grep -q '^BASELINE_STARTED$' "$stdout_file"; then
        printf 'BASELINE_TRUE: EXECUTION_FAILURE (exit %s)\n' "$rc" >&2
    else
        report_startup_failure BASELINE_TRUE "$rc" "$stderr_file"
    fi
    fail 'sandboxed /usr/bin/true did not exit 0'
fi

probe="$scratch/probe.py"
cat > "$probe" <<'PY'
import errno
import os
import socket
import subprocess
import sys
from pathlib import Path

outside_read = Path(sys.argv[1]) / "sentinel.txt"
outside_write = Path(sys.argv[1]) / "write-probe.txt"
failed = False

print("PROFILE_STARTED", flush=True)
workspace_file = Path("workspace-write.txt")
workspace_file.write_text("ok")
if workspace_file.read_text() != "ok":
    print("WORKSPACE_READ_WRITE_FAILED", flush=True)
    failed = True
else:
    print("WORKSPACE_READ_WRITE_OK", flush=True)

child = subprocess.run(["/bin/sh", "-c", "printf CHILD_EXECUTED"],
                       capture_output=True, text=True)
if child.returncode == 0 and child.stdout == "CHILD_EXECUTED":
    print("CHILD_EXECUTION_OK", flush=True)
else:
    print(f"CHILD_EXECUTION_FAILED exit={child.returncode} stderr={child.stderr[:240]!r}", flush=True)
    failed = True

try:
    network_socket = socket.create_connection(("1.1.1.1", 443), timeout=2)
except OSError as exc:
    if exc.errno in (errno.EPERM, errno.EACCES):
        print(f"COMMAND_NETWORK_DENIED errno={exc.errno}", flush=True)
    else:
        print(f"COMMAND_NETWORK_INDETERMINATE errno={exc.errno} error={str(exc)[:160]!r}", flush=True)
        failed = True
else:
    print("COMMAND_NETWORK_ALLOWED", flush=True)
    failed = True
    network_socket.close()

try:
    read_fd = os.open(outside_read, os.O_RDONLY)
except OSError as exc:
    if exc.errno in (errno.EPERM, errno.EACCES, errno.EROFS):
        print(f"OUTSIDE_READ_DENIED errno={exc.errno}", flush=True)
    else:
        print(f"OUTSIDE_READ_UNEXPECTED_ERROR errno={exc.errno}", flush=True)
        failed = True
else:
    os.close(read_fd)
    print("OUTSIDE_READ_ALLOWED", flush=True)
    failed = True

try:
    write_fd = os.open(outside_write, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
except OSError as exc:
    if exc.errno in (errno.EPERM, errno.EACCES, errno.EROFS):
        print(f"OUTSIDE_WRITE_DENIED errno={exc.errno}", flush=True)
    else:
        print(f"OUTSIDE_WRITE_UNEXPECTED_ERROR errno={exc.errno}", flush=True)
        failed = True
else:
    os.write(write_fd, b"must not persist")
    os.close(write_fd)
    print("OUTSIDE_WRITE_ALLOWED", flush=True)
    failed = True

child_probe = r'''import errno, os, sys
try:
    fd = os.open(sys.argv[1], os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
except OSError as exc:
    if exc.errno in (errno.EPERM, errno.EACCES, errno.EROFS):
        print(f"CHILD_OUTSIDE_WRITE_DENIED errno={exc.errno}")
    else:
        print(f"CHILD_OUTSIDE_WRITE_UNEXPECTED_ERROR errno={exc.errno}")
        sys.exit(3)
else:
    os.write(fd, b"must not persist")
    os.close(fd)
    print("CHILD_OUTSIDE_WRITE_ALLOWED")
    sys.exit(4)
'''
grandchild = subprocess.run([sys.executable, "-c", child_probe,
                             str(outside_write)], capture_output=True, text=True)
if grandchild.returncode == 0 and grandchild.stdout.startswith("CHILD_OUTSIDE_WRITE_DENIED"):
    print(grandchild.stdout.strip(), flush=True)
else:
    print(f"CHILD_OUTSIDE_WRITE_TEST_FAILED exit={grandchild.returncode} stdout={grandchild.stdout[:160]!r} stderr={grandchild.stderr[:240]!r}", flush=True)
    failed = True

sys.exit(1 if failed else 0)
PY

if CODEX_HOME="$isolated_home" codex sandbox \
    --permission-profile workspace-only --cd "$workspace" -- \
    /usr/bin/python3 "$probe" "$cache_fixture" \
    >"$stdout_file" 2>"$stderr_file"; then
    rc=0
else
    rc=$?
fi

cat "$stdout_file"
if ! /usr/bin/grep -q '^PROFILE_STARTED$' "$stdout_file"; then
    report_startup_failure PROFILE_PYTHON "$rc" "$stderr_file"
    fail 'Python did not print PROFILE_STARTED; denial tests were not counted'
fi

if [ "$rc" -ne 0 ]; then
    printf 'PROFILE_PYTHON: EXECUTION_FAILURE (exit %s)\n' "$rc" >&2
    sed -e "s|$HOME|<HOME>|g" -e "s|$scratch|<SCRATCH>|g" "$stderr_file" >&2
    fail 'the probe process started but did not complete successfully'
fi

for marker in WORKSPACE_READ_WRITE_OK CHILD_EXECUTION_OK COMMAND_NETWORK_DENIED OUTSIDE_READ_DENIED OUTSIDE_WRITE_DENIED CHILD_OUTSIDE_WRITE_DENIED; do
    /usr/bin/grep -Eq "^${marker}([[:space:]]|$)" "$stdout_file" || fail "required marker missing: $marker"
done

printf '%s\n' 'PROFILE_PYTHON: PASS'
printf '%s\n' 'RESULT: PASS — workspace writes and child execution work; command network and outside reads/writes are denied.'
