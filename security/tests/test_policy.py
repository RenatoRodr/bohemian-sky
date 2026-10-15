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
        self.a = self.root / "projects" / "a"
        self.b = self.root / "projects" / "b"
        self.a.mkdir(parents=True)
        self.b.mkdir(parents=True)
        self.identity = Identity("host:coordinator", "coordinator", trusted=True)
        self.builder = Identity("host:builder-1", "builder", "host:coordinator", trusted=True)
        self.cap = Capability(read_roots=(self.a, self.b), write_roots=(self.a,), cross_project=True, network_read=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_authorized_workspace_actions(self):
        for op in ("read", "create", "write", "rename"):
            self.assertTrue(authorize(self.builder, self.cap, op, self.a / "file.txt").allowed, op)
        self.assertTrue(authorize(self.builder, self.cap, "read", self.b / "readme").allowed)

    def test_outside_root_and_symlink_escape_denied(self):
        self.assertFalse(authorize(self.builder, self.cap, "write", self.b / "x").allowed)
        link = self.a / "escape"
        link.symlink_to(self.b, target_is_directory=True)
        self.assertEqual(authorize(self.builder, self.cap, "write", link / "x").reason, "outside_workspace")

    def test_explicit_cross_project_write_requires_both_roots(self):
        self.assertTrue(authorize(self.identity, Capability(write_roots=(self.a, self.b), cross_project=True),
                                  "write", self.a / "x", other_target=self.b / "y").allowed)
        self.assertEqual(authorize(self.identity, self.cap, "write", self.a / "x", other_target=self.b / "y").reason,
                         "cross_project_capability_required")

    def test_child_roots_are_narrowed_and_cannot_impersonate(self):
        requested = Capability(read_roots=(self.root,), write_roots=(self.root,), governance_write=True,
                               git_push=True, external_effects=frozenset({"github_write", "deploy"}))
        child = child_capability(self.cap, requested)
        self.assertEqual(child.read_roots, ())
        self.assertEqual(child.write_roots, ())
        self.assertFalse(child.governance_write or child.git_push or child.external_effects)
        self.assertEqual(authorize(Identity("builder", "coordinator", trusted=False), self.cap,
                                   "write", self.a / "x").reason, "untrusted_identity")

    def test_governance_resources_protected_at_any_depth(self):
        for path in (self.a / "PLAN.md", self.a / "control" / "RESOURCES.md"):
            self.assertEqual(authorize(self.builder, self.cap, "write", path).reason,
                             "governance_capability_required")

    def test_external_effects_are_separate_and_exact(self):
        for op in ("email_send", "github_write", "publish", "deploy", "paid_api"):
            self.assertEqual(authorize(self.identity, self.cap, op).reason, "approval_required", op)
        scoped = Capability(external_effects=frozenset({"email_send"}))
        self.assertTrue(authorize(self.identity, scoped, "email_send").allowed)
        self.assertFalse(authorize(self.identity, scoped, "deploy").allowed)

    def test_git_read_does_not_grant_push(self):
        self.assertTrue(authorize(self.builder, self.cap, "git_fetch").allowed)
        self.assertFalse(authorize(self.builder, self.cap, "git_push").allowed)
        grant = Capability(git_push=True, external_effects=frozenset({"git_push"}))
        self.assertTrue(authorize(self.identity, grant, "git_push").allowed)

    def test_secrets_escalation_and_nonfixture_delete_denied(self):
        for op in ("secret_read", "secret_write", "new_session_escalate", "identity_change", "exec_escalate"):
            self.assertFalse(authorize(self.identity, self.cap, op).allowed, op)
        self.assertEqual(authorize(self.builder, self.cap, "delete", self.a / "x").reason, "recovery_required")

    def test_launcher_fails_closed_without_host_services(self):
        with self.assertRaises(LauncherUnavailable):
            require_production_boundary(trusted_runtime=False, os_sandbox_verified=False, audit_recovery_broker=False)

    def test_hook_is_deny_only_and_catches_common_forms(self):
        self.assertEqual(classify("git push origin main"), "git_push")
        self.assertEqual(classify("git -C repo push origin main"), "git_push")
        self.assertEqual(classify("git -c push.default=current push origin main"), "git_push")
        self.assertEqual(classify("sendmail user@example.com"), "external_communication")
        self.assertEqual(classify("python3 build.py"), "")


if __name__ == "__main__":
    unittest.main()
