# Factory Simplification and Security v3 — work plan

Status: PR #15 merged to `main` at `029f12b`; this checkout continues its
security prototype on `build/security-v3-runtime`. No live configuration was
changed. The next action is human review of the separate PR; do not install or
activate from this branch.

1. **Baseline and scope — DONE.** Confirmed merged PR #15 and its v2-preserving,
   inactive prototype. Existing hook registration and live configuration are
   outside this change.
2. **Factory proposal — DONE in PR #15.** One-agent default and coordinator,
   architect, builder, auditor boundaries are in the merged rules/proposals.
3. **Security v3 policy/runtime reference — PARTLY DONE.** Added scoped local
   path policy, explicit cross-project checks, child-capability narrowing,
   governance protection, distinct external-effect grants and a fail-closed
   launcher contract. Trusted identity issuance, macOS OS sandbox, actual
   Google Drive workspace enforcement, connector mediation, and protected
   audit/recovery service remain NOT IMPLEMENTED.
4. **Regression evidence — PARTLY DONE.** Tests cover authorized policy paths
   and denials for outside roots, symlink escapes, role impersonation, child
   escalation, governance writes, secret operations, external effects, Git
   push, and unsafe deletion. They do not execute/adversarially contain child
   processes or alternate tools: there is no enforcing runtime to test.
5. **Staged migration and rollback — DOCUMENTED, NOT EXECUTED.** Scripts remain
   inert instructions. No backup, install, activation, or live config change.
6. **Review package — WAITING_FOR_APPROVAL.** Commit `0b74f96` is pushed on
   `build/security-v3-runtime`. The pre-tool-use hook blocked `gh pr create`
   as an external send requiring explicit human approval. The branch is ready;
   PR creation is not complete. No install, merge, or activation occurred.

## Gated actions

- **Create GitHub PR:** blocked by the active pre-tool-use hook with
  `BLOCKED — external send`; it requires explicit human approval. The exact
  proposed action is to create a PR from `build/security-v3-runtime` into
  `main`, titled “Continue Security v3 runtime prototype,” for code review.

## Acceptance state

- Versioned, reviewable prototype and reconciled plan: **met**.
- Installed hooks, live configuration, credentials unchanged: **met by scope**;
  no write was made to them.
- Regression suite: **met for the policy reference**; 10 tests passed with
  `python3 -m unittest discover -s security/tests -v`.
- Child process/alternate tool enforcement: **not met; unsupported until a
  trusted launcher, OS sandbox and connector brokers exist**.
- Production security guarantee: **not claimed**.
