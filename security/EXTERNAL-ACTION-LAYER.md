# External action layer proposal

Status: **MOCK PROTOTYPE IMPLEMENTED; NOT ACTIVE**. The prototype has no
credentials, sockets, durable state, or live provider. It does not authorize
connector use, modify Codex settings, install software, or activate Security v3.

## Decision

Test Codex's built-in per-tool approval controls before building a separate
broker. Official Codex documentation exposes app-wide and per-tool approval
modes, an enabled/disabled switch, and a reviewer setting that can route
prompts to the user. A `prompt` mode on each mutating tool may provide the
needed gate in the Codex app surface. This behavior has not been verified in
the current connector runtime.

Keep the offline broker below as a policy fixture. Build a trusted broker only
if built-in approval controls fail to govern a connector call. Until a prompt
is observed and declining it is shown to prevent the provider action, keep
consequential service writes manual.

The relevant settings and approval flow are described in the [Codex
configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
and [Codex App Server documentation](https://learn.chatgpt.com/docs/app-server).

A Gmail draft was created through a connector without a visible human approval
pause in the observed Codex runtime. A `request_permissions` grant protected
local file access; it did not gate that connector action. Do not assume the
same approval behavior for other connectors or operations.

In the current assessment, a read-only fetch of the public `openai/codex`
README succeeded. The available tool inventory also includes GitHub, Drive,
Gmail, and Sites mutation tools. Their effective per-tool approval modes were
not visible: `codex app-server daemon version` failed because the expected
control socket was absent. No external mutation was attempted.

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
   the 17-test reference suite. The approval panel issues simulated receipts;
   it is not a human UI. The audit hash chain detects fixture mutation but is
   not durable or protected from a process that can edit its memory.
3. **Codex control configuration — DOCUMENTED, NOT APPLIED OR VERIFIED.**
   Inspect the effective `apps` config and exact connector tool IDs. Test a
   per-tool `approval_mode = "prompt"` with `approvals_reviewer = "user"` in a
   disposable task. The local CLI can read the base config, but this task has
   no connection to the active app-server `config/read` interface or an
   isolated connector test surface. Do not change live configuration as part
   of this design assessment.
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
