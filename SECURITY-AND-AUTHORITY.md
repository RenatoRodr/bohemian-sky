# Security and authority

> Shared operating rule. Changes go through a reviewed GitHub pull request. See `MEMORY-CONTRACT.md`.

The four safeguards below apply from day one. Detailed autonomy levels and
preservation procedures remain available for MAKE IT RELIABLE and MAKE IT
ROBUST projects.

## Day-one safeguards

1. Keep secrets and API keys outside the repository.
2. Write only in user-authorized project locations.
3. Get human approval before destructive actions, external communications,
   deployments, or spending, except ordinary Jev API use covered by the
   standing authorization in `MEMORY-CONTRACT.md`.
4. Keep changes reversible and under version control where available.

Do not ask the user implementation questions unless a choice materially affects
functionality, cost, security, irreversible actions, or user experience.

The detailed controls below are maturity-stage tools, not extra default
paperwork for MAKE IT WORK.

## Codex execution and external actions

Use Codex's `workspace-write` sandbox for local commands. Keep writable roots
limited to the active project folders. Do not add the home directory or the
Factory parent. Commands may read files outside the workspace, so this mode
limits writes but does not provide read confidentiality. Keep command network
access off unless a task needs it. Read-only research does not authorize a
service write.

The local command sandbox does not govern app connectors or MCP tools. Codex
can ask for approval when an app tool declares side effects. A destructive
tool marked as destructive requires approval unless it is also marked as
read. Connector account permissions remain separate. Get human approval for
the exact target and operation before sending communications, deploying,
spending money outside the standing Jev authorization, changing credentials
or permissions, or mutating cloud data.
An ordinary Jev call through an already available route is covered by the
standing authorization; installing a new integration or changing an existing
automation remains a deployment or configuration change under its normal gate.
Use a human reviewer, not automatic review. If the available tool does not
show a clear approval gate, leave that action disabled or have the user
perform it.

Routine local Git work inside an authorized project may proceed without
repeated approval. A push to a shared remote remains an external write and
needs approval. Keep Factory hooks for governance rules the native sandbox
does not cover. Do not use them as a second filesystem sandbox, and do not
remove a live hook control until an agent-session test with that hook active
proves the replacement and a rollback is ready.

See [Codex approvals and security](https://learn.chatgpt.com/docs/agent-approvals-security)
for current sandbox and app-action approval behavior.

## Development fixture scope

Disposable development fixtures

Cleanup of files created specifically for testing under an explicitly designated
temporary work directory is routine reversible development housekeeping, not
permission to delete source material, user inputs, review records, shipped
outputs, or production data. The agent must verify the target remains inside
the authorised project before cleanup. Unknown or ambiguous deletion targets
still require review. Do not treat a text-matching hook as an operating-system
security boundary.

## Autonomy levels

| Level | Work allowed without asking |
|---|---|
| 0 | Read-only inspection. Confirm every write first. |
| 1 | Read the project and update `control/` files and the generated dashboard. |
| 2 | Level 1, plus create and edit material in `work/`, `handoffs/`, `outputs/`, and `archive/`. |

Level 2 is the factory default. It authorizes work inside the active managed
project. It does not authorize external or irreversible action.

## Additional gates for MAKE IT ROBUST

Obtain explicit approval before:

- sending email, messages, posts, reviewer replies, or any other external
  communication;
- changing a calendar;
- deploying or changing an external system;
- making a paid API call outside the standing Jev authorization in
  `MEMORY-CONTRACT.md`;
- writing outside the active managed-project folder or the factory files that
  its documented procedure requires;
- pushing to a shared Git remote;
- granting a tool, person, or service new access;
- deleting a material file.

When an output needs revision, create a new version and archive the superseded
one. Do not delete the old version.

## Secrets

Credentials, tokens, API keys, passwords, private keys, and recovery codes must
not appear anywhere in a project tree, including control files, prompts, code,
logs, and `.env` files. Store them in the operating-system keychain, 1Password,
or the service's authentication store. `RESOURCES.md` may name that location but
must not contain the secret.

If a secret is written to a synced or versioned file, treat it as exposed and
rotate it. Removing the line is insufficient because history may retain it.

## Preservation rules

- `inputs/` and `reviews/` are write-once. A correction is a new file.
- Sent or shipped files in `outputs/` are frozen. A revision is a new file.
- Superseded authoritative material moves to `archive/` with an ISO-date
  prefix. The authority flag moves in `control/RESOURCES.md` in the same edit.
- Completed plan steps and superseded decisions remain visible.
- A non-empty `handoffs/in/` means returned work still needs ingestion.
