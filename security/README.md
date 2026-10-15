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

Google Drive authorization is not implemented or granted by this checkout.
Only a host broker with an explicit selected workspace scope can provide it.
The installed hooks and live configuration remain untouched.

Run the local policy regression suite with
`python3 -m unittest discover -s security/tests -v`. These tests validate the
reference model only; they do not prove enforcement against subprocesses,
alternate tools, macOS escape paths, connector APIs, or a hostile process.
