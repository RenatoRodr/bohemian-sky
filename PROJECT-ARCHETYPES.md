# Project archetypes

> Store: operating rules. Writers: human only. See `MEMORY-CONTRACT.md`.

The architecture is not always the same. Choose a shape autonomously when
managed structure is useful. The four safeguards in SECURITY-AND-AUTHORITY.md
apply at every maturity level; files, portfolio rows, and detailed state are
optional at MAKE IT WORK.

## Quick-task lane

A quick task is work expected to finish in the current session, with no delegate,
later restart, or ongoing status to track. It is not a managed project: work in
the current authorized workspace without creating a project folder, control
files, or a portfolio row. Keep the request and response self-contained in the
chat. Apply the same security and approval gates as managed work.

If it needs another session, a delegate, or ongoing status, add only the notes
needed to continue. Full managed-project structure is optional until a later
maturity level or the user's request warrants it.

## Axis 1 — weight

| Weight | Control plane | When |
|---|---|---|
| Light | PROJECT.md + LOG.md only; decisions and resources as sections inside PROJECT.md; no dashboard unless asked | Under ~2 weeks, one or two delegates, low stakes |
| Standard | The full four control files + INSTRUCTIONS.md + dashboard | Multi-week, several delegates, external parties |
| Heavy | Standard + code/AGENTS.md and/or per-round review folders | Code involved, or formal external review cycles |

Weight can move up mid-project (light → standard splits the inline sections out into their own files; the conductor does this on request). Moving down is archiving, not restructuring.

## Axis 2 — type

| Archetype | Folder emphasis | Plan style | Default delegates | Default autonomy |
|---|---|---|---|---|
| review-consolidate (documents in, comments/replies out — a technical document review pattern) | inputs/, reviews/roundN/, handoffs/ | Rounds, each round a step block | Bulk drafting: assistant selected by the user; independent review: a different assistant | 2 |
| build-artifact (a deliverable is made: document, deck, tool) | work/ → outputs/; code/ if software | Milestones with acceptance criteria | Implementation: assistant selected for the artifact; independent review: a different assistant | 2 |
| research-decide (question in, recommendation out) | inputs/, work/; outputs/ holds the recommendation | Questions to close, then a decision step | Gathering: web-capable assistant selected for the task; counter-argument: a different assistant | 2 |
| operate-admin (filings, moves, applications, life ops) | Light weight almost always; inputs/ for received paperwork | Checklist; steps are tasks, not workstreams | Usually none; otherwise assistant selected by the user | 1 (external parties and irreversible submissions everywhere) |

Defaults are proposals. INSTRUCTIONS.md records deviations per project; a deviation that keeps recurring is a lesson (tag: archetype) and eventually a change to this file.

## What the intake conversation decides, in order

Choose routine setup details autonomously; these are presets, not required
questions. Ask only when a choice materially affects functionality, cost,
security, irreversible actions, or user experience.

1. MAKE IT WORK by default; raise maturity only when warranted.
2. Choose archetype and weight if managed structure is useful.
3. Start with the next concrete action; expand a plan during execution only if needed.
4. Check portfolio claims when registering a managed project.
5. Set autonomy only when it changes a meaningful boundary.

## Choosing wrong costs little

The chassis is the same underneath every archetype; a mischosen shape is corrected by adding a folder or splitting a file, and the conductor performs both without data loss. This is the reason the axes are presets rather than hard categories — the factory should decide in one minute, not model the project perfectly at birth.
