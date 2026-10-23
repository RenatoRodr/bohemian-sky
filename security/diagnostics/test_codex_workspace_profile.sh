#!/bin/bash
set -u

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=classify_sandbox_startup.sh
source "$script_dir/classify_sandbox_startup.sh"

# Disposable native Codex permission-profile probe. The target probe uses only
# /bin/sh and system utilities so a Python/xcrun startup dependency cannot be
# misreported as a sandbox denial. No live Codex configuration is edited.

fail() {
    printf 'RESULT: FAIL — %s\n' "$1" >&2
    exit 1
}

report_startup_failure() {
    label=$1
    rc=$2
    stderr_path=$3
    classification=$(classify_sandbox_startup "$stderr_path")
    if [ "$classification" = 'STARTUP_PERMISSION_ERROR' ]; then
        printf '%s: %s (exit %s; cause unverified, not counted as a policy-denial pass)\n' "$label" "$classification" "$rc" >&2
    else
        printf '%s: %s (exit %s)\n' "$label" "$classification" "$rc" >&2
    fi
    sed -e "s|$HOME|<HOME>|g" -e "s|$scratch|<SCRATCH>|g" "$stderr_path" >&2
}

command -v codex >/dev/null 2>&1 || fail 'codex CLI was not found in PATH'

scratch=$(mktemp -d "${TMPDIR:-/tmp}/codex-native-profile.XXXXXX") || fail 'could not create disposable scratch directory'
isolated_home="$scratch/codex-home"
workspace="$scratch/workspace"
outside="$scratch/outside"
cache_root="$HOME/Library/Caches"
home_outside="$cache_root/codex-native-profile-$(basename "$scratch")"
home_outside_created=0
stdout_file="$scratch/profile.stdout"
stderr_file="$scratch/profile.stderr"
apple_network_log="$scratch/apple-network-denials.log"
apple_log_error="$scratch/apple-log-query.stderr"
host_network_stderr="$scratch/host-network.stderr"

cleanup() {
    rm -rf "$scratch"
    if [ "$home_outside_created" -eq 1 ]; then
        rm -rf "$home_outside"
    fi
}
trap cleanup EXIT HUP INT TERM

mkdir -p "$isolated_home" "$workspace" "$outside" || fail 'could not create disposable fixtures'
[ -d "$cache_root" ] || fail 'the existing ~/Library/Caches directory is unavailable'
mkdir "$home_outside" || fail 'could not create unique external fixture (it may already exist)'
home_outside_created=1
printf 'outside sentinel\n' > "$outside/sentinel.txt" || fail 'could not create outside read fixture'
printf 'external sentinel\n' > "$home_outside/sentinel.txt" || fail 'could not create external-home read fixture'

cat > "$isolated_home/config.toml" <<'TOML'
default_permissions = "workspace-only"

[permissions.workspace-only]
extends = ":workspace"

[permissions.workspace-only.filesystem]
":root" = "deny"
":minimal" = "read"
":tmpdir" = "deny"
":slash_tmp" = "deny"

[permissions.workspace-only.filesystem.":workspace_roots"]
"." = "write"

[permissions.workspace-only.network]
enabled = false
TOML

printf '%s\n' '=== Codex workspace profile diagnostic (shell-only target) ==='
printf 'Codex CLI: %s\n' "$(command -v codex)"
printf 'Temporary config and fixtures: <SCRATCH>/{codex-home,workspace,outside}\n'
printf 'External-home fixture: <HOME>/Library/Caches/<unique disposable directory>\n'
printf '%s\n' 'Live ~/.codex configuration: unchanged'
printf '%s\n' 'Python and xcrun: not used by target probes'

# Matched unconfined control: this performs only a TCP connect attempt to the
# same public IP/port as the sandboxed probe and sends no application data.
if /usr/bin/nc -z -v -w 3 -4 1.1.1.1 443 >/dev/null 2>"$host_network_stderr"; then
    host_network_rc=0
    printf '%s\n' 'HOST_NETWORK_CONTROL: ALLOWED (same TCP connect succeeded outside Codex sandbox)'
