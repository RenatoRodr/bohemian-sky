# Project factory — blueprint

> Shared operating rule. Changes go through a reviewed GitHub pull request. See `MEMORY-CONTRACT.md`.

This folder is the factory root. The factory is the layer above any single project: it births projects adapted to their goal, keeps one portfolio file every project reports into, and improves its own templates from recorded lessons. The per-project machinery (control files, conductor skill, dashboard) is the chassis. Its retained build package is in `conductor-build-v1/`; the active procedure is the installed `conductor` skill.

## What lives at the factory root

| File | Role | Written by |
|---|---|---|
| AGENTS.md | Persistent ChatGPT/Codex operating rules for this local project | Reviewed GitHub pull request |
| CHATGPT-SETUP.md | How to run the factory in ChatGPT desktop, Goal mode, and scheduled tasks | Reviewed GitHub pull request |
| FACTORY-BLUEPRINT.md | This document; includes the factory changelog | Reviewed GitHub pull request |
| PORTFOLIO.md | Live register: one row per project. The chief-of-staff view. | Each project's close routine (own row only); portfolio review (whole file) |
| LESSONS.md | Append-only friction log feeding factory improvements | Any project's retro routine |
| PROJECT-ARCHETYPES.md | How a project's architecture flexes with its goal | Reviewed GitHub pull request |
| PORTFOLIO-SPECIFICATION.md | Format and rules for PORTFOLIO.md | Reviewed GitHub pull request |
| MASTER-PROMPTS.md | Ready-to-copy prompts: quick task, intake, resume, delegate, review, retro, briefing | Reviewed GitHub pull request |
| SECURITY-AND-AUTHORITY.md | Autonomy levels, approval gates, secrets, and preservation rules | Reviewed GitHub pull request |
| MEMORY-CONTRACT.md | Which store is which: writers, readers, retention, authority, promotion path | Reviewed GitHub pull request |
| proposals/ | Quarantine. Proposed changes to stores the proposer may not write. Nothing here is in force. | A review pass (portfolio review, retro, audit) |

For ChatGPT local-project work, new projects live under `projects/` unless the user names another attached writable folder. Existing projects may remain elsewhere. Each project's PROJECT.md frontmatter carries the portfolio path, so a session inside any project can find its way back here. A scheduled or unattended task can work only where its sandbox has write access.

## Project maturity

Start every project at **MAKE IT WORK**. Advance only when use, stakes, or
the user's request justifies the overhead.

| Level | Approach | When |
|---|---|---|
| **MAKE IT WORK** (default) | Define outcome → build autonomously → the user tries it → iterate. Keep it useful, attractive, and simple; minimal notes and no routine proposal paperwork. | Every new project until real use shows more structure is needed. |
| **MAKE IT RELIABLE** | Add the tests, recovery, monitoring, permissions, and continuity practices this project needs. | the user starts depending on it or failures have meaningful cost. |
| **MAKE IT ROBUST** | Use formal architecture gates, threat modelling, audits, Pattern IDs, Outcome Scores, retrospectives, portfolio learning, and proposal machinery where useful. | High-stakes, valuable, shared, or externally governed systems. |

## Lifecycle of a project

1. **Define outcome.** Capture the intended result and material constraints; infer routine details.
2. **Build autonomously.** Make a usable version without asking implementation questions unless the choice materially affects functionality, cost, security, irreversible actions, or user experience.
3. **User tries it.** Show the user the result early.
4. **Iterate.** Improve it from his feedback.
5. **Harden later.** Add reliability or robust governance when maturity warrants it.

The existing intake, scaffold, resume, delegate, ingest, close, retro,
portfolio, and audit machinery remains available as optional tools. It is not
the default front door or recurring checklist at MAKE IT WORK.

## Fixed versus flexible

Four safeguards apply from day one: secrets/API keys outside the repo; writes
only in user-authorized project locations; human approval for destructive
actions, external communications, deployments, and spending; and reversible,
version-controlled changes. Detailed tracking and governance are optional
until a later maturity level calls for them.

Flexible per archetype (see PROJECT-ARCHETYPES.md): which folders exist, whether DECISIONS.md and RESOURCES.md are separate files or inline sections, plan granularity, default autonomy, default delegate mix, dashboard on or off.

At MAKE IT WORK, use only the files that help build and continue the project.
Detailed state, decision and resource records are added when continuity or a
higher maturity level needs them.

## How the factory self-corrects

Two loops, different speeds.

In-project, immediate: the conductor validates structure at resume and close, names what is broken instead of guessing, and repairs on approval. Feedback in conversation ("do it this way") lands in the project's INSTRUCTIONS.md so it sticks.

