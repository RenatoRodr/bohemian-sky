---
name: factory-build
description: Run the project factory's architect, builder, gatekeeper, and auditor workflow for a requested multi-step build or an existing PLAN.md. Use after managed-project intake; ordinary small edits do not need a build crew.
---

# Factory build

The main Codex task coordinates the build and owns its durable state. Use the
conductor for project intake, resume, and close. The factory's AGENTS.md permits
Codex to write control files; older conductor text assigning that only to Claude
does not override it. Do not create a new project before intake approval.

This skill authorizes bounded subagent delegation for the requested build.
Use the four `factory_*` agents in the factory's `.codex/agents/`. In a runtime
without a custom-agent selector, read the corresponding TOML and give its
developer_instructions and a self-contained brief to a fresh subagent. Use
`fork_turns="none"` where available. Inherit the user's model; do not guess a
cheap substitute. State if a role's read-only sandbox cannot be selected.

## Start and ownership

1. Read the project's control files, binding decisions, and relevant instructions.
   The coordinator may inspect source to resolve a planning gap. Keep reads
   targeted. Confirm the requested project and check for another active owner.
2. Use `PLAN.md` as the detailed execution contract for the current control-plan
   step. `control/PROJECT.md` remains authoritative for project status. Register
   PLAN.md in RESOURCES.md and preserve replaced plans in archive/ with an ISO
   date. Do not use the Claude package's packer or scribe for this workflow.
3. Acquire the project lock using this skill's `scripts/build_check.py lock
   <project-root> <session-id>`. A pre-existing lock is a stop, not permission to
   steal it. Investigate an abandoned lock and obtain confirmation before release.
4. If there is no plan, ask the architect for one using
   [the contract](references/PLAN.md). The coordinator saves it, validates with
   `python3 <skill>/scripts/build_check.py validate <project-root>/PLAN.md`, and
   marks the control-plan step in_progress before implementation.

## Execute and verify

Use one builder at a time in the shared project directory. Independent read-only
research may run alongside it. Parallel builders require separate worktrees or
equivalent isolated directories and an explicit integration step, even when
their declared scopes differ. Never have two coordinators on the same project.

### Jev live advice for new Factory builds

At intake for a new project or a newly started task in an existing project,
follow the Jev opportunity check in `AGENTS.md`.
When a useful bounded judgment about task difficulty, risk, or role usefulness
could change the build plan, use the shared live adapter before choosing roles.
This is the ordinary new-work path under the standing authorization in
`MEMORY-CONTRACT.md`; do not replace it with shadow telemetry, a Gate A record,
or repeated per-project or per-call approval.

Use `projects/jev-decision-gateway/code/assess_new_work.py` and its shared
`decide()` contract. Read its `--help` before use. Supply only a minimized
task ID and summary in an authorized input category. Attest permitted input and
account preflight only after those checks are actually complete. Use
`--include-risk-role` when separate risk and useful-implementer advice can
affect the plan; the caller bundles those questions in one bounded request.

Make the assessment once for the task-level state. Reassess only when relevant
state changes and a new bounded judgment could change the decision; do not repeat
the same call for every build step. If no useful judgment is needed, an exact
rule decides, or nothing relevant changed, make no Jev call. If the permitted
input or live route is unavailable, continue deterministically and record the
specific gap.

Keep valid Jev advice and its confidence visible to the coordinator, including
low-confidence output. The coordinator selects the actual roles and review;
deterministic rules preserve mandatory reviews and all permissions. The
provisional pilot thresholds do not gate ordinary live new-work advice. Record
the advice, actual role choice and observed outcome in the project's existing
record when known, using privacy-safe summaries rather than raw prompts.

### Existing Jev shadow telemetry (Gate A pilots only)

This separate observer remains for historical or explicitly approved shadow
pilots. Its Gate A scope, expiry, budget, opt-in, telemetry contract and
outcome controls still apply to that observer. Do not invoke it merely to satisfy
the live new-work advice rule. It never changes role, model, permissions,
reviews, acceptance rules, or dispatch. Never send source, full prompts, diffs,
private details, or credentials.

After the coordinator has selected the normal role/runtime/model/effort, make at
most one observer call before dispatch:

```sh
python3 build-agents-v1/codex/jev_shadow.py classify \
  --record experiments/jev-shadow/events.jsonl --task-id TASK-ID --step-id S1 \
  --role builder --runtime codex --model SELECTED-MODEL --effort SELECTED-EFFORT \
  --attempts 1 --summary 'Short non-sensitive task description' \
  --non-sensitive --paid-call-opt-in
