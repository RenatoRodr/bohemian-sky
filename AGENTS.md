# Project factory instructions

> Store: operating rules. Writers: human only. See `MEMORY-CONTRACT.md`.

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
