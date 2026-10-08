# Portfolio specification

> Shared operating rule. Changes go through a reviewed GitHub pull request. See `MEMORY-CONTRACT.md`.

PORTFOLIO.md is the one high-level file. Everything above a single project reads it; every project writes to it. It exists so that an AI chief of staff (or the user, or any LLM handed the file) knows in one read what is going on, what is stuck, and what would collide with what.

## Format

```markdown
---
updated: 2026-07-19
---

# Portfolio

## Active

| Project | Archetype | Status | Next action | Owner | Waiting on | Claims | Path | Updated |
|---|---|---|---|---|---|---|---|---|
| Document review batch | review-consolidate | active | Ingest independent review | claude | – | Revision 04 replies; external stakeholder thread | projects/example-review/ | 2026-07-18 |

## Paused

(same columns)

## Done — last 90 days

| Project | Finished | Outcome | Lessons filed |
|---|---|---|---|

## Cross-project notes

Free lines for things no single project owns: shared deadlines,
sequencing between projects, capacity warnings.
```

Column meanings worth pinning: **Waiting on** is the external blocker (a person, a returned review, a date) — the chief of staff chases these. **Claims** is what the project owns: documents, folders, external threads, decision areas. Claims are prose, not paths only; "replies to an external review round" is a claim even though it is not a file.

## Rules

1. One row per project, one writer per row. A project's close routine rewrites its own row and touches nothing else. Only the portfolio review routine may restructure the whole file.
2. The row is a cache, the project files are the truth. On any mismatch, PROJECT.md wins and the row gets corrected — never the reverse. Rows carry their Updated date precisely so staleness is visible.
3. Overlap check at intake: before a new project is scaffolded, its proposed claims are read against every Active and Paused row. A hit is not a veto — it is a forced conversation ("this overlaps an existing review project's claim on an external thread; same project, dependent project, or genuinely separate?") recorded as a decision in whichever project wins the claim.
4. No secrets, no content. The portfolio points and summarises; it never contains draft text, reviewer names beyond what a shared file can hold, or anything from the security ban list.
5. Done rows keep outcome and lessons pointers for 90 days, then move to the bottom of the file under a collapsed history heading. Nothing is deleted.

## The chief-of-staff read

Any LLM given PORTFOLIO.md plus the briefing prompt in MASTER-PROMPTS.md can answer: what is active, what moved lately, what is stalled (Updated old while status active), what is waiting on whom, what overlaps, and what patterns sit unresolved in LESSONS.md. That is the whole job description. The chief of staff proposes; changes to projects go through each project's own conversation and routines, because the portfolio is a map, and redrawing a map moves no terrain.

## Failure behaviour

If PORTFOLIO.md is lost, it is rebuilt by scanning project folders for control/PROJECT.md frontmatter — ten minutes of work, because every fact in it is a cache of files that still exist. If a project stops reporting (row stale, project alive), the portfolio review flags it; the fix is running that project's close routine, not editing the row by hand.
