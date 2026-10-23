# Factory Simplification and Security v3 — work plan

Status: PR #15 and PR #18 are merged. GitHub confirms PR #18 merged on 15
October 2026; its patch matches the current `HEAD` change, while this
checkout's `origin/main` is stale. The current branch is
`codex/security-architecture-simplification-20261015`. The Codex-native
assessment is recorded in `CODEX-NATIVE-ASSESSMENT.html`. The mock broker
remains a fixture. Custom Seatbelt development is paused. No live configuration
or hooks were changed, and no connector mutation was attempted during this
assessment turn. The existing Open Loop record was updated. Keep consequential
connector writes manual until a user prompt and denial behavior are verified.
The latest normal-Terminal profile output predates the startup-classification
refactor in the current diagnostic. Shell syntax and classifier tests pass, but
the desktop safety boundary refused Codex access to Terminal, so the final
script version has not had an end-to-end macOS rerun. Run the documented command
in normal Terminal before treating the latest script as fully verified.
Do not activate Security v3.

1. **Baseline and scope — DONE.** Confirmed merged PR #15 and its v2-preserving,
   inactive prototype. Existing hook registration and live configuration are
   outside this change.
2. **Factory proposal — DONE in PR #15.** One-agent default and coordinator,
   architect, builder, auditor boundaries are in the merged rules/proposals.
3. **Security v3 policy/runtime reference — PARTLY DONE.** Added scoped local
   path policy, explicit cross-project checks, child-capability narrowing,
   governance protection, distinct external-effect grants and a fail-closed
   launcher contract. The custom runtime does not implement trusted identity,
   OS sandboxing, Drive folder enforcement, connector mediation, or protected
   audit/recovery. The Codex-native replacement assessment is separate.
4. **Regression evidence — PARTLY DONE.** Tests cover authorized policy paths
   and denials for outside roots, symlink escapes, role impersonation, child
   escalation, governance writes, secret operations, external effects, Git
   push, and unsafe deletion. They do not execute/adversarially contain the
   custom launcher or alternate connector routes. The prior `workspace-write`
   profile allowed reads outside the workspace; the separate workspace-only
   profile later passed tested outside-read/write denials and child execution
   in normal Terminal. That result covers only the paths exercised by the
   diagnostic, not arbitrary filesystem access or connector-mediated access.
5. **Staged migration and rollback — DOCUMENTED, NOT EXECUTED.** Scripts remain
   inert instructions. No backup, install, activation, or live config change.
6. **Review package — PR #18 MERGED; FOLLOW-UP COMMITTED LOCALLY, NOT PUSHED.**
   Commit `4891a92` records the current follow-up assessment and diagnostics.
   No follow-up PR exists. GitHub reports PR #18,
   “Document Codex workspace and external action boundaries,” merged into
   `main`. Its remote diff is identical to the current `HEAD` patch. Refresh
   stale `origin/main` before the next branch/PR step. Follow-up assessment and
   diagnostic files remain local and have not been pushed.
7. **Codex-native architecture assessment — FILESYSTEM PROFILE PASS; NETWORK PROFILE-DIFFERENTIAL OBSERVED; AUDIT EVENT MISSING.**
   The first normal-Terminal run passed the simple shell/`true` baseline, then
   failed before Python printed `PROFILE_STARTED`: the active developer path
   `/Library/Developer/CommandLineTools` lacks `usr/bin/xcrun`. No profile
   denial was tested. See `diagnostics/XCRUN-ISSUE.md` for the handoff summary.
   A shell-only run then started; workspace read/write and child execution
   passed, but the supposed outside fixtures in `$TMPDIR` were allowed because
   `:workspace` inherits writable `:tmpdir` and `:slash_tmp`. The profile was
   corrected to deny both; the user reran it and workspace read/write, child
   execution, and all three temp-path denials passed. A later run also denied
   outside reads/writes and child writes for a unique, automatically cleaned
   fixture under `~/Library/Caches`. The filesystem scope tested by this
   diagnostic now passes. The TCP egress probe returned `Operation not
   permitted`, but neither `--log-denials` nor the independent Apple unified
   sandbox-violation query found a matching outbound event. The latest matched
   test connected to `1.1.1.1:443` outside Codex, while sandboxed `nc` returned
   `Operation not permitted`. The runner reported
   `COMMAND_NETWORK: PROFILE_DIFFERENTIAL`. This strongly correlates the denial
   with the Codex sandbox, but neither log source captured an audit event, so
   do not call it an audited denial. Keep command networking disabled.
   Other network protocols and connector traffic are not covered. Do not run the restricted
   profile test inside Codex.
