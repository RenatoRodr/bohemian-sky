# ChatGPT setup

> Shared operating rule. Changes go through a reviewed GitHub pull request. See `MEMORY-CONTRACT.md`.

## Recommended setup

Use this folder as a local project in the ChatGPT desktop app and make it the
primary folder. Local projects give ChatGPT direct access to the control files
and outputs. The root `AGENTS.md` supplies the persistent operating rules for
new chats.

No additional project-instructions text is needed in the ChatGPT interface for
this local project. Start a new chat after changing `AGENTS.md`; Codex reads it
when a run starts.

Use a ChatGPT web project only when all required sources can be uploaded or
connected. A web project does not have direct access to this local folder.

Set the sandbox to workspace-write. Keep approval for network access and writes
outside the workspace. Full access is unnecessary for the factory's normal
work.

## Starting a project

For work expected to finish in this session, with no delegate or ongoing
tracking, use the quick-task lane. State the task, constraints, verification,
existing material, and sensitivity. Do not scaffold a project or add a portfolio
row. If the work needs another session or coordination, promote it to a Light
managed project before continuing.

Open a new chat in this local project and give the intake information:

```text
New project.

Outcome: <the observable result and who it is for>
Constraints: <boundaries, required tools or formats, and approaches to avoid>
Verification: <tests or review criteria that prove it is done>
Deadline or cadence: <date, recurring cadence, or none>
Existing material: <files, folders, links, conversations, or nothing>
Sensitivity: <what must stay local or must not reach another service>
```

The factory checks portfolio overlap and proposes one project shape. Approve or
adjust that proposal before scaffolding.

The overlap check reads the Claims column. It does not require access to the
folders of projects already listed in the portfolio.

For an extended run, start Goal mode with a measurable statement:

```text
/goal Build <result>. Respect <constraints>. It is done when <verification>.
Use the managed project's control files, work through every safe unblocked
step, and stop only at a documented approval gate or unresolved blocker.
```

Use a separate chat for each distinct outcome. Do not let two chats modify the
same files. For parallel code work, use separate Git worktrees.

## Returning later

Start a new chat in the same local project and say:

```text
Resume <project name>. Read its control files, verify registered paths, carry
out the next safe action, and continue until the goal is verified or an
approval gate is reached.
```

The control files, rather than chat memory, carry the project between sessions.

## Instructions and memory

`AGENTS.md` contains rules that must apply whenever this local project is
opened. A child project's `control/INSTRUCTIONS.md` contains behavior specific
to that child project. Code-only conventions belong in the closest
`code/AGENTS.md`.

Codex memories are optional personal recall. They are stored separately from
ChatGPT web memory and may be disabled. Do not use memory as the only place for
factory rules, project decisions, paths, or current status.

## Background execution

Goal mode continues a long run while the chat is active. It keeps the current
sandbox and approval boundaries.

For work that must resume on a clock, create a scheduled task in the ChatGPT
desktop app. Point it at the local project and give it a durable prompt that
defines what to do on each run, when to report, and when to stop. Keep the Mac
awake and the app running when the task needs local files. Test the prompt in a
normal chat before scheduling it.
