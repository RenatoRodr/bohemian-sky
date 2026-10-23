# `xcrun` startup failure — handoff summary

## Observed result

On 22 October 2026, the normal-Terminal diagnostic reported:

```text
BASELINE_TRUE: PASS (shell started, /usr/bin/true exit 0)
PROFILE_PYTHON: HOST_FAILURE (exit 1)
xcrun: error: invalid active developer path (/Library/Developer/CommandLineTools), missing xcrun at: /Library/Developer/CommandLineTools/usr/bin/xcrun
RESULT: FAIL — Python did not print PROFILE_STARTED; denial tests were not counted
```

The selected developer directory exists, but its expected `usr/bin/xcrun` is
missing. `/usr/bin/xcrun` exists and reports version 72; the current selection
still points to `/Library/Developer/CommandLineTools`. No Xcode app was found
in the inspected `/Applications` paths.

## What this establishes

- The sandbox command could start a shell and run `/usr/bin/true` in the
  baseline.
- The restricted-profile Python target did not reach its first output marker.
- Therefore no restricted-profile read/write or network denial result was
  produced. This is a host/toolchain startup failure, not evidence that the
  profile denied the target operation.
- The error identifies an invalid active Apple developer-tools path. It does
  **not** by itself establish why the Codex invocation needed `xcrun`, nor prove
  that Python dependencies or the Seatbelt policy caused the failure.

## Follow-up shell-only result

The target was changed to `/bin/sh` and run again in normal Terminal. It printed
`PROFILE_STARTED`; workspace read/write and child execution passed. The outside
read, outside write, and child outside-write probes were all **allowed**, so the
run failed its intended boundary check. Inspection found that those fixtures
were siblings under `$TMPDIR`, which the inherited `:workspace` profile makes
writable unless the derived profile explicitly denies `:tmpdir` and
`:slash_tmp`. This result does not show whether the corrected profile denies
other paths; it does show the prior probe was not checking an excluded path.

The disposable diagnostic added explicit `:tmpdir = "deny"` and
`:slash_tmp = "deny"` rules while retaining the workspace-root write grant.
The user reran it: workspace read/write and child execution passed, all three
temp-path denial probes passed, and read/write/child-write attempts against a
unique `~/Library/Caches` fixture were denied. Filesystem checks in the profile
passed for those tested paths. The network probe’s shell started and `nc`
reported `Operation not permitted`, but neither `--log-denials` nor Apple’s
filtered unified sandbox-violation query contained a matching outbound denial
for `nc`. The matched control then connected to the same IP and port outside
Codex, while the sandboxed attempt failed with `Operation not permitted`.
This strongly correlates the denial with the Codex sandbox, but it is not an
audited denial because neither log source captured a matching event.

## Follow-up result and next action

The extended shell-only profile has now been rerun. Workspace operations and
the tested outside-path denials passed. The same TCP connection succeeded
outside Codex and returned `Operation not permitted` inside the sandbox; both
Codex and Apple log queries lacked a matching event. Treat this as a
profile-correlated differential without an audit record. Do not repeat the
network probe unless the profile or host changes.

The remaining assessment gate is connector approval. Effective app-server
configuration is unavailable in this task because its control socket is
absent. Inspect the active per-app/per-tool approval settings in Codex, then
use an isolated connector test to display and decline a harmless action and
verify no provider-side result. Do not change live settings or use a
consequential provider action as the test.

For reference, rerun the filesystem profile from normal macOS Terminal only
after changing the profile or host:

```sh
cd "/Users/renato/Documents/Codex/2026-10-15/continue-existing-build-security-v3-sandbox/work/project-factory-security-simplification"
./security/diagnostics/test_codex_workspace_profile.sh
```

The target uses `/bin/sh`, does not invoke Python or call `xcrun`, and checks
shell startup, workspace read/write, child execution, temp-path denial,
external-home read/write denial, and a TCP egress attempt. For network, it
requires an `nc` permission error plus a matching outbound denial record for a
confirmed sandbox audit result. The latest run was profile-correlated by the
outside/inside comparison, but no audit event was captured. Codex may still depend on the
selected developer directory while starting the sandbox.

If the shell-only restricted probe reports the same `xcrun` host failure, stop
the sandbox test. A developer-tools repair or selection change is a separate
macOS administration decision; this project does not perform it. Do not count
startup failure as a negative-test pass.