8. **Connector approval — CONFIG INSPECTED; BEHAVIOR UNVERIFIED.** Codex
   documentation exposes `apps._default` and per-app/per-tool `approval_mode`
   settings plus `approvals_reviewer = "user"`. The inspected local base
   `~/.codex/config.toml` has no approval or app settings. The documented
   app-server RPC can read resolved on-disk config, managed requirements, and
   app/tool metadata, but it does not claim to expose the desktop's current
   in-memory thread state. The user's first Terminal run showed that app-server
   initialization returned, but the inspector incorrectly treated each stdout
   line as end-of-stream and reported a false early-exit error before collecting
   the config response. The user's second run obtained responses through
   `app/installed` but timed out waiting for optional `app/list` catalog
   enumeration; accumulated results were discarded. The inspector now omits
   `app/list` and makes `app/read` best-effort while preserving configuration
   and installed-app results. A separate attempt
   from this Codex sandbox cannot initialize
   app-server SQLite state under `~/.codex`, so do not run this query here.
   The latest Terminal output reports `status: complete`,
   `approval_policy: null`, `approvals_reviewer: null`, and
   `managed_requirements: null`. The shown configuration contains no app-specific
   approval overrides. The installed-app snapshot marks multiple connectors
   enabled and callable, including Google Drive, GitHub, Gmail, Outlook Email,
   Notion, Google Calendar, Outlook Calendar, and Sites. The filtered
   `enabled_write_tools` output additionally lists Drive create/update/delete/
   share/upload and batch-update operations; GitHub issue/PR/repository writes
   including PR creation and merge; calendar event create/update/delete/respond;
   and numerous Notion create/update/delete/move/comment operations. It also
   lists administrative or consequential tools for plugin permissions and
   uninstall, document commands, and pet management. These are tool names
   marked enabled and `isReadOnly: false` by metadata; no tool was called. These results
   establish availability in a standalone App Server snapshot, not whether a
   call prompts, is automatically reviewed, or can be declined without provider
   effect. The snapshot is not the desktop's current in-memory thread state; no
   connector action or decline test was performed. The inspector invokes no
   connector tools. A prior Gmail draft ran without a visible prompt, and a
   public GitHub fetch succeeded, but neither establishes policy for other
   tools. Treat the exposed write surface as broad until narrowed. Keep consequential writes manual until a user-routed prompt and a
   declined call with no provider effect are verified. See
   `EXTERNAL-ACTION-LAYER.md`.
9. **External action mock — IMPLEMENTED, NOT ACTIVE.** The in-memory GitHub PR
   fixture and seven broker tests pass within the 21-test suite. Approval
   receipts are simulated. It has no credential, durable audit, real provider,
   or direct-route enforcement. Keep it as a fallback reference, not a broker.

## Gated actions

- **Follow-up GitHub PR:** not created. PR #18 merged the prior
  `SECURITY-AND-AUTHORITY.md` change. Current assessment and diagnostic edits
  are local and require review before any shared-remote write.
- **Live approval configuration:** not changed. An isolated per-tool approval
  test may be planned, but do not write live settings, hooks, or credentials
  under this assessment.

## Acceptance state

- Previous prototype and PR #18 review: **merged**. Follow-up assessment and
  diagnostic are committed locally on the current branch; no follow-up review
  or PR has occurred.
- Installed hooks, live configuration, credentials unchanged: **met by scope**;
  no write was made to them.
- Regression suite: **21/21 passed in this session** with
  `python3 -m unittest discover -s security/tests -v`. These tests cover the
  policy reference, mock broker, and startup-error classification; they do not
  verify OS enforcement or live connector approval. `bash -n` passed for both
  diagnostic shell scripts. The macOS sandbox diagnostic itself was not run
  inside Codex.
- Codex native workspace boundary: **verified for tested filesystem cases**.
  The prior active
  workspace-write probe denied outside writes but allowed outside reads. In the
  first shell-only read-deny-profile run, the target started and workspace
  read/write plus child execution passed; reads/writes to a sibling fixture in
  `$TMPDIR` were allowed because the derived profile had not overridden the
  inherited temp-directory grants. The corrected profile explicitly denies
  `:tmpdir` and `:slash_tmp`; the user reran it and the temp-path read/write
  probes were denied while workspace writes and child execution worked. The
  user reran the extended diagnostic: read/write and child-write probes against
  a disposable `~/Library/Caches` fixture were denied; workspace read/write and
  child execution passed. In the matched network probe, the same TCP connect
  succeeded outside Codex and returned `Operation not permitted` inside. This
  is a **profile-correlated differential**; both log sources lacked a matching
  audit event. The latest profile output predates the diagnostic's
  startup-classification refactor. Codex computer-use access to Terminal was
  refused, so rerun the final script version in normal Terminal. Other
  protocols, connectors, and every external path are not covered.
- Connector approval: standalone App Server configuration and tool inventory
  **inspected**; active desktop thread state and approval behavior remain
  **unverified**. Reported approval fields are null, apps and broad write tools
  are enabled/callable, and no decline/no-provider-effect test ran.
- Cross-project edits and logging: per-path scoping is documented; Git records
  versioned changes and commits. A complete activity log requires an external
  trusted component and is **not demonstrated**.
- Role identity and per-role write isolation: separate tasks can be scoped by
  configuration; subagents inherit parent permissions. A trusted role identity
  or elevation-resistant authorization was **not demonstrated**.
- Protected plans: per-path read-only rules are documented, but the proposed
  builder-specific arrangement has not been runtime-tested.
- Audit/recovery: a tamper-resistant full audit and provider recovery process
  require external components and are **not demonstrated**.
- Production security guarantee: **not claimed**.
