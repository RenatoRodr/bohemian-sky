---
goal: "Replace with an observable result"
root: "Replace with the absolute active project directory"
---

# Goal

State the result and independent verification. Include binding decisions and
constraints or point to the exact control-file entries.

# Steps

## S1 — Produce the first reviewable result

- **status:** pending
- **depends_on:** none
- **write_scope:**
  - `work/example.txt`
- **read_manifest:**
  - `control/DECISIONS.md`
- **acceptance:** Replace with a command or explicit yes/no criteria that test the result.
- **output:** Replace with the deliverable and evidence.
- **gated:** no
- **milestone:** first review

Instructions specific to this step belong here.

# Gated actions

Record the concrete action, its prerequisites, and existing or needed approval.
Represent prerequisite gates as steps with `gated: yes`; downstream work depends
on those IDs. Never imply they already ran. Gated actions are not builder work.

# Contract rules

IDs are stable S<number> values. Status is pending, in_progress, done, blocked,
failed, or dropped. A dropped step needs a recorded decision. Dependencies must
exist and form an acyclic graph. A milestone must occur before the last ungated
step when there are more than three. The coordinator also performs a final audit.

Scopes and manifests use project-relative paths without `..` or symlink escapes.
Scopes are exact files or directories ending in `/**`. No other glob syntax.
Separate files can still share build outputs, lockfiles, or runtime resources;
disjoint scopes alone do not justify parallel builders in a shared directory.
