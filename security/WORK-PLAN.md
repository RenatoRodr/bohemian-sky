# Factory Simplification and Security v3 — work plan

Status: PR #15 and PR #18 are merged. GitHub confirms PR #18 merged on 15
October 2026; it covered the earlier `SECURITY-AND-AUTHORITY.md` change only.
On 23 October 2026, `origin/main` was refreshed to `2c00d1b` (after PR #19),
and the follow-up commit series was rebased onto it. The current branch is
`codex/security-architecture-simplification-20261015`. The Codex-native
assessment is recorded in `CODEX-NATIVE-ASSESSMENT.html`. The mock broker
remains a fixture. Custom Seatbelt development is paused. No live configuration
or hooks were changed. A single Drive folder was created as a user-authorized,
disposable connector probe; no production connector mutation was attempted.
The existing Open Loop record was updated. The follow-up is in
GitHub PR #20 (`Assess Codex-native security architecture`), based on
`2c00d1b`; the latest remote check reports it open and draft, with no submitted
reviews or commit statuses. Mergeability is currently unknown.
Keep consequential connector writes manual until a
user prompt and denial behavior are verified.
The latest normal-Terminal run is the current shell-only diagnostic. It passed
the workspace read/write and child execution checks, denied the tested temp and
external-home reads/writes (including child writes), and confirmed a network
profile differential. No matching audit event was captured for the network
denial, so network enforcement is correlated but not audited. Connector
approval behavior remains unverified.
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
6. **Review package — PR #18 MERGED; FOLLOW-UP IN PR #20, REVIEW PENDING.**
   Commit `4dc747d` records the follow-up assessment and diagnostics.
   GitHub reports PR #18, “Document Codex workspace and external action
   boundaries,” merged into
   `main`; the merged local commit `7887c80` contains the authority document
   change, whose file patch matches the merged PR diff. The follow-up commits
   begin with `f606595`; they are not part of PR #18. `origin/main` is refreshed
   to `2c00d1b` after PR #19 and the
   follow-up branch is rebased onto it. The user approved the push and the
   follow-up was pushed as PR #20. That PR remains a draft with no reviews; it
   has not been merged.
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
8. **Connector approval — CONFIG INSPECTED; BEHAVIOR UNVERIFIED.** Current
   Codex documentation distinguishes command `approval_policy` from app/MCP
   tool approval. App tools have app-wide and per-tool modes (`auto`, `prompt`,
   `writes`, `approve`) and a reviewer setting; the approval/security guide
   says side-effecting app calls can prompt and destructive calls require
   approval when metadata marks them destructive (unless marked read-only).
   The inspected local base
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
   `managed_requirements: null`; it returned no `apps` table. Null command
   approval fields do not establish the app-tool approval mode. The
   installed-app snapshot marks multiple connectors
   enabled and callable, including Google Drive, GitHub, Gmail, Outlook Email,
   Notion, Google Calendar, Outlook Calendar, and Sites. The filtered
   `enabled_write_tools` output additionally lists Drive create/update/delete/
   share/upload and batch-update operations; GitHub issue/PR/repository writes
   including PR creation and merge; calendar event create/update/delete/respond;
   and numerous Notion create/update/delete/move/comment operations. It also
   lists administrative or consequential tools for plugin permissions and
   uninstall, document commands, and pet management. These are tool names
   marked enabled and `isReadOnly: false` by metadata; at the time of that
   configuration inspection no tool had been called. These results establish
   availability in a standalone App Server snapshot, not whether a
   call prompts, is automatically reviewed, or can be declined without provider
   effect. The snapshot is not the desktop's current in-memory thread state; no
   decline test was performed. Optional Codex OpenTelemetry
   can export tool-decision and tool-result events, but it is off by default
   and is not a demonstrated complete or tamper-resistant audit of provider
   effects. The inspector invokes no
   connector tools. A prior Gmail draft ran without a visible prompt, and a
   public GitHub fetch succeeded, but neither establishes policy for other
   tools. Treat the exposed write surface as broad until narrowed. At the
   latest check the Mac was unlocked, but the app-control tool refused access
   to ChatGPT/Codex for safety reasons; the live approval surface remains
   uninspected. The separate connector snapshot is not proof of the desktop's
   current approval mode. On 23 October, after the user explicitly authorized
   a disposable Drive-folder probe, `google_drive_create_folder` returned
   success and the private folder was verified by a metadata search: `Codex
   Security Approval Probe 2026-10-23`. This proves the connected route can perform the
   authorized write. Because the action was pre-authorized in the conversation,
   it does not test whether Codex would prompt for an unapproved write, and it
   does not test decline/no-provider-effect behavior. The folder remains as a
   clearly named fixture; no deletion was authorized. Keep consequential
   writes manual until a genuine prompt and a declined call with no provider
   effect are observed through a supported UI route. See
   `EXTERNAL-ACTION-LAYER.md`.
9. **External action mock — IMPLEMENTED, NOT ACTIVE.** The in-memory GitHub PR
   fixture and seven broker tests pass within the 21-test suite. Approval
   receipts are simulated. It has no credential, durable audit, real provider,
   or direct-route enforcement. Keep it as a fallback reference, not a broker.

## Gated actions

- **Follow-up GitHub PR:** PR #20 is open as a draft, based on `main` at
  `2c00d1b`; its latest remote check found no submitted reviews or commit
  statuses. Mergeability is currently unknown. PR #18
  merged the prior `SECURITY-AND-AUTHORITY.md` change. Current assessment and
  diagnostic edits are already in PR #20.
- **Live approval configuration:** not changed. An isolated per-tool approval
  test may be planned, but do not write live settings, hooks, or credentials
  under this assessment.

## Acceptance state

- Previous prototype and PR #18 review: **merged**. Follow-up assessment and
  diagnostic are pushed in PR #20, which is **open as a draft, not yet reviewed,
  and without reported commit statuses**. Current mergeability is unknown. PR
  #18 did not review these later commits.
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
  audit event. The current diagnostic version has now been rerun in normal
  Terminal and reproduces these results. Other protocols, connectors, and
  every external path are not covered.
- Connector approval: standalone App Server configuration and tool inventory
  **inspected**; active desktop thread state and approval behavior remain
  **unverified**. One user-authorized Drive-folder write probe succeeded and
  its private folder was verified by search. As the call was explicitly
  authorized in the conversation, it does not demonstrate whether the platform
  would prompt for an unapproved write or whether decline prevents provider
  effects. No decline test ran. The latest app-control attempt explicitly denied access to
  ChatGPT/Codex for safety reasons, so the live approval surface could not be
  inspected. Reported command approval fields are
  null, the response has no app settings table, apps and broad write tools are
  enabled/callable, and
  no decline/no-provider-effect test ran. Current Codex docs describe app-tool
  modes separately from command approvals.
- Cross-project edits and logging: per-path scoping is documented; Git records
  versioned changes and commits. A complete activity log requires an external
  trusted component and is **not demonstrated**.
- Role identity and per-role write isolation: separate tasks can be scoped by
  configuration; subagents inherit parent permissions. A trusted role identity
  or elevation-resistant authorization was **not demonstrated**.
- Protected plans: per-path read-only rules are documented, but the proposed
  builder-specific arrangement has not been runtime-tested.
- Audit/recovery: optional Codex OpenTelemetry can export tool-decision and
  tool-result events, but is off by default and was not tested. A complete,
  tamper-resistant audit and provider recovery process require external
  components and are **not demonstrated**.
- Production security guarantee: **not claimed**.
