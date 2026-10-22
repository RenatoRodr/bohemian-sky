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
   custom launcher or alternate connector routes. The current Codex sandbox
   probe separately confirmed child execution and outside-write denial, but
   external reads were allowed. The documented read-deny profile remains
   untested.
5. **Staged migration and rollback — DOCUMENTED, NOT EXECUTED.** Scripts remain
   inert instructions. No backup, install, activation, or live config change.
6. **Review package — PR #18 MERGED; FOLLOW-UP LOCAL.** GitHub reports PR #18,
   “Document Codex workspace and external action boundaries,” merged into
   `main`. Its remote diff is identical to the current `HEAD` patch. Refresh
   stale `origin/main` before the next branch/PR step. Follow-up assessment and
   diagnostic files remain local and have not been pushed.
7. **Codex-native architecture assessment — RECORDED; PROFILE TEST PENDING.**
   The documented workspace-only profile denies reads outside configured roots.
   A normal-Terminal diagnostic is at
   `diagnostics/test_codex_workspace_profile.sh`. This task's nested sandbox attempt failed at host startup with
   `sandbox_apply: Operation not permitted`; no negative test was counted. The
   script uses the documented `codex sandbox --permission-profile` syntax and
   distinguishes host failure from target startup failure and intended denials.
   Only syntax is verified here; the macOS profile must be run in normal Terminal.
   See `CODEX-NATIVE-ASSESSMENT.html`.
8. **Connector approval — DOCUMENTED, NOT VERIFIED IN THIS RUNTIME.** Codex
   documentation exposes `apps._default` and per-app/per-tool `approval_mode`
   settings plus `approvals_reviewer = "user"`. The inspected local base
   `~/.codex/config.toml` has no approval or app settings; this task cannot see
   cloud-managed or desktop-effective overrides. The CLI help available in
   this task exposes no command for active desktop state; although the
   app-server protocol supports `config/read`, this task has no connection to
   the active app server. Its expected control socket is absent. A prior Gmail
   draft ran without a visible prompt. A public GitHub fetch succeeded, but
   separate mutation tools are exposed. Verify effective config and declined-
   call behavior before relying on this control. See
   `EXTERNAL-ACTION-LAYER.md`.
9. **External action mock — IMPLEMENTED, NOT ACTIVE.** The in-memory GitHub PR
   fixture and seven broker tests pass within the 17-test suite. Approval
   receipts are simulated. It has no credential, durable audit, real provider,
   or direct-route enforcement. Keep it as a fallback reference, not a broker.

## Gated actions

- **Follow-up GitHub PR:** not created. PR #18 merged the prior
  `SECURITY-AND-AUTHORITY.md` change. Current assessment and diagnostic edits
  are local and require review before any shared-remote write.
- **Live approval configuration:** not changed. A disposable per-tool approval
  test may be planned, but do not write live settings, hooks, or credentials
  under this assessment.

## Acceptance state

- Previous prototype and PR #18 review: **merged**. Follow-up assessment and
  diagnostic are written locally and remain unreviewed.
- Installed hooks, live configuration, credentials unchanged: **met by scope**;
  no write was made to them.
- Regression suite: **met for the policy and mock references in the recorded prior run**; 17 tests passed with
  `python3 -m unittest discover -s security/tests -v`.
- Codex native workspace boundary: **partly verified**. Outside writes were
  denied, but outside reads were allowed by the active profile. Run the
  supplied Terminal test for the documented read-deny profile.
- Connector approval: **not verified**. Active app-server settings are
  unavailable here, and no decline/no-provider-effect test ran.
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
