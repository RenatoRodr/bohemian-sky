# Master prompts

> Store: operating rules. Writers: human only. See `MEMORY-CONTRACT.md`.

Seven prompts, ready to copy. Once the conductor skill is installed, the short trigger phrases replace most of these in Cowork; the full texts exist so the same procedures run in any LLM that has never seen the skill — portability is the point.

## 0. Quick task — finish in this session

```text
Quick task. Complete this in the current session without creating a managed
project or portfolio row.

Task: <the result I need>
Constraints: <boundaries, tools, format, or approaches to avoid>
Verification: <how to tell it is done>
Existing material: <files or context, or "none">
Sensitivity: <what must stay local or avoid another service, or "none">

If the work needs another session, a delegate, or ongoing status, create only
the lightweight notes needed for continuity; full managed-project machinery is
optional until a later maturity stage warrants it.
```

## 1. Fast start — default for any project

```
Build this outcome: <what should work for me>
Constraints: <material boundaries, if any>

Choose routine implementation details yourself. Ask me only if a choice
materially affects functionality, cost, security, irreversible actions, or
user experience. Keep secrets/API keys outside the repo, write only in
authorized project locations, get approval for destructive actions, external
communications, deployments, or spending, and keep changes reversible.
Show me a usable result early so I can try it; then iterate from my feedback.
```

## 2. Intake — optional managed-project setup

```
New project. Before creating anything, read PORTFOLIO.md and
PROJECT-ARCHETYPES.md in my Project factory folder.

The goal: <what done looks like, one or two sentences>
Deadline or cadence: <date, or "none">
What already exists: <files, folders, email threads, prior chats — or "nothing">
Sensitivity: <anything that must not leave my machine or reach a third-party
LLM; or "none">

Do, in order:
1. Check my proposed scope against the Claims column of the portfolio and
   name any overlap before proceeding.
2. Choose sensible defaults and begin the first build step. Ask only if a
   choice materially affects functionality, cost, security, irreversible
   actions, or user experience.
3. Use a lightweight scaffold only if continuity requires it. Full portfolio
   registration, restart briefs, and intake approval belong to later maturity
   stages or an explicit request.
```

## 3. Resume — optional continuity

```
Resume <project>. Read the control files, verify registered paths, and give
me the restart brief: goal, next action and owner, current position, plan,
blockers, last two log entries, authoritative resources. Flag anything
stale, missing, or contradicting the portfolio row. Then wait.
```

## 4. Delegate — hand a step to another LLM

```
Delegate step <N> to <tool>. Build the handoff as a self-contained prompt:
the task; the goal in one line; the binding decisions by number, quoted;
the input material itself (inline or attached — the delegate has no file
access); required output format and exact filename; and the return
instructions: return the complete file, list anything you changed beyond
the ask, list open questions, do not summarise the input back to me.
Save it to handoffs/out/ and mark the step in progress with that owner.
Refuse if the step already has one.
```

## 5. Independent review — a different model than the drafter

```
You are reviewing work you had no part in producing. Attached: the
deliverable and the requirements it must meet. You do not get the drafting
conversation, on purpose.

Report only findings: numbered, each with severity (blocker / should-fix /
note), the exact location, and the smallest fix. Judge against the
requirements and against internal consistency. Do not rewrite the work, do
not praise it, do not summarise it. A review with zero findings must state
what you checked to earn that.
```

## 6. Retro — optional at later maturity stages

```
Retro for <project>, milestone <name or "final">. From LOG.md and your own
observation of this project: what cost time or attention that the system
should have prevented? For each item, tag it — template, skill, prompt,
archetype, or process — and state the smallest factory change that would
have prevented it. Append the tagged entries to LESSONS.md in the Project
factory folder. Do not change any factory file; changes happen at portfolio
review, with my approval.
```

## 7. Chief-of-staff briefing — optional portfolio governance

```
Portfolio review. Read PORTFOLIO.md and LESSONS.md in my Project factory
folder. Report, in this order and nothing else:
1. Needs my attention today: blockers, waiting-on items now overdue,
   approvals I owe.
2. Stalled: active rows whose Updated date is 7+ days old — name the
   project and its last known next action.
3. Overlaps or claim conflicts.
4. Lesson patterns: any tag+problem appearing twice or more, with the
   concrete factory change you propose for each. Wait for my approval
   before touching anything.
5. Register honesty check: rows that contradict their project's
   PROJECT.md, if you have access to spot-check them. Files win.
Nothing to report in a section: say "clear" and move on.
```
