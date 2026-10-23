# External action layer proposal

Status: **MOCK PROTOTYPE IMPLEMENTED; NOT ACTIVE**. The prototype has no
credentials, sockets, durable state, or live provider. It does not authorize
connector use, modify Codex settings, install software, or activate Security v3.

## Decision

Test Codex's built-in per-tool approval controls before building a separate
broker. Current Codex documentation distinguishes command `approval_policy`
from app/MCP tool approval. App-wide and per-tool approval modes, enabled
switches, and a reviewer setting are available. Side-effecting app calls can
prompt; destructive calls require approval when the tool metadata marks them
destructive (unless marked read-only). A `writes` or `prompt` mode may provide
the needed gate for app tools, but it has not been verified in the current
connector runtime.

Keep the offline broker below as a policy fixture. Build a trusted broker only
if built-in approval controls fail to govern a connector call. Until a prompt
is observed and declining it is shown to prevent the provider action, keep
consequential service writes manual.

The relevant settings and approval flow are described in the [Codex
configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference),
[approval and security guide](https://learn.chatgpt.com/docs/agent-approvals-security),
and [App Server documentation](https://learn.chatgpt.com/docs/app-server).

A Gmail draft was created through a connector without a visible human approval
pause in the observed Codex runtime. A `request_permissions` grant protected
local file access; it did not gate that connector action. Do not assume the
same approval behavior for other connectors or operations.

In the current assessment, a read-only fetch of the public `openai/codex`
README succeeded. A standalone App Server inspection returned
`approval_policy: null`, `approvals_reviewer: null`, and
`managed_requirements: null`, and no `apps` table; it listed several apps as
enabled and callable. The null command-approval fields do not establish the
app-tool approval mode.
The enabled non-read-only tool inventory includes Drive file mutations,
GitHub issue/PR/repository and workflow actions, calendar changes, many Notion
mutations, and plugin-permission/uninstall controls. The recommendation is to
disable unneeded apps and writes, then configure a user-routed `writes` or
per-tool prompt mode for any required mutation and verify it in the live
surface. This is an inventory from
a separate App Server process, not the desktop's live thread state. It does
not establish which tools prompt, how a decline behaves, or whether the live
desktop has different settings. No connector mutation was attempted.

## Trust boundary

The broker is trusted only if Codex cannot change its executable, policy,
credentials, approval surface, or audit records. Keep those outside agent
writable roots. Store provider credentials in the macOS Keychain and expose
them only to the broker process. Never return credentials or reusable tokens
to Codex.

Codex documents separate approval controls for Apps and MCP calls. These
settings do not inherit the local command sandbox's network boundary. Each
connector must be governed at the app/tool layer; shell networking, browser
actions, other MCP servers, and other products have separate control paths.
An app setting is useful only if it applies to the live tool and declining a
prompt prevents its provider request. Prompts, role names, and request JSON
alone are not security controls.

## Request and approval contract

Codex submits a data-only request with:

- an allowlisted action name;
- provider account and exact target, such as repository and base branch;
- the complete user-visible content or change;
- a content digest, expiry, and one-use request identifier.

The broker rejects unknown fields, actions, targets, expired requests, and
requests that do not match local policy. It renders the exact action and
content in a user-controlled approval surface. Approval applies to that one
request only. Any edit to the target or content invalidates the approval. No
approval means no credential access and no provider call.

Start with one bounded action, such as creating a GitHub pull request in an
explicitly allowlisted repository. Do not include email sending, publishing,
deployment, permission changes, spending, or deletion in the first version.
Those actions need separate policy and approval checks if added later.

## Audit and recovery

Codex's optional OpenTelemetry can export tool-decision and tool-result events.
It is off by default and has not been enabled or tested here. It may support
operational traceability, but it is not evidence of a complete, tamper-resistant
record of local file activity or provider-side effects. Keep the external
trusted audit store requirement below for those guarantees.

For every request, record the request digest, action, target, approver,
decision, time, provider result identifier, and final status. Do not log
credentials or unnecessary private content. Agents must not be able to edit or
delete the audit record. A denied, expired, malformed, or failed request must
produce no external effect.

Provider success and local timeout can be ambiguous. Use a provider idempotency
key when available; otherwise check the target for an existing result before
retrying. Record `execution`, `denial`, and `host/provider failure` as distinct
outcomes. Recovery is a new separately approved action; never imply that a
completed external action can always be undone.

## Build and verification order

1. **Design — DONE.** This document defines the approval and fallback
   requirements.
2. **Mock prototype — DONE.** `mock_action_broker.py` implements one GitHub PR
   request against an in-memory provider. Seven broker tests passed as part of
   the 21-test reference suite. The approval panel issues simulated receipts;
   it is not a human UI. The audit hash chain detects fixture mutation but is
   not durable or protected from a process that can edit its memory.
3. **Standalone settings and tool inventory — INSPECTED; LIVE POLICY NOT VERIFIED.**
   The standalone `config/read` response showed null top-level approval fields,
   null managed requirements, and no app-specific approval overrides. The
   runtime inventory showed a broad enabled write surface. This does not expose
   the desktop's live in-memory state or prove that a particular tool prompts.
   A future test would need the exact target tool ID and a disposable task. Do
   not change live configuration as part of this design assessment.
4. **Connector approval test — NOT VERIFIED.** A previous reversible Gmail
   create-draft call had no visible approval pause; no email was sent. It did
   not test a declined call or prove what the active per-tool policy was. In an
   isolated connector setup, confirm that the prompt shows the account and
   exact action, decline, then verify no provider-side result. Do not test send,
   publish, deploy, spend, or production mutation.
5. **Broker fallback — CONDITIONAL.** If Codex's supported settings do not
   mediate the current connector calls, keep them manual. Consider a trusted
   broker only if a supported configuration can also prevent direct connector
   and alternate-tool calls.
6. **Expansion — NOT APPROVED.** Add other providers or operations only after
   reviewing their credential scopes, exact approval display, logs, denial
   behavior, and recovery path.

## Acceptance criteria

- A user sees the exact account, target, and content before approval.
- Approval is single-use and bound to the request digest, target, and expiry.
- Rejection, missing approval, tampering, expiry, and unknown action produce no
  provider request.
- Credentials never enter model context, request files, environment variables,
  or logs.
- Each consequential connector tool requires a user-routed prompt, and a
  decline prevents the provider call.
- Logs distinguish approval, execution, denial, and provider/host failure and
  cannot be edited by the requesting agent.
- Tests cover permitted and prohibited behavior before any live service test.

The prototype tests request validation, target allowlisting, missing and
rejected approval, digest mismatch after review, expiration, one-use request
IDs, mock provider failure, and audit-chain tampering. It proves only the
behavior of this Python fixture. It does not prove a trusted identity for the
approver, a user-visible confirmation prompt, credential isolation, durable
audit storage, operating-system containment, or prevention of direct connector
calls.

Until these criteria are verified, human approval for consequential connector
actions remains **UNTESTED** and those actions stay manual.
