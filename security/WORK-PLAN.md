# Factory Simplification and Security v3 — work plan

Status: implementation in the isolated `design/factory-security-v3` checkout; no installation or activation.

1. **Inspection — DONE.** Read the shared operating rules, current v2 policy and launcher, active hook registration, and installed agent definitions. Existing v2 files/configuration remain read-only.
2. **Factory proposal — IN PROGRESS.** Clarify one-agent default and the coordinator, architect, builder, and independent auditor boundaries in `AGENTS.md`, `FACTORY-BLUEPRINT.md`, and versioned agent definitions.
3. **Security v3 design and prototype — NOT STARTED.** Specify workspace capabilities, trusted identity, host launcher and OS containment; implement a reviewable prototype under `security/` only.
4. **Regression evidence — NOT STARTED.** Exercise authorized file operations and denials for impersonation, privilege escalation, external impact, Git push, and protected governance.
5. **Staged migration — NOT STARTED.** Document backup, isolated test, human activation, post-install verification, and rollback. No activation in this task.
6. **Review package — NOT STARTED.** Review diffs, create separate local commits for Factory and Security changes, and report evidence. No remote push or PR publication without separate approval.

Acceptance: deliverables remain versioned and reviewable; local private configuration, installed hooks, live projects, and credentials are unchanged; regression tests pass; no claim of OS enforcement is made where only a prototype or policy exists.