elif /usr/bin/grep -Eiq 'Operation not permitted|Permission denied' "$host_network_stderr"; then
    host_network_rc=1
    printf '%s\n' 'HOST_NETWORK_CONTROL: PERMISSION_ERROR (outside-sandbox attempt was also denied)'
    sed -e "s|$HOME|<HOME>|g" -e "s|$scratch|<SCRATCH>|g" "$host_network_stderr"
else
    host_network_rc=2
    printf '%s\n' 'HOST_NETWORK_CONTROL: INDETERMINATE (outside-sandbox attempt did not establish a connection)'
    sed -e "s|$HOME|<HOME>|g" -e "s|$scratch|<SCRATCH>|g" "$host_network_stderr"
fi

# Establish that the sandbox can launch a minimal command before evaluating
# any policy behavior.
if CODEX_HOME="$isolated_home" codex sandbox \
    --permission-profile workspace-only --cd "$workspace" -- \
    /bin/sh -c 'printf "BASELINE_STARTED\\n"; exec /usr/bin/true' \
    >"$stdout_file" 2>"$stderr_file"; then
    if /usr/bin/grep -q '^BASELINE_STARTED$' "$stdout_file"; then
        printf '%s\n' 'BASELINE_TRUE: PASS (shell started, /usr/bin/true exit 0)'
    else
        report_startup_failure BASELINE_TRUE 0 "$stderr_file"
        fail 'baseline returned 0 without starting the marker shell'
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

