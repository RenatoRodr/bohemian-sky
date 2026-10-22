import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mock_action_broker import (
    ACTION,
    MockActionBroker,
    MockAuditLog,
    MockPullRequestProvider,
    PreparedAction,
    SimulatedApprovalPanel,
)


class MockActionBrokerTests(unittest.TestCase):
    def setUp(self):
        self.now = 1_800_000_000
        self.provider = MockPullRequestProvider()
        self.audit = MockAuditLog()
        self.broker = MockActionBroker(
            self.provider, now=lambda: self.now, audit=self.audit
        )
        self.panel = SimulatedApprovalPanel()

    def request(self, request_id="req-1", **overrides):
        result = {
            "request_id": request_id,
            "action": ACTION,
            "account": "fixture-account",
            "owner": "example",
            "repository": "sandbox",
            "head": "feature/demo",
            "base": "main",
            "title": "Add demo change",
            "body": "A mock-only request.",
            "expires_at": self.now + 60,
        }
        result.update(overrides)
        return result

    def approved_receipt(self, prepared, approved=True):
        return self.panel.issue(
            prepared, approver="fixture-user", approved=approved, now=self.now
        )

    def test_approved_action_creates_only_in_memory_mock_result(self):
        prepared = self.broker.prepare(self.request())
        self.assertIsInstance(prepared, PreparedAction)
        receipt = self.approved_receipt(prepared)

        result = self.broker.execute(prepared, receipt)

        self.assertEqual((result.outcome, result.reason), ("execution", "created"))
        self.assertEqual(len(self.provider.created), 1)
        self.assertEqual(self.provider.created[0]["repository"], "sandbox")
        self.assertEqual(self.panel.last_preview["title"], "Add demo change")
        self.assertEqual(self.panel.last_preview["body"], "A mock-only request.")
        self.assertTrue(self.audit.verify())

    def test_missing_or_rejected_approval_has_no_provider_effect(self):
        prepared = self.broker.prepare(self.request())
        missing = self.broker.execute(prepared, None)
        self.assertEqual((missing.outcome, missing.reason), ("denial", "approval_missing"))
        self.assertEqual(self.provider.created, [])

        prepared = self.broker.prepare(self.request("req-2"))
        receipt = self.approved_receipt(prepared, approved=False)
        rejected = self.broker.execute(prepared, receipt)
        self.assertEqual((rejected.outcome, rejected.reason), ("denial", "approval_rejected"))
        self.assertEqual(self.provider.created, [])

    def test_request_changes_after_preview_invalidate_receipt(self):
        prepared = self.broker.prepare(self.request())
        receipt = self.approved_receipt(prepared)
        altered_request = replace(prepared.request, title="Different title")
        altered = PreparedAction(request=altered_request, digest=prepared.digest)

        result = self.broker.execute(altered, receipt)

        self.assertEqual((result.outcome, result.reason), ("denial", "approval_invalid"))
        self.assertEqual(self.provider.created, [])

    def test_wrong_receipt_digest_and_expiry_are_denied(self):
        prepared = self.broker.prepare(self.request())
        good = self.approved_receipt(prepared)
        wrong_digest = replace(good, digest="0" * 64)
        self.assertEqual(self.broker.execute(prepared, wrong_digest).reason, "approval_invalid")

        prepared = self.broker.prepare(self.request("req-2"))
        receipt = self.approved_receipt(prepared)
        self.now = prepared.request.expires_at
        self.assertEqual(self.broker.execute(prepared, receipt).reason, "request_expired")
        self.assertEqual(self.provider.created, [])

    def test_unknown_fields_bad_schema_and_disallowed_target_are_denied(self):
        malformed = self.request()
        malformed["unreviewed"] = "extra"
        self.assertEqual(self.broker.prepare(malformed).reason, "invalid_schema")
        self.assertEqual(self.broker.prepare(
            self.request("req-unknown", action="github.delete_repository")
        ).reason, "unknown_action")
        self.assertEqual(self.broker.prepare(self.request("req-2", owner="attacker")).reason,
                         "target_not_allowed")
        self.assertEqual(self.provider.created, [])

    def test_request_id_is_one_use_and_provider_failure_is_distinct(self):
        prepared = self.broker.prepare(self.request())
        executed = self.broker.execute(prepared, self.approved_receipt(prepared))
        self.assertEqual(executed.outcome, "execution")
        repeated = self.broker.execute(prepared, self.approved_receipt(prepared))
        self.assertEqual((repeated.outcome, repeated.reason), ("denial", "duplicate_request"))
        self.assertEqual(len(self.provider.created), 1)

        failing_provider = MockPullRequestProvider(fail_next=True)
        failing_broker = MockActionBroker(failing_provider, now=lambda: self.now)
        second = failing_broker.prepare(self.request("req-fail"))
        failed = failing_broker.execute(second, self.panel.issue(
            second, approver="fixture-user", approved=True, now=self.now
        ))
        self.assertEqual((failed.outcome, failed.reason),
                         ("host_failure", "mock_provider_failure"))
        self.assertEqual(failing_provider.created, [])

    def test_audit_chain_detects_record_tampering(self):
        prepared = self.broker.prepare(self.request())
        self.broker.execute(prepared, self.approved_receipt(prepared, approved=False))
        self.assertTrue(self.audit.verify())
        self.audit._events[0] = replace(self.audit._events[0], outcome="execution")
        self.assertFalse(self.audit.verify())


if __name__ == "__main__":
    unittest.main()
