# Project archetypes

> Shared operating rule. Changes go through a reviewed GitHub pull request. See `MEMORY-CONTRACT.md`.

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
6. If the project will make recurring model calls, build it with the layered
   architecture below.

## Recurring-AI architecture

Applies when a project, at any archetype or weight, makes recurring or
high-volume model calls over sources that repeat or change slowly. Newly
started tasks, including work in an existing project, and quick tasks still use
the Jev opportunity check in `AGENTS.md` without requiring this whole
architecture. Build a recurring project this way from the start:

```
raw sources
  → reuse existing scripts · skills · native automations · libraries
      └─ where useful: filter · diff · dedupe · calculate · cache · validate
          └─ nothing relevant changed → stop, no model call
  → deterministic policy: hard rules, exact lookups, calculations
  → Jev: bounded decisions; bundle independent questions over the same compact state when useful
      └─ clear → continue
      └─ novel or uncertain → frontier model, only when required
  → human, for authority decisions
```

- Reuse the shared contracts of `projects/jev-decision-gateway`
  (`decide()` and the `preprocessors/`). Do not build a per-project Jev
  integration or a second set of compilers.

  
### Reuse-before-build rule

At intake, identify existing scripts, configured automations, skills, standard
libraries, connectors and native application capabilities that already perform
the deterministic operation. Prefer reusing or configuring these over creating
a new standalone script. "Deterministic first" is an execution preference,
**not** an instruction to write new code for every project.

Only build a new reusable preprocessor when the expected repeated usage, avoided
model work, reliability gain or cross-project benefit reasonably outweighs
implementation, verification, deployment and maintenance effort. Make this a
brief engineering judgment, not a compulsory business case. A small, safe,
project-local adjustment to an existing workflow may be justified without
creating a new shared component.

If a custom preprocessor does not yet justify its cost, use the simplest
working alternative, including an authorised Jev judgment where appropriate;
do not block project delivery just to save occasional tokens. Record a
specific candidate only when there is observed friction or credible recurrence:
project-local ideas stay in the project's existing log; reusable cross-project
patterns go to the Factory `LESSONS.md` with evidence, scope and review date.
The existing Factory portfolio review checks recurrence and can propose a
shared improvement; it does not auto-build it. Keep general tool bugs in the
automation system's `BUG_LOG.md`, and running-automation incidents in their
existing health checks. Do not create another review schedule or backlog.
- Code owns known rules, exact extraction and calculation, permissions,
  execution, and mandatory surfacing or review. Jev classifies facts,
  relevance, ambiguity, severity, materiality, difficulty, or review
  usefulness. Frontier models handle novel reasoning, synthesis and drafting.
  Humans hold approval.
- Jev is never the final authority for deletion, spending, external
  communication, deployment, access changes, financial transactions, security
  alert suppression, technical or compliance correctness, or waiver of a
  required review. A Jev answer cannot remove a review or alert that policy
  requires.
- Keep a valid Jev label and confidence visible as advisory evidence,
  including at low confidence. The coordinator may use deterministic fallback
  or a higher tier when the decision contract warrants it. A missing provider
  uses the available offline path or next tier; never silently drop a required
  item.
- Record privacy-preserving usage (calls, approximate tokens, duration, result,
  context hashes), never raw private content, so savings are measured, not
  assumed.
- Jev calls remain spending and external data disclosure under
  `SECURITY-AND-AUTHORITY.md` and the standing authorization in
  `MEMORY-CONTRACT.md`. This section adds no separate approval.

## Jev as an advisory dispatcher — existing and new automations

The coordinator uses deterministic classification first, then may ask Jev for
a bounded recommendation on **difficulty**, **risk** and **role usefulness**
(e.g. direct builder vs architect + builder vs independent reviewer). It may
choose different model tiers per role only if the runtime actually supports
that choice; otherwise it records model inheritance and does not claim savings.

**Do not conflate risk with difficulty.** Evaluate them separately even when
the provider exposes only one Score call: the adapter may bundle two named
judgements over the same minimal state. Preserve historical D0-D4 observer
records rather than silently reinterpreting D4 as the new risk axis.

Pilot evaluation hypotheses only. These thresholds do not gate ordinary
live Jev advice for new Factory projects or quick tasks. Show valid advice with
its confidence by default. A caller may apply a decision-specific confidence
floor when evidence and the task warrant one; mandatory reviews remain
deterministic.

| Axis | Example assessment | Low-confidence handling |
|---|---|---|
| Difficulty | D0 script/no model; D1 routine; D2 standard; D3 complex | Pilot threshold 0.80; during evaluation, use a capable default agent or escalate after failure |
| Risk | R0 negligible; R1 reversible/local; R2 sensitive; R3 material/high impact | Pilot threshold 0.95; during evaluation, seek an independent judgment if authorised, otherwise retain review and stop at any required human gate |

These values are **provisional evaluation hypotheses**, not calibrated accuracy
claims or security guarantees. Calibrate against verified outcomes and audit
false negatives. For any mandatory security, financial or production gate,
deterministic policy wins even when Jev reports low risk with high confidence.
A second model may strengthen evidence but can never grant permissions, waive
an approval or override an existing human-only gate.

**New project = live; existing automation = unchanged until evaluated.** At project
intake, first look for existing off-the-shelf scripts, automations and tools
that can filter, diff, dedupe or cache inputs. Check whether an unchanged
run can stop with **zero** model calls, and apply the reuse-before-build
trade-off above before writing a dedicated preprocessor. Use exact code for
rules and must-surface conditions. For every new recurring-AI project with
useful bounded judgement, integrate the shared `decide()` contract and
preprocessors; do not duplicate provider integrations. Under the standing Jev
authorization, make Jev an ordinary **live advisory input from the first
operational run** when the provider route, permitted input and offline
safeguards are ready. Do not defer a new project's useful Jev decisions solely
to collect shadow data or obtain a repeated project-use approval. If the live
route is unavailable, continue deterministically and record that gap.
Existing automations keep their current behavior while evidence from first
uses is gathered. For failures or ambiguous judgments preserve deterministic
fallback and mandatory reviews; do not discard work silently. Record the
decision type, minimized input category, model version, advice, outcome when
known, calls, costs and overrides without raw private content. Review early
disagreements and adjust the question, criteria or threshold based on evidence;
do not claim savings without a no-Jev baseline.

An **existing shadow route** may move to live advice after representative
route-specific evidence, a reversible change and verified activation under
its normal authority. Honor an applicable Gate B or project-specific gate,
but do not impose Gate B on every existing task. More complex decisions may be
tried in a bounded advisory role after simpler uses show where Jev succeeds
and fails. Jev never gains action authority or waives a mandatory review.

## Choosing wrong costs little

The chassis is the same underneath every archetype; a mischosen shape is corrected by adding a folder or splitting a file, and the conductor performs both without data loss. This is the reason the axes are presets rather than hard categories — the factory should decide in one minute, not model the project perfectly at birth.
