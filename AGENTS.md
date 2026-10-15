# Project factory instructions

> Shared operating rule. Changes go through a reviewed GitHub pull request. See `MEMORY-CONTRACT.md`.

## Role

Operate this folder as a file-based project factory that creates new projects
and tracks the projects it creates. Durable state belongs in the factory and
project files. A chat is working context, not the only record of decisions or
progress.

Use the `conductor` skill for managed-project lifecycle work that needs its
control-file procedures, including resume, execution tracking, ingestion, close,
status, retro, dashboard, and portfolio review. A lightweight MAKE IT WORK
request does not require formal intake or a separate scaffold approval. For a
new software goal, the request authorizes reversible setup and implementation
in an authorized target location: perform the quick duplicate check and
target-folder inspection below, infer routine choices, create only the
continuity files needed, and begin building. If the skill is triggered, this
current Factory rule overrides any embedded legacy intake or approval sequence.
Ask only when a missing decision materially affects functionality, cost,
security, an irreversible action, or user experience.
Apply the `writing-rules` skill whenever drafting or reviewing text for the user.
New projects default to MAKE IT WORK; use later maturity procedures only when
requested or when real use shows they are needed.

Within this factory, ChatGPT/Codex may scaffold new projects and write their
control files. It may carry out consecutive safe steps during an active goal.
Do not assume ownership of a pre-existing external project or a project assigned
to another tool. Applicable security, source-authority, preservation,
concurrency, and approval rules still apply; skill defaults do not add gates
that current Factory policy does not require.

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

When a new or existing project will make recurring model calls, use the
layered architecture in `PROJECT-ARCHETYPES.md`: reuse existing scripts,
skills, libraries and native automations before writing preprocessing code;
apply deterministic policy, then Jev for useful bounded judgments, frontier
models only when required, and humans for authority. Reuse
`projects/jev-decision-gateway`. Do not build a dedicated script merely to
avoid one model call: assess likely recurrence, saved work, reuse elsewhere,
build/test effort and maintenance first. This adds no approval: spending, data
disclosure and action authority stay under `SECURITY-AND-AUTHORITY.md`.

## Jev pilot learning and advisory role assignment

Jev is the preferred *inexpensive first-pass advisor* for eligible, bounded
judgements about **task difficulty, risk/uncertainty and useful agent roles**.
Apply deterministic rules first (including no-change and no-model short circuits);
the Factory coordinator remains accountable for choosing the actual role, model,
review and next step. Jev is not a mandatory extra model call.

- **Existing automations and approved pilots:** make no change to the execution
  path merely because this policy changes. A separately approved existing-route
  pilot may observe eligible recurring runs in shadow within its exact Gate A
  scope, expiry and budget, without further per-run approval. Jev failure or
  pilot expiry stops Jev observations, not the original automation. Promotion
  of an existing route to live requires representative evidence and Gate B.
- **New Factory projects:** include the shared Jev adapter whenever recurring
  bounded judgement is useful. Ask at intake: "Which existing script, skill,
  library, native automation or connector can filter, diff, dedupe or cache
  this? Can an unchanged run stop with zero model calls? If new code is needed,
  does expected recurrence and reuse justify building, testing and maintaining it?"
  When there is no new relevant state, stop without a model call. Otherwise,
  **use Jev live from the first authorised operational run, not in shadow**,
  after Renato approves the exact project-use record in `MEMORY-CONTRACT.md`
  and credentials, billing, privacy, caller fallback and offline safeguards
  have been verified. This is one project-level approval, not per-run approval.
  New projects must reuse `projects/jev-decision-gateway` and its `decide()`
  contract; never create a duplicate Jev integration. Before approval, use
  deterministic/offline paths. Project creation is not itself consent for paid
  API calls or data disclosure. A shadow-pilot Gate A record cannot approve
  live project operation. An approved live judgement is an advisory input;
  code alone retains permissions, actions and mandatory reviews.
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
A new two-axis schema may be introduced alongside the old one, but **no
promotion of existing shadow routes, model switching, automatic approval or
policy relaxation** is enabled by this rule. Separately authorised new-project
Jev inputs remain advisory: caller code owns all actions, hard rules and required
reviews. Use the standing pilot and project-specific limits already defined in
`MEMORY-CONTRACT.md`; no new authorisation process is created here.

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

Use one accountable agent and one writer by default. Read relevant instructions,
build a usable result early, run proportionate checks, and keep continuity notes
minimal. Resolve routine choices autonomously.

Delegate only when a bounded independent task, separate worktree, or useful
independent review improves the result enough to justify coordination. The
coordinator remains accountable for integration and acceptance. A coordinator
may create and maintain the working plan, scope, and acceptance criteria as
needed. A delegated builder may report a needed change but cannot edit the
authoritative plan or redefine acceptance. An independent auditor reviews
against the user goal and agreed criteria; an auditor cannot certify work they
implemented. Architecture review, builders, and audits are available roles, not
mandatory gates. Use the smallest set of roles that fits the task.

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

Use the **full build crew** only for genuinely complex coordination,
material/high-risk operations, repeated unresolved failure, explicitly requested
formal governance, or MAKE IT ROBUST. Security-sensitive changes may need an
independent review without requiring the whole crew. Verification is
proportionate to risk and consequence; do not weaken a required check to bypass
a denial.

Use editable work/previews for drafts and disposable fixtures under work/tmp;
freeze shipped deliverables in outputs. Platform approvals and tool-level
permissions remain in force. Opening a reviewed pull request never implies
permission to merge, deploy, or disclose private material.

## Codex build crew

Use the project-local `factory-build` skill only when the full crew's
controls materially help: genuinely complex coordination, material risk,
repeated unresolved failure, explicit request for a formal crew, or MAKE IT
ROBUST. A multi-step task or existing `PLAN.md` alone does not justify it.
Its definitions and design notes live in `build-agents-v1/codex/README.md`;
installed agents are in `.codex/agents/`. Keep one builder at a time in a
shared project directory and retain conductor control authority. Small or
ordinary MAKE IT WORK builds use the default one-agent lane above. Review and
trust the two local hooks before relying on them; they supplement sandbox and
tool permissions.

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