profile_script=$(cat <<'SH'
set -u
work=$1
outside=$2
home_outside=$3
failed=0

printf 'PROFILE_STARTED\n'

if printf 'workspace probe\n' 2>"$work/work-write.stderr" >"$work/work-write.txt"; then
    if [ "$(/bin/cat "$work/work-write.txt" 2>/dev/null)" = 'workspace probe' ]; then
        printf 'WORKSPACE_READ_WRITE_OK\n'
    else
        printf 'WORKSPACE_READ_WRITE_FAILED (write succeeded; readback failed)\n'
        failed=1
    fi
else
    printf 'WORKSPACE_WRITE_FAILED\n'
    failed=1
fi

child_output=$(/bin/sh -c 'printf "CHILD_STARTED\\n"; printf "child probe\\n" >"$1"' child "$work/child-write.txt" 2>"$work/child.stderr")
child_rc=$?
if [ "$child_rc" -eq 0 ] && [ "$child_output" = 'CHILD_STARTED' ] && [ "$(/bin/cat "$work/child-write.txt" 2>/dev/null)" = 'child probe' ]; then
    printf 'CHILD_EXECUTION_OK\n'
else
    printf 'CHILD_EXECUTION_FAILED exit=%s marker=%s\n' "$child_rc" "$child_output"
    failed=1
fi

if /bin/sh -c 'printf "NETWORK_PROBE_SHELL_STARTED\\n" >"$1"; exec /usr/bin/nc -z -v -w 3 -4 1.1.1.1 443' sh "$work/network.started" >/dev/null 2>"$work/network.stderr"; then
    network_rc=0
else
    network_rc=$?
fi
if [ "$(/bin/cat "$work/network.started" 2>/dev/null)" != 'NETWORK_PROBE_SHELL_STARTED' ]; then
    printf 'COMMAND_NETWORK_STARTUP_FAILURE exit=%s\n' "$network_rc"
    failed=1
elif [ "$network_rc" -eq 0 ]; then
    printf 'COMMAND_NETWORK_ALLOWED\n'
    failed=1
elif /usr/bin/grep -Eiq '^nc:.*(Operation not permitted|Permission denied)' "$work/network.stderr"; then
    printf 'COMMAND_NETWORK_PERMISSION_ERROR\n'
    printf 'COMMAND_NETWORK_DETAIL: '
    /bin/cat "$work/network.stderr"
elif /usr/bin/grep -Eiq '^/bin/sh:.*(/usr/bin/nc|exec)' "$work/network.stderr"; then
    printf 'COMMAND_NETWORK_STARTUP_FAILURE exit=%s\n' "$network_rc"
    failed=1
else
    printf 'COMMAND_NETWORK_INDETERMINATE\n'
    /bin/cat "$work/network.stderr"
fi

if /bin/cat "$outside/sentinel.txt" >"$work/outside-read.out" 2>"$work/outside-read.stderr"; then
    printf 'OUTSIDE_READ_ALLOWED\n'
    failed=1
elif /usr/bin/grep -Eiq 'Operation not permitted|Permission denied|Read-only file system' "$work/outside-read.stderr"; then
    printf 'OUTSIDE_READ_DENIED\n'
else
    printf 'OUTSIDE_READ_INDETERMINATE\n'
    failed=1
fi

if /bin/cat "$home_outside/sentinel.txt" >"$work/home-outside-read.out" 2>"$work/home-outside-read.stderr"; then
    printf 'HOME_OUTSIDE_READ_ALLOWED\n'
    failed=1
elif /usr/bin/grep -Eiq 'Operation not permitted|Permission denied|Read-only file system' "$work/home-outside-read.stderr"; then
    printf 'HOME_OUTSIDE_READ_DENIED\n'
else
    printf 'HOME_OUTSIDE_READ_INDETERMINATE\n'
    failed=1
fi

if printf 'must not persist\n' 2>"$work/outside-write.stderr" >"$outside/write-probe.txt"; then
    printf 'OUTSIDE_WRITE_ALLOWED\n'
    failed=1
elif /usr/bin/grep -Eiq 'Operation not permitted|Permission denied|Read-only file system' "$work/outside-write.stderr"; then
    printf 'OUTSIDE_WRITE_DENIED\n'
else
    printf 'OUTSIDE_WRITE_INDETERMINATE\n'
    failed=1
fi

if printf 'must not persist\n' 2>"$work/home-outside-write.stderr" >"$home_outside/write-probe.txt"; then
    printf 'HOME_OUTSIDE_WRITE_ALLOWED\n'
    failed=1
elif /usr/bin/grep -Eiq 'Operation not permitted|Permission denied|Read-only file system' "$work/home-outside-write.stderr"; then
    printf 'HOME_OUTSIDE_WRITE_DENIED\n'
else
    printf 'HOME_OUTSIDE_WRITE_INDETERMINATE\n'
    failed=1
fi

child_out=$(/bin/sh -c 'printf "CHILD_OUTSIDE_STARTED\\n"; printf "must not persist\\n" 2>"$2" >"$1"' child "$outside/child-write-probe.txt" "$work/child-outside-write.stderr")
child_out_rc=$?
if [ "$child_out" != 'CHILD_OUTSIDE_STARTED' ]; then
    printf 'CHILD_OUTSIDE_STARTUP_FAILURE exit=%s marker=%s\n' "$child_out_rc" "$child_out"
    failed=1
elif [ "$child_out_rc" -eq 0 ]; then
    printf 'CHILD_OUTSIDE_WRITE_ALLOWED\n'
    failed=1
elif /usr/bin/grep -Eiq 'Operation not permitted|Permission denied|Read-only file system' "$work/child-outside-write.stderr"; then
    printf 'CHILD_OUTSIDE_WRITE_DENIED\n'
else
    printf 'CHILD_OUTSIDE_WRITE_INDETERMINATE\n'
    failed=1
fi

home_child_out=$(/bin/sh -c 'printf "CHILD_HOME_OUTSIDE_STARTED\\n"; printf "must not persist\\n" 2>"$2" >"$1"' child "$home_outside/child-write-probe.txt" "$work/child-home-outside-write.stderr")
home_child_out_rc=$?
if [ "$home_child_out" != 'CHILD_HOME_OUTSIDE_STARTED' ]; then
    printf 'CHILD_HOME_OUTSIDE_STARTUP_FAILURE exit=%s marker=%s\n' "$home_child_out_rc" "$home_child_out"
    failed=1
elif [ "$home_child_out_rc" -eq 0 ]; then
    printf 'CHILD_HOME_OUTSIDE_WRITE_ALLOWED\n'
    failed=1
elif /usr/bin/grep -Eiq 'Operation not permitted|Permission denied|Read-only file system' "$work/child-home-outside-write.stderr"; then
    printf 'CHILD_HOME_OUTSIDE_WRITE_DENIED\n'
else
    printf 'CHILD_HOME_OUTSIDE_WRITE_INDETERMINATE\n'
    failed=1
fi

exit "$failed"
SH
)

