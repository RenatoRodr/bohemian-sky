import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("safe_export", Path(__file__).with_name("safe_export.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SafeExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / "native.jsonl"
        self.source.write_text(json.dumps({"type": "response_item", "payload": {
            "password": "synthetic-secret", "text": "hello bearer fakeToken123456789",
            "tool": {"name": "exec", "arguments": "safe action"}}}) + "\n")
        self.target = module.ArchiveTarget("synthetic-folder", "owner@example.test", Path(self.temp.name) / "mounted")

    def metadata(self):
        return {"id": self.target.folder_id, "mime_type": "application/vnd.google-apps.folder",
                "account_email": self.target.owner_email, "checked_at_epoch": time.time(),
                "permissions": [{"type": "user", "role": "owner", "emailAddress": self.target.owner_email}]}

    def review(self):
        _, receipt = module.prepare(self.source)
        return {"reviewer": self.target.owner_email, "decision": "APPROVED",
                "source_sha256": receipt["source_sha256"],
                "output_sha256": receipt["output_sha256"]}

    def test_redacts_and_preserves_record_structure(self):
        payload, receipt = module.prepare(self.source)
        item = json.loads(payload)
        self.assertEqual(item["type"], "response_item")
        self.assertEqual(item["payload"]["tool"]["name"], "exec")
        self.assertEqual(item["payload"]["password"], module.REDACTED)
        self.assertNotIn(b"fakeToken123456789", payload)
        self.assertTrue(receipt["review_required"])
        self.assertEqual(set(Path(self.temp.name).iterdir()), {self.source})

    def test_quoted_secret_with_spaces_is_removed_entirely(self):
        self.source.write_text(json.dumps({"text": "password=\"synthetic two words\""}) + "\n")
        payload, _ = module.prepare(self.source)
        self.assertNotIn(b"synthetic", payload)
        self.assertNotIn(b"two words", payload)

    def test_no_write_without_exact_review(self):
        writes = []
        with self.assertRaises(module.CaptureError):
            module.export(self.source, self.target, {}, self.metadata, lambda *args: writes.append(args))
        self.assertEqual(writes, [])

    def test_no_write_when_acl_or_freshness_fails(self):
        writes = []
        for change in ({"permissions": []}, {"checked_at_epoch": time.time() - 31},
                       {"id": "other-folder"}):
            with self.subTest(change=change), self.assertRaises(module.CaptureError):
                module.export(self.source, self.target, self.review(),
                              lambda: {**self.metadata(), **change},
                              lambda *args: writes.append(args))
        self.assertEqual(writes, [])

    def test_direct_write_after_review_and_fresh_check(self):
        calls = []
        def write(folder, payload):
            calls.append((folder, json.loads(payload)))
            return {"id": "synthetic-file", "parent_id": folder}
        result = module.export(self.source, self.target, self.review(), self.metadata, write)
        self.assertEqual(result["status"], "REMOTE_WRITTEN")
        self.assertEqual(len(calls), 1)
        self.assertEqual(set(Path(self.temp.name).iterdir()), {self.source})

    def test_rejects_symlink_and_malformed_source(self):
        symlink = Path(self.temp.name) / "link"
        symlink.symlink_to(self.source)
        with self.assertRaises(OSError):
            module.prepare(symlink)
        self.source.write_text("not json\n")
        with self.assertRaises(module.CaptureError):
            module.prepare(self.source)

    @unittest.skipUnless(sys.platform == "darwin", "macOS Drive mount only")
    def test_mounted_writer_creates_only_in_verified_folder(self):
        mount = Path(self.temp.name) / "mounted"
        mount.mkdir(mode=0o700)
        subprocess.run(["xattr", "-w", "com.google.drivefs.item-id#S", self.target.folder_id, str(mount)], check=True)
        name = "project-factory-chat--synthetic.jsonl"
        result = module.write_mounted(self.target.folder_id, b'{"synthetic":true}\n', name, self.target)
        self.assertTrue(result["local_written"])
        self.assertEqual((mount / name).read_bytes(), b'{"synthetic":true}\n')
        self.assertEqual((mount / name).stat().st_mode & 0o777, 0o600)
        with self.assertRaises(FileExistsError):
            module.write_mounted(self.target.folder_id, b"replacement", name, self.target)
        self.assertEqual((mount / name).read_bytes(), b'{"synthetic":true}\n')

    @unittest.skipUnless(sys.platform == "darwin", "macOS Drive mount only")
    def test_mounted_writer_rejects_wrong_identity(self):
        mount = Path(self.temp.name) / "mounted"
        mount.mkdir(mode=0o700)
        subprocess.run(["xattr", "-w", "com.google.drivefs.item-id#S", "wrong", str(mount)], check=True)
        with self.assertRaises(module.CaptureError):
            module.write_mounted(self.target.folder_id, b"synthetic", "project-factory-chat--synthetic.jsonl", self.target)
        self.assertEqual(list(mount.iterdir()), [])

    def test_reviewed_prefix_stays_stable_when_new_record_arrives(self):
        payload, receipt = module.prepare(self.source, record_limit=1)
        with self.source.open("a") as stream:
            stream.write('{"type":"later"}\n')
        again, later = module.prepare(self.source, record_limit=1)
        self.assertEqual(again, payload)
        self.assertEqual(later["source_sha256"], receipt["source_sha256"])
        self.assertTrue(later["source_is_prefix"])
        self.assertEqual(module.prepare(self.source)[1]["records"], 2)

    def test_changed_reviewed_bytes_block_write(self):
        review = self.review()
        self.source.write_text('{"type":"changed"}\n')
        calls = []
        with self.assertRaises(module.CaptureError):
            module.export(self.source, self.target, review, self.metadata,
                          lambda *args: calls.append(args))
        self.assertEqual(calls, [])

    @unittest.skipUnless(sys.platform == "darwin", "macOS Drive mount only")
    def test_mounted_writer_rejects_open_permissions(self):
        mount = Path(self.temp.name) / "mounted"
        mount.mkdir(mode=0o700)
        subprocess.run(["xattr", "-w", "com.google.drivefs.item-id#S", self.target.folder_id, str(mount)], check=True)
        mount.chmod(0o755)
        with self.assertRaises(module.CaptureError):
            module.write_mounted(self.target.folder_id, b"synthetic", "project-factory-chat--synthetic.jsonl", self.target)
        self.assertEqual(list(mount.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
