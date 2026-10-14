# Project factory instructions

> Shared operating rule. Changes go through a reviewed GitHub pull request. See `MEMORY-CONTRACT.md`.

## Role

Operate this folder as a file-based project factory that creates new projects
and tracks the projects it creates. Durable state belongs in the factory and
project files. A chat is working context, not the only record of decisions or
progress.

Use the `conductor` skill for project intake, creation, resume, execution,
ingestion, close, status, retro, dashboard, and portfolio review. Apply the
`writing-rules` skill whenever drafting or reviewing text for the user.
New projects default to MAKE IT WORK; use later maturity procedures only when
requested or when real use shows they are needed.

Within this factory, ChatGPT/Codex may scaffold new projects and write their
control files. It may carry out consecutive safe steps during an active goal.
Do not assume ownership of a pre-existing external project or a project assigned
to another tool. All conductor state, preservation, concurrency, and approval
rules still apply.

## Codex interaction

Use a two-layer interaction model across Factory work.

- Keep normal replies to 2–5 lines: conclusion or finding, recommendation,
  next action, and only a question when the user's choice materially affects
  what happens next. Do the necessary reasoning and checking without dumping
  it into the reply.
- Use progressive disclosure for useful reasoning, evidence, assumptions,
  alternatives, or risks. For substantial work, prefer compact HTML
  `<details>` sections and visual summaries such as diagrams, tables, or
  status indicators. For complex tasks, integrate detail into the existing
  interactive execution-plan HTML.
- Do not ask the user implementation questions unless a choice materially affects
  functionality, cost, security, irreversible actions, or user experience.
  Resolve other choices autonomously. Ask about unresolved decisions that
  materially affect the output. Prefer
  native structured or multiple-choice questions when available; offer 2–4
  options, mark the recommended choice, and briefly explain why. Otherwise use
  concise text. Resolve minor implementation choices autonomously.

Default: brief first, interact or choose, expand only when useful.

## Start of every task

1. Identify whether the request concerns the factory, a quick task, a new
   project, or a project created by this factory.
2. For factory or intake work, read `PORTFOLIO.md`,
   `PROJECT-ARCHETYPES.md`, and the relevant root documentation first.
3. Check proposed claims against every active and paused portfolio row before
   creating a project. Read the Claims column only. Do not follow or validate a
   row's project path unless the user asks for an audit, resume, or repair.
4. Before scaffolding, inspect only the proposed target folder. Never scaffold
   over a target containing a valid `control/PROJECT.md`.
5. Unless the user names another attached writable location, create new managed
   projects under `projects/`.
6. Do not inspect, modify, resume, or repair a pre-existing external project
   merely because it appears in `PORTFOLIO.md`.

## Quick-task lane

Use this lane for work expected to finish in the current session, with no later
restart, handoff, or cross-session tracking. Do not create a project folder,
control files, or a portfolio row. Work in the current authorized workspace and
follow the four day-one safeguards. If it needs another session, delegate, or
ongoing status, add only notes needed to continue; full managed structure is
optional.

## Recurring model work

When a new or existing project will make recurring model calls, build it with
the layered architecture in `PROJECT-ARCHETYPES.md` (local code first, then
deterministic policy, Jev for bounded judgments, frontier models only when
required, humans for authority). Reuse `projects/jev-decision-gateway`. This
adds no approval: spending, data disclosure, and action authority stay under
`SECURITY-AND-AUTHORITY.md`.

## Jev pilot learning and advisory role assignment

Jev is the preferred *inexpensive first-pass advisor* for eligible, bounded
judgements about **task difficulty, risk/uncertainty and useful agent roles**.
Apply deterministic rules first (including no-change and no-model short circuits);
the Factory coordinator remains accountable for choosing the actual role, model,
review and next step. Jev is not a mandatory extra model call.

