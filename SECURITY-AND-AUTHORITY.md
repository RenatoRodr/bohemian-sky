# Security and authority

> Shared operating rule. Changes go through a reviewed GitHub pull request. See `MEMORY-CONTRACT.md`.

The four safeguards below apply from day one. Detailed autonomy levels and
preservation procedures remain available for MAKE IT RELIABLE and MAKE IT
ROBUST projects.

## Day-one safeguards

1. Keep secrets and API keys outside the repository.
2. Write only in user-authorized project locations.
3. Get human approval before destructive actions, external communications,
   deployments, or spending.
4. Keep changes reversible and under version control where available.

Do not ask the user implementation questions unless a choice materially affects
functionality, cost, security, irreversible actions, or user experience.

The detailed controls below are maturity-stage tools, not extra default
paperwork for MAKE IT WORK.

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
- making a paid API call;
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