Factory-level, deliberate: LESSONS.md accumulates tagged entries (template | skill | prompt | archetype | process). During a portfolio review, when the same tag+problem appears twice or more, the chief-of-staff proposes a concrete change to the relevant factory file or the conductor skill. The human approves; the change is made once, centrally; the changelog below records it. Lessons never edit the factory automatically — a factory that rewrites itself unsupervised will drift faster than it improves.

From 2026-09-16, `MEMORY-CONTRACT.md` declares which agent may write which store, and local hook checks supplement those rules. Their coverage depends on the local installation and should not be treated as complete enforcement. A review pass that wants to change a shared operating rule prepares a GitHub pull request. After Renato merges it, Codex may refresh local runtime copies through the versioned sync procedure, preserving private additions and stopping on conflicts. The private overlay stays outside this repository.

## Where problems get logged

Two buckets, not one — introduced after a categorisation issue showed that
project-specific lessons and cross-project tool problems need different destinations.

- **Project-specific** — a finding about this project's own content, process, template,
  or prompts. Would it *not* recur in a different project using the same tools? Then
  it's project-specific. Stays inside that project: DECISIONS.md for a choice with a
  reason, LESSONS.md-via-retro or a mid-flight friction note for what cost time. This
  is unchanged from the rest of this document.
- **Generic / transversal** — a tool, connector, or platform bug that would recur in
  any project using the same tool/connector/synced folder. Test: "would this bug recur
  in a different project that used the same tool/connector/synced folder?" If yes, it
  does not belong in any single project's LESSONS.md, and it does not belong in this
  factory's LESSONS.md either — LESSONS.md is for patterns in how *this factory*
  operates (templates, the conductor skill, archetypes, prompts), not for tool bugs.
  Route it to the automation system's bug log configured by the private local
  overlay. This public pack intentionally omits the destination, monitoring-task
  names, and session metadata format. The private local overlay must supply those
  settings for generic bug routing to work. Use the configured session/project
  metadata field when filing a report.

Default behaviour for every session, scheduled or interactive: project-specific
improvements stay in the project's own files. Once the private local overlay is
configured, generic errors are logged to its configured destination for the
matching local monitoring process; until then, that routing cannot be relied on.
Don't wait for a repeated pattern before filing a generic bug; file it the same
session it's found (mirrors the mid-flight friction rule above, just routed to
the other log).

## Auditing the factory

The portfolio review routine (MASTER-PROMPTS.md, briefing prompt) is the audit instrument: cross-project status, stalled projects, claim overlaps, and open lesson patterns, in one pass. PORTFOLIO.md rows against project frontmatter answers "is the register honest"; LESSONS.md against the changelog answers "is the factory learning".

## Factory changelog

| Date | Change | Trigger |
|---|---|---|
| 2026-09-29 | Introduced Fast-Start Factory v2: MAKE IT WORK is default; MAKE IT RELIABLE and MAKE IT ROBUST retain advanced governance as optional stages. | Recurring feedback identified excess routine decisions and paperwork; advanced controls remain available. |
| 2026-09-28 | Added a quick-task lane for single-session work with no delegate or ongoing tracking; defined promotion to Light when continuity is needed. | Recurring setup overhead and service-use cost motivated a lightweight single-session lane. |
| 2026-09-17 | Activated the factory hook integration through the platform's native trust interface; its status was verified at the time. | The user explicitly requested the activation step. |
| 2026-09-17 | Added the factory-local Codex build crew, invocation skill, tested hook guardrails, plan validation and attempt evidence. Source and design changes: build-agents-v1/codex/README.md. Hook trust remains a user activation step. | A request for a native build workflow led to documented agent roles, guardrails, and validation steps. |
| 2026-09-16 | Memory contract added: MEMORY-CONTRACT.md declares each store's writers, readers, retention, authority and promotion path; `proposals/` added as a quarantine store; LESSONS.md entries gained Evidence / Scope / Review by; local hook checks were added to supplement the writer column. a related project-frontmatter issue was resolved in the same pass. | Review of external memory-design ideas identified a need to declare stores, add quarantine, and document write boundaries |
| 2026-08-10 | Added ChatGPT/Codex local-project instructions, Goal mode setup, scheduled-task guidance, and the missing security/authority source | A setup review identified a need for local-project and background-execution guidance |
| 2026-07-19 | Factory created: blueprint, portfolio, archetypes, master prompts, lessons | Initial design |
| 2026-08-06 | Added "Where problems get logged": generic/transversal tool bugs route to the automation system's BUG_LOG.md, not LESSONS.md; project-specific stays in the project | A categorisation review showed that a cross-project file-access failure had been recorded as a project-specific lesson |