if CODEX_HOME="$isolated_home" codex sandbox \
    --permission-profile workspace-only --log-denials --cd "$workspace" -- \
    /bin/sh -c "$profile_script" profile "$workspace" "$outside" "$home_outside" \
    >"$stdout_file" 2>"$stderr_file"; then
    rc=0
else
    rc=$?
fi

cat "$stdout_file"
if ! /usr/bin/grep -q '^PROFILE_STARTED$' "$stdout_file"; then
    report_startup_failure PROFILE_SHELL "$rc" "$stderr_file"
    fail 'shell did not print PROFILE_STARTED; policy probes were not counted'
fi

# Query Apple's documented unified-log sandbox violation category independently
# of Codex's --log-denials capture. Restrict results to messages mentioning nc.
if /usr/bin/log show --last 2m --style compact \
    --predicate 'subsystem == "com.apple.sandbox.reporting" AND category == "violation" AND eventMessage CONTAINS[c] "nc"' \
    >"$apple_network_log" 2>"$apple_log_error"; then
    apple_log_rc=0
else
    apple_log_rc=$?
fi
if [ "$apple_log_rc" -eq 0 ]; then
    if /usr/bin/grep -Eiq '\(nc\).*network-outbound|network-outbound.*\(nc\)' "$apple_network_log"; then
        printf '%s\n' 'APPLE_SANDBOX_LOG: matching nc event found'
        /usr/bin/grep -Ei '\(nc\).*network-outbound|network-outbound.*\(nc\)' "$apple_network_log" \
            | sed -e "s|$HOME|<HOME>|g" -e "s|$scratch|<SCRATCH>|g"
    else
        printf '%s\n' 'APPLE_SANDBOX_LOG: query succeeded; no matching nc outbound denial found'
    fi
else
    printf '%s\n' 'APPLE_SANDBOX_LOG: UNAVAILABLE (query failed; network attribution will remain inconclusive)'
    sed -e "s|$HOME|<HOME>|g" -e "s|$scratch|<SCRATCH>|g" "$apple_log_error"
fi

if [ "$rc" -ne 0 ]; then
    if /usr/bin/grep -qx 'COMMAND_NETWORK_ALLOWED' "$stdout_file"; then
        printf '%s\n' 'COMMAND_NETWORK: ALLOWED (unexpected; profile network is disabled)' >&2
        fail 'command network access was allowed'
    fi
    if /usr/bin/grep -q '^COMMAND_NETWORK_STARTUP_FAILURE' "$stdout_file"; then
        printf '%s\n' 'COMMAND_NETWORK: STARTUP_FAILURE (not counted as denial)' >&2
        fail 'the network probe command did not start cleanly'
    fi
    printf 'PROFILE_SHELL: CHECK_FAILURE (probe shell started; exit %s; inspect emitted markers)\n' "$rc" >&2
    sed -e "s|$HOME|<HOME>|g" -e "s|$scratch|<SCRATCH>|g" "$stderr_file" >&2
    fail 'the probe shell started but one or more checks failed or were indeterminate'
