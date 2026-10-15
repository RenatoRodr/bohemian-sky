# Security v3 proposal

This directory contains an unactivated policy and prototype. It does not replace v2, alter installed hooks, or enforce OS isolation. `launcher.py` deliberately refuses to launch because this repository cannot establish trusted runtime identity, a verified OS sandbox, or protected audit/recovery storage.

- `POLICY.md` defines intended capabilities and enforcement boundaries.
- `policy.py` is a testable authorization model.
- `hooks.py` illustrates narrow denial-only classification; an empty result is not authorization.
- `agent-proposals/` contains replacement role definitions. Current installed role files remain untouched.
- `migrate.sh` and `rollback.sh` print the required manual stages and do not modify configuration.
- `tests/` covers policy-level positive and negative cases. They cannot prove OS or connector containment.
- `WORK-PLAN.md` records task status.

## Current inspection findings

The live runtime registers pre-tool-use and session-start hooks under `~/.codex/hooks.json`; hook programs and v2 policy are under private local paths. v2 labels itself best effort and defers opaque shell forms to native controls. These private configurations and source files were inspected read-only and are not copied here. The repository itself had no versioned agent definitions; the local definitions were inspected read-only and generalized into review proposals.

## Explicit scope

Authorized development target: this repository checkout. Google Drive project workspaces are proposed as an explicit future capability, not accessed or modified by this change. No credentials, personal content, absolute private paths, active hook configuration, installation, activation, or Git push are included.
