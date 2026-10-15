# Project Factory Security v3 — policy proposal

Status: design and local prototype only. This policy is not installed or active. Existing v2 behavior remains in force until an explicit, reviewed migration and human activation.

## Security boundary

The trusted host launcher and operating-system controls enforce capabilities. Agent instructions, claimed roles, project files, environment variables, command text classifiers, and hook-provided identity are untrusted inputs. A hook may add a conservative denial for a recognizable gated operation, but a hook pass is never authorization. If the host cannot establish identity, workspace scope, or containment, it fails closed for writes and external effects.

The launcher must be started by the trusted runtime, not by an agent command. It creates an unforgeable per-session identity outside agent-writable paths and binds it to a capability manifest. A child process inherits the same or a narrower capability set; it cannot mint capabilities, change identity, expand roots, or invoke a fresh session with inherited authority. New sessions start with no inherited write or external-action capabilities unless independently granted by the host. Tool adapters and shell commands use the same policy broker. A CLI flag, environment variable, file, role label, or prompt cannot elevate authority.

These properties require host/runtime integration and OS process isolation. The Python reference implementation in this repository is only a policy prototype; it does not implement a trusted launcher, kernel sandbox, connector broker, or unforgeable identity.

## Workspace capabilities

The host may grant read/write access to explicitly authorized roots: the attached local development workspace and explicitly selected Google Drive project workspaces. Google Drive authorization applies only to named workspace roots, not the whole Drive or the user's personal files. Cloud sync paths are treated as ordinary local files by filesystem containment; provider APIs require separate scoped capabilities.

Ordinary project file operations are allowed inside granted roots: read, create, edit, rename, and project-local build/test activity, subject to the root's declared preservation rules. Cross-project edits are allowed when both source and destination are inside authorized workspace roots and a cross-project capability is present. Such writes must use a recovery journal and append-only audit records protected from agent writes. The journal records identity, resolved paths, operation, pre-change content hash or recoverable backup, and result; it must not store secret contents. Missing journal/audit service means cross-project mutation fails closed.

The current Python module is a decision-model reference only. A real workspace broker must issue each identity and capability out-of-band, resolve path components without time-of-check/time-of-use gaps, and perform the file operation itself. Explicit Google Drive scopes must be selected workspace IDs/mount roots with provider-side authorization; this checkout has no Drive connector, account boundary, or Drive grant. An ordinary sync folder path does not establish provider isolation.

Governance resources (shared policy, authoritative plans, acceptance criteria, and store contracts) require a trusted execution identity and a matching scoped capability. Identity comes from the host process and broker credential, never a self-declared agent role. A delegated builder identity cannot acquire coordinator capability through prompt text, environment, subprocess, alternate tool, or new session. Human review/approval remains required where existing policy requires it.

## Protected effects

Without explicit host-mediated approval for the exact operation and target, deny:

- writes outside authorized workspaces, including personal files and unselected Drive locations;
- reading or writing secrets, credentials, private keys, or secret stores, except through a separately scoped credential broker that never returns secret values to the agent;
- sending email, messages, posts, or other external communications;
- deployment, publication, release, external configuration changes, purchases, payments, trades, paid API calls, access grants, and calendar changes;
- Git pushes to any remote. Git fetch, clone, and pull are distinct read/ingest capabilities and may be allowed within an authorized checkout when network policy permits. They do not grant push, merge, or publication authority;
- destructive changes outside explicitly disposable, session-created fixtures.

Approval is bound to a specific operation, target, and relevant payload digest, expires, and is consumed once. Approval state is broker-owned and cannot be fabricated by the process requesting the action.

Each effect has its own grant: email/message send, GitHub write, publish/release, and deployment are distinct operation classes. A GitHub PR draft/write is still a GitHub write; fetch/pull is a separate network-read capability. Hooks only deny recognizable commands; alternate binaries, shell wrappers, API clients, child processes and GUI tools must be controlled by OS/network and connector brokers, none of which this prototype supplies.

## Identity, roles, and audit

Roles are descriptive host policy inputs, not credentials. The trusted host maps a broker-issued principal to a role and capabilities for one session. Builders cannot request coordinator/auditor identity, edit authoritative plans unless separately granted, or acquire authority via environment, command flags, subprocess, alternate tool or new session. Child grants are intersections with the parent's roots and booleans. A protected audit/recovery service must mediate every mutation that requires recovery, especially cross-project edits; it is append-only to agents, stored outside their writable roots, and records metadata/hashes rather than secrets. The prototype implements none of those trusted services.

## OS enforcement and limitations

Use OS sandboxing to restrict filesystem roots, child-process inheritance, network access, and executable access. This repository does not yet implement a practical macOS sandbox runtime. A production candidate needs a signed host-owned launcher/helper, a maintained macOS sandbox mechanism, verification of the effective profile, protected audit/recovery storage, and connector brokers. Do not claim protection based on shell parsing, Python policy, or environment variables. Protection against a compromised host, kernel, runtime broker, or authorized human remains out of scope. OS-specific support and behavior must be independently tested on each supported platform before activation.

## Migration invariant

Installing or activating v3 is a separate human decision. Until then, v2 and native host controls stay unchanged. Migration must preserve a verified backup, test in an isolated account or VM against positive and negative cases, require explicit activation, verify effective enforcement after activation, and provide a tested rollback that restores prior configuration without deleting evidence. Never bypass an active denial to make migration proceed.