fi

for marker in WORKSPACE_READ_WRITE_OK CHILD_EXECUTION_OK OUTSIDE_READ_DENIED OUTSIDE_WRITE_DENIED CHILD_OUTSIDE_WRITE_DENIED HOME_OUTSIDE_READ_DENIED HOME_OUTSIDE_WRITE_DENIED CHILD_HOME_OUTSIDE_WRITE_DENIED; do
    /usr/bin/grep -qx "$marker" "$stdout_file" || fail "required marker missing: $marker"
done

printf '%s\n' 'PROFILE_SHELL: PASS'
if [ -s "$stderr_file" ]; then
    sed -e "s|$HOME|<HOME>|g" -e "s|$scratch|<SCRATCH>|g" "$stderr_file"
else
    printf '%s\n' '=== Sandbox denials ==='
    printf '%s\n' 'None found.'
fi
if /usr/bin/grep -qx 'COMMAND_NETWORK_PERMISSION_ERROR' "$stdout_file" && \
    [ "$apple_log_rc" -eq 0 ] && \
    /usr/bin/grep -Eiq '\(nc\).*network-outbound|network-outbound.*\(nc\)' "$apple_network_log"; then
    printf '%s\n' 'COMMAND_NETWORK: DENIED (nc permission error plus matching Apple sandbox violation log)'
    printf '%s\n' 'RESULT: PASS — workspace and child operations work; temp/external-home access and command network are denied.'
elif /usr/bin/grep -qx 'COMMAND_NETWORK_PERMISSION_ERROR' "$stdout_file" && \
    [ "$host_network_rc" -eq 0 ]; then
    printf '%s\n' 'COMMAND_NETWORK: PROFILE_DIFFERENTIAL (unconfined control connected; sandboxed nc returned Operation not permitted; no matching audit event)'
    printf '%s\n' 'RESULT: PARTIAL — filesystem boundary passed; network denial correlates with the Codex sandbox, but no audit event was captured.'
    exit 2
elif /usr/bin/grep -qx 'COMMAND_NETWORK_PERMISSION_ERROR' "$stdout_file" && \
    [ "$host_network_rc" -eq 1 ]; then
    printf '%s\n' 'COMMAND_NETWORK: HOST_OR_SYSTEM_DENIAL (the same permission error occurred outside the Codex sandbox)'
    printf '%s\n' 'RESULT: PARTIAL — filesystem boundary passed; network denial cannot be attributed to the Codex profile.'
    exit 2
elif /usr/bin/grep -qx 'COMMAND_NETWORK_INDETERMINATE' "$stdout_file"; then
    printf '%s\n' 'COMMAND_NETWORK: INDETERMINATE (see nc output and sandbox log; not counted as denial)'
    printf '%s\n' 'RESULT: PARTIAL — filesystem and child boundaries passed; network enforcement remains unverified.'
    exit 2
elif /usr/bin/grep -qx 'COMMAND_NETWORK_PERMISSION_ERROR' "$stdout_file"; then
    printf '%s\n' 'COMMAND_NETWORK: INDETERMINATE (permission error lacked a matching sandbox log)'
    printf '%s\n' 'RESULT: PARTIAL — filesystem boundary passed; network denial was not attributed to the profile.'
    exit 2
else
    if /usr/bin/grep -qx 'COMMAND_NETWORK_ALLOWED' "$stdout_file"; then
        printf '%s\n' 'COMMAND_NETWORK: ALLOWED (unexpected; profile network is disabled)' >&2
        fail 'command network access was allowed'
    fi
    printf '%s\n' 'COMMAND_NETWORK: INDETERMINATE (no attributable denial evidence)'
    printf '%s\n' 'RESULT: PARTIAL — filesystem boundary passed; network enforcement remains unverified.'
    exit 2
fi
