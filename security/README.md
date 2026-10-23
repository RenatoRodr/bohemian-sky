# Security v3 runtime prototype

This branch continues the Security v3 proposal merged in PR #15. The code is a
fail-closed policy reference, not a practical macOS security runtime: it does
not spawn commands, establish trusted identities, enforce OS sandboxing, broker
Google Drive or other connectors, or provide protected audit/recovery storage.
No production security guarantee is claimed.

## Implemented here

- Policy decisions for authorized local workspace reads/writes and explicit
  cross-project grants, with resolved-path and symlink escape checks.
- Narrow child capability derivation and separate external-effect categories
  for email, GitHub writes, publishing, deployments, Git pushes and paid APIs.
- Protected governance-name checks and fail-closed handling for secret and
  identity/escalation operations.
- Deny-only hook classification and a launcher boundary that refuses to spawn
  unless required host services are asserted (the assertions themselves are
  not trustworthy in this Python prototype).
- Inert migration and rollback checklists; neither edits configuration.

Google Drive access uses its separate connector and account permissions. The
local command sandbox does not scope that connector to the active project
folder. This checkout does not prove folder-level Drive isolation. Installed
hooks and live configuration remain untouched.

The connector approval assessment and offline broker mock are documented in
[`EXTERNAL-ACTION-LAYER.md`](EXTERNAL-ACTION-LAYER.md). Codex documents per-app
and per-tool approval settings, but they have not been verified in this task's
connector runtime. The mock uses an in-memory provider and simulated approval
receipts. Keep consequential service actions manual until a user-routed prompt
and a declined call with no provider effect are verified.

To inspect resolved approval settings and connector/tool metadata from normal
macOS Terminal, run
`python3 security/diagnostics/inspect_codex_approvals.py`. It does not invoke
connector tools or write configuration. It uses a standalone App Server and
cannot establish the desktop's current in-memory thread state. Earlier Terminal
attempts exposed a client-side stream handling bug and a timeout during optional
directory enumeration. The latest run completed: the standalone snapshot
reported `approval_policy: null`, `approvals_reviewer: null`, and
`managed_requirements: null`; several apps were enabled and callable. Its
enabled non-read-only tool inventory includes broad Drive, GitHub, calendar,
and Notion mutations, plus plugin-permission/uninstall controls. This does not
reveal effective approval behavior or prove a human prompt/decline path. No
connector operation was invoked. The diagnostic skips slow directory
enumeration and treats tool metadata as best-effort.

See [`CODEX-NATIVE-ASSESSMENT.html`](CODEX-NATIVE-ASSESSMENT.html) for the
capability matrix, probe evidence, recommendation, and remaining checks. The
disposable macOS profile diagnostic is now shell-only:
[`diagnostics/test_codex_workspace_profile.sh`](diagnostics/test_codex_workspace_profile.sh).
Its first Python-based Terminal run stopped before the target marker because
the selected Command Line Tools path lacks `usr/bin/xcrun`; see the portable
handoff at [`diagnostics/XCRUN-ISSUE.md`](diagnostics/XCRUN-ISSUE.md). The
shell-only profile passed workspace/child execution and temp plus
`~/Library/Caches` denial. The matched TCP check connected outside Codex and
returned `Operation not permitted` inside its sandbox. This strongly correlates
the block with the Codex sandbox. Neither Codex’s denial capture nor Apple’s
filtered unified log found a matching event, so it is not an audited denial.
The diagnostic now labels explicit `sandbox_apply` and broken-`xcrun` startup
errors as host failures. A generic permission error before the target marker is
reported as an unattributed startup permission error, never as a denial pass.

Run the local policy regression suite with
`python3 -m unittest discover -s security/tests -v`. These tests validate the
reference model only; they do not prove enforcement against subprocesses,
alternate tools, macOS escape paths, connector APIs, or a hostile process.
