# Project factory — shared rules

This repository's `main` branch is the canonical source for the shared,
manual-only factory rules. Private operating data and local
tool configuration remain in the Google Drive Project factory. A branch or
pull request does not replace the active `main` rules.

## Included

Eight cleaned copies of the current manual-only rule files, with their original
filenames:

- `AGENTS.md`
- `SECURITY-AND-AUTHORITY.md`
- `FACTORY-BLUEPRINT.md`
- `PROJECT-ARCHETYPES.md`
- `PORTFOLIO-SPECIFICATION.md`
- `MASTER-PROMPTS.md`
- `CHATGPT-SETUP.md`
- `MEMORY-CONTRACT.md`

## Local setup and exclusions

Personal names, identifiable project examples, absolute local paths, scheduled
task names, and personal changelog triggers have been generalized. Tool and
brand defaults remain as in the source. The blueprint's generic bug-report
routing now points to a private local overlay; that overlay must supply the
actual bug-log destination, monitoring task names, and session metadata format
for this routing to work.

This pack does not include the live `PORTFOLIO.md`, `LESSONS.md`, proposals,
project files, hook source, installed tool configuration, or historical
archives. `MEMORY-CONTRACT.md` keeps its seven-column `## The stores` table and
its current writer rules. The current source table does not authorize an
optional classification-telemetry store, so the pack does not add one or enable
that telemetry. The public copy omits local hook installation,
bypass, and weakness instructions; consult the private local enforcement
documentation for the actual configured controls and their limits.

The `factory-build` skill, `build-agents-v1/codex/README.md`, and `.codex/agents/`
mentioned in `AGENTS.md` are local build-crew components. Install them from the
private factory before using that workflow. The public rules alone do not
provide the skill or agents.

## Change control

Review changes to the shared rules in a pull request before merging `main`.
Keep private overlay material in Drive. Codex may refresh local runtime copies
from a reviewed merge using a versioned procedure that preserves private text
and stops on conflicts. The local Git checkout supplies the last verified copy
when offline. A repository merge does not install hooks or change private
configuration by itself.
