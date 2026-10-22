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

See [`CODEX-NATIVE-ASSESSMENT.html`](CODEX-NATIVE-ASSESSMENT.html) for the
capability matrix, probe evidence, recommendation, and remaining checks. The
disposable macOS profile diagnostic is
[`diagnostics/test_codex_workspace_profile.sh`](diagnostics/test_codex_workspace_profile.sh).

Run the local policy regression suite with
`python3 -m unittest discover -s security/tests -v`. These tests validate the
reference model only; they do not prove enforcement against subprocesses,
alternate tools, macOS escape paths, connector APIs, or a hostile process.