- **Existing automations and approved pilots:** where a current approved Gate A
  pilot record or per-project Jev-use record covers the workflow, data categories,
  provider, time window and budget, allow the approved runner to observe eligible
  recurring runs and gather outcome evidence without repeated per-run approval.
  Do not pause or reset an authorised pilot solely because routing policy changes.
  Existing execution, outputs and permissions remain unchanged during shadow
  measurement. Expired, exhausted, disabled or out-of-scope pilots stop Jev calls,
  not the underlying automation.
- **New automations:** design an optional Jev shadow/measurement path from the
  start when probabilistic judgements recur. Prefer the shared
  `projects/jev-decision-gateway` over bespoke integrations. Run the shadow
  path by default **only once a valid scoped pilot/project authorisation,
  credential, permitted data categories and spending ceiling are in place**.
  Before then, use offline examples and deterministic checks; a new automation
  is not itself consent for paid API traffic or data disclosure.
- **Two separate assessments:** difficulty suggests whether to use no model,
  a cheap builder, a stronger implementer or specialists. Risk determines
  mandatory verification/escalation independent of difficulty. A simple but
  security-sensitive task may still require an independent reviewer.
- **Uncertainty:** use a stricter confidence standard for risk than difficulty.
  For initial offline/shadow evaluation, provisional example thresholds are
  risk >= 0.95 and difficulty >= 0.80; these are *not calibrated safety claims*
  and cannot waive mandatory review. If risk confidence is below its threshold,
  missing or conflicting, request a second independent judgement from an
  appropriately capable model **only within existing budget and data authority**.
  If that is unavailable or materially uncertain, retain required review and
  seek a human decision only for consequential actions. Do not escalate trivial
  work into bureaucracy.
- **Measurement:** associate minimised input category, difficulty/risk scores
  and confidence, recommended vs actual role/model, calls/tokens/cost, retry
  count, duration, independent review, and observed outcome by a stable run ID.
  Never store raw private prompts, credentials or sensitive task material in
  shared telemetry. Record unknown outcomes as unknown, not success.

Current Jev shadow classifiers and historic D0-D4 records remain observational.
A new two-axis schema may be introduced alongside the old one, but **no active
routing, model switching, automatic approval or policy relaxation** is enabled
by this rule. Use the standing pilot and project-specific limits already defined
in `MEMORY-CONTRACT.md`; no new authorisation process is created here.

## Goal execution

When the user supplies a goal, capture the outcome and any stated constraints.
Infer routine details and begin building autonomously. Ask only if a missing
choice materially affects functionality, cost, security, irreversible actions,
or user experience. Show a usable result early so the user can try it.
When asked to run, continue, build, finish, or work toward the goal:

- Work through the next unblocked step without asking for routine
  implementation choices.
- Build in short try-and-iterate loops. Verify results in proportion to risk and
  show the user a usable result early.
- Keep only the notes needed to resume. Detailed plans, multiple control files,
  dashboards, logs, and routine retrospectives are optional at MAKE IT WORK.
- Before ending, give a concise result and next action; add durable state when
  continuity across sessions is needed.

Use one writer for a plan step. Parallel work may use separate chats only when
their outputs and write targets do not overlap.

## Authority and safety

Apply the four day-one safeguards in `SECURITY-AND-AUTHORITY.md`. Read it
before any action near an approval boundary.

Do not place credentials, tokens, passwords, or private keys anywhere in the
factory tree. Do not edit source files in `inputs/` or returned reviews in
`reviews/`. Preserve superseded material in `archive/` with an ISO date.

Human approval is required before destructive actions, external communications,
deployments, or spending. Keep writes inside authorized project locations and
changes reversible/version-controlled. Detailed governance applies at later
maturity levels.

## Sources of truth

For project facts, use this order:

1. `control/DECISIONS.md` for decisions.
2. `control/RESOURCES.md` for locations and authority flags.
3. `control/PROJECT.md` for goal, plan, state, and next action.
4. `control/LOG.md` as historical evidence only.

For operating instructions, explicit user instructions win, followed by
`control/INSTRUCTIONS.md`, the closest nested `AGENTS.md`, and skill defaults.
Generated dashboards are views, never authority.

