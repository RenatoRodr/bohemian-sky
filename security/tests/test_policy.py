import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from policy import Capability, Identity, authorize, child_capability
from launcher import LauncherUnavailable, require_production_boundary
from hooks import classify


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.project_a = self.root / "projects" / "a"
        self.project_b = self.root / "projects" / "b"
        self.project_a.mkdir(parents=True)
        self.project_b.mkdir(parents=True)
        self.identity = Identity("runtime:coordinator", trusted=True)
        self.builder = Identity("runtime:builder", trusted=True, parent_principal="runtime:coordinator")
        self.cap = Capability(
            read_roots=(self.project_a, self.project_b),
            write_roots=(self.project_a, self.project_b),
            cross_project=True,
            network_read=True,
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_authorized_project_file_operations(self):
        self.assertTrue(authorize(self.identity, self.cap, "create", self.project_a / "new.py").allowed)
        self.assertTrue(authorize(self.identity, self.cap, "write", self.project_a / "src.py").allowed)
        self.assertTrue(authorize(self.identity, self.cap, "read", self.project_b / "README.md").allowed)

    def test_explicit_cross_project_edit(self):
        self.assertTrue(authorize(self.identity, self.cap, "write", self.project_a / "x", other_target=self.project_b / "y").allowed)
        narrow = Capability(write_roots=(self.project_a,))
        self.assertEqual(authorize(self.identity, narrow, "write", self.project_a / "x", other_target=self.project_b / "y").reason, "cross_project_capability_required")

    def test_untrusted_identity_and_subagent_role_impersonation(self):
        fake_role = Identity("factory_coordinator", trusted=False, parent_principal="runtime:builder")
        self.assertEqual(authorize(fake_role, self.cap, "write", self.project_a / "x").reason, "untrusted_identity")

    def test_child_process_cannot_expand_capabilities(self):
        requested = Capability(write_roots=(self.root,), governance_write=True, git_push=True,
                               external_effects=frozenset({"email_send"}))
        narrowed = child_capability(self.cap, requested)
        self.assertFalse(narrowed.governance_write)
        self.assertFalse(narrowed.git_push)
        self.assertFalse(narrowed.external_effects)
        self.assertEqual(narrowed.write_roots, ())

    def test_governance_protected(self):
        target = self.project_a / "PLAN.md"
        self.assertEqual(authorize(self.identity, self.cap, "write", target).reason, "governance_capability_required")
        privileged = Capability(write_roots=(self.project_a,), governance_write=True)
        self.assertTrue(authorize(self.identity, privileged, "write", target).allowed)

    def test_external_personal_and_secret_operations_denied(self):
        self.assertEqual(authorize(self.identity, self.cap, "write", self.root.parent / "private.txt").reason, "outside_workspace")
        self.assertEqual(authorize(self.identity, self.cap, "secret_read").reason, "broker_only_or_denied")
        for operation in ("email_send", "deploy", "publish", "paid_api", "calendar_change"):
            self.assertEqual(authorize(self.identity, self.cap, operation).reason, "approval_required")

    def test_git_fetch_distinct_from_push(self):
        self.assertTrue(authorize(self.identity, self.cap, "git_fetch").allowed)
        self.assertEqual(authorize(self.identity, self.cap, "git_push").reason, "git_push_capability_required")

    def test_deletion_requires_recovery_scope(self):
        self.assertEqual(authorize(self.identity, self.cap, "delete", self.project_a / "x").reason, "recovery_required")
        self.assertTrue(authorize(self.identity, self.cap, "delete", self.project_a / "tmp", session_created_fixture=True).allowed)

    def test_launcher_refuses_unverified_host_boundary(self):
        with self.assertRaises(LauncherUnavailable):
            require_production_boundary(trusted_runtime=False, os_sandbox_verified=False, audit_recovery_broker=False)

    def test_hooks_deny_known_external_impact_and_abstain_otherwise(self):
        self.assertEqual(classify("git push origin main"), "git_push")
        self.assertEqual(classify("sendmail user@example.com"), "external_communication")
        self.assertEqual(classify("python3 build.py"), "")


if __name__ == "__main__":
    unittest.main()