```

The local script reads the key from the macOS login Keychain service
`project-factory-jev`. Record the returned classification event ID. Whether Jev
returns a class, reports low confidence, fails, or cannot write telemetry, carry
on with the already planned dispatch unchanged. A missing attestation or paid
call opt-in means skip Jev and proceed normally. Never retry automatically.

After step completion, append a separate outcome event. Reuse the exact task,
step, role and record path; pass the event ID from classification when one was
recorded. For `available` or `uncertain`, the script requires the classification
event ID and predicted class, then checks the stored classification matches the
task, step, role, and prediction. `unavailable` may be unlinked. Optionally,
assign a human D0–D4 label before viewing Jev's prediction and pass it with
`--human-label-before-jev`; this label is written only in the outcome event.
Use only known runtime metadata. Outcome Score is categorical or null when
unrated; Pattern ID remains null unless its proposal is implemented. Before
viewing any Jev result for an evaluation cohort, select and freeze a
representative task/step set, assign each task a human D0–D4 difficulty label,
and keep that label blinded from Jev. At outcome capture, require the
preassigned label and `--human-label-before-jev` attestation for every cohort
task. Outside that preselected cohort, human labels remain optional.

```sh
python3 build-agents-v1/codex/jev_shadow.py outcome \
  --record experiments/jev-shadow/events.jsonl --task-id TASK-ID --step-id S1 \
  --role builder --runtime codex --model SELECTED-MODEL --effort SELECTED-EFFORT \
  --attempts 1 --classification-event-id EVENT-ID --jev-status available \
  --predicted D2 --no-review-required --verified pass
```

The script uses only Python's standard library. It sends one request to Jev's
documented System One endpoint when explicitly invoked and appends JSONL under
`experiments/jev-shadow/`. Before reading the key, calling Jev, or appending an
event, it requires exactly one complete seven-column `Jev shadow telemetry`
row under `## The stores` in `MEMORY-CONTRACT.md`, with the exact path
`experiments/jev-shadow/events.jsonl` in its Files cell. A proposal or prose
mention, duplicate row, or incomplete row does not enable use. Until the human
applies that rule, it fails closed with no call and no event file. Tests use
mocked transport and keychain access; they never contact Jev.

For each ready, ungated step:

1. Record `in_progress` and the owner in PLAN.md. Give each attempt a stable
   number; never reset the total by replanning. Check recorded failures first.
   Before dispatching a factory role, append a `started` event to the local
   usage ledger with a stable run ID, passing `--model` with the model id you
   are running as (read it from the session; pass `unknown` only if the runtime
   does not expose it). After its handback and verification,
   append `finished` with the result, verification status, and any runtime usage
   values actually available. See `build-agents-v1/codex/README.md`; leave
   unavailable token and cost values unset. Never include prompts, source text,
   diffs, or private project details in the ledger.
2. Run `scripts/execution_manifest.py start` with the project root,
   task/step/attempt IDs, role, selected runtime/model/effort, role-profile mode,
   planned snapshot path and exact handback path. This creates the attempt's
   `execution.json`; use `unknown` for model or effort when the runtime does not
   expose them. Record any prior attempt in `--retry-of-attempt`. Then run
   `build_check.py snapshot <project-root> <evidence-path>` before dispatch.
   Store evidence in `work/build-evidence/<step>/attempt-<n>/`. The snapshot
   includes `execution.json`, so this coordinator-owned file is not reported as
   a builder change. Give the builder the goal, task, binding decisions, scopes,
   minimal source files, acceptance, and handback path
   `handoffs/in/<step>-attempt-<n>.md`.
3. Dispatch the builder, wait for completion, and stop it before verification.
   Run `build_check.py changes <project-root> <snapshot-path>` to inventory
   changes. This includes untracked files and material deletions. The snapshot
   omits its own exact file only; it does not excuse unrelated work/ changes.
4. Inspect the actual changes. Check scope, acceptance evidence, and the handback
   every time, even when tests exit zero. Run acceptance in the project directory
   after inspecting the command for approval gates. Reuse trustworthy recorded
   results when unchanged; do not rerun tests just to confirm an exit code.
   Use the gatekeeper for prose criteria, uncertain evidence, or failed checks.
   Script-checkable steps can be verified by the coordinator without a model call.
5. Run `scripts/execution_manifest.py finish` for the same step and attempt
   after verification, recording final state, change-inventory path, verdict
   references and failure class. An interrupted attempt also gets a finished
   state after reconciliation; never overwrite an existing finished manifest.
   Record attempt, evidence paths, verdict, and reason in control/LOG.md. Archive
   the handback into `work/build-evidence/` through conductor ingestion; retain
   all attempts. Only the coordinator marks done after all checks pass. A failed
   acceptance or scope check counts as a failed attempt. After three failures
   mark blocked and stop that step; no fourth attempt without user direction.
6. At every milestone and at the end, invoke the auditor with the goal, plan,
   deliverables, constraints, and evidence. Save its returned report under the
   evidence directory. A blocker prevents completion. Ask the architect for the
   smallest repair, preserve history, and continue safe work within authorization.

Use specialized document, spreadsheet, or domain skills for the artifacts being
built. A build agent does not replace their formatting or verification rules.

## Stop and resume

Nothing ready can mean blocked dependencies, interrupted work, a gate, or an
invalid plan. It means complete only when every required step is done (or a
recorded decision removed it), every required audit passed, and goal verification
passed. Readiness alone is not a completion test.

At an approval boundary, prepare the concrete result and record the exact action
for approval. Do not bypass a denied hook by rewording a command. Native tool
approval and prior user authorization still govern; hook matches are heuristics.

Before ending, stop/wait for all writers, update control state and the exact next
action, regenerate the dashboard, update only this project's portfolio row, and
release the lock with `build_check.py unlock <root> <same-session-id>`. Resume
unfinished attempts from evidence; do not dispatch an in_progress step twice.
Report what exists, verification, the stopping reason, and any action needed.