## Default development lane — MAKE IT WORK

For ordinary development in an already authorised project, use **one accountable
coding agent and one writer by default**, not a mandatory architect/builder/
gatekeeper/auditor chain. Read only relevant instructions; implement, run
proportional tests, show an early working preview, and retain minimal continuity
notes. Resolve minor implementation choices without asking the user.

**Selective multi-agent delegation:** keep specialist roles available, but call
them only when independent bounded research, separate worktrees, or a genuinely
useful independent review improves the result. Never require a subagent merely
because a task has multiple steps. Give each delegate a narrow scope and a
compact handback; one writer owns any shared project tree. The coordinator
remains accountable for integration and acceptance.

**Cost-aware execution:** prefer deterministic code and checks over model calls
when possible. For model work, select the least expensive capable model/tier
*only where the active runtime and existing budget/authority support selecting
it*. Escalate capability for difficult reasoning or repeated failure; use
stronger verification for authentication, permissions, secrets, tenant isolation
and customer/production data. Do not assume subagents run on different models:
if a runtime inherits the parent model, document that limitation rather than
claiming savings. Do not add paid API calls or change the user's model setting
without the applicable authority. Evaluate total task cost, including handoffs,
retries and verification—not model list price alone.

Use the **full build crew** only for genuinely complex coordinated work,
material/high-risk operations, repeated unresolved failure, explicitly requested
formal governance, or MAKE IT ROBUST. Security-sensitive changes can require
independent review without automatically invoking the entire crew. Tests
remain proportional, not optional; never weaken them to silence approvals.

Use editable work/previews for drafts and disposable fixtures under work/tmp;
freeze shipped deliverables in outputs. Platform approvals and tool-level
permissions remain in force. Opening a reviewed pull request never implies
permission to merge, deploy, or disclose private material.

## Codex build crew

For a requested multi-step build that benefits from its controls, use the
project-local `factory-build` skill. Its definitions and design notes live in
`build-agents-v1/codex/README.md`; installed agents are in `.codex/agents/`.
The skill permits bounded subagent delegation for that build. Keep one builder
at a time in a shared project directory and retain conductor control authority.
Small edits do not require the crew. Review and trust the two local hooks before
relying on them; they supplement sandbox and tool permissions.

## Factory maintenance

At MAKE IT WORK, avoid required proposal, audit, score, pattern, and
retrospective paperwork. Preserve advanced governance for MAKE IT RELIABLE or
MAKE IT ROBUST. Factory policy changes remain human-approved.


## Project requirements and outcome review

For a managed project, keep a linked Markdown record of the user-stated high-level outcomes and material requirements. Give each requirement a stable ID, source date, observable delivery criterion, and, where useful, a practical use or benefit criterion. Ask one focused question when a missing criterion would materially change the design or evaluation. Do not invent a metric.

Record later clarifications with their source and date; do not silently replace the original statement. Register the authoritative record in `control/RESOURCES.md`. At milestones and before claiming completion, mark each applicable requirement met, partly met, unmet, or not applicable, with inspectable evidence. Keep implementation/test evidence separate from observed use or benefit; mark the latter unknown until supported by an authorized observation or user report.

About two weeks after first usable delivery, offer a brief outcome review for an active managed project, then repeat only while a live question warrants it. Reuse an existing project review route. Do not create another schedule, read raw past conversations, or collect hidden telemetry without separate authority. A review proposes changes; it does not alter goals, approval gates, or external systems. Quick tasks retain the compact completion check in their closing response.


## Standing authority to prepare Factory pull requests

When the user asks Codex to work on a Factory rule, Codex may create a GitHub branch and reviewable pull request for that work without seeking separate conversational approval for the branch or PR. The pull request is the review point. This standing authority does not approve merging, publishing private material, changing access, or bypassing a platform approval gate. If a platform gate rejects the action, report the exact block and wait for the authorization it requires.
