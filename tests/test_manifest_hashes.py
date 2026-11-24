"""Fail when a pinned file and package-manifest.json disagree.

Reuses the updater's own code (source_verifier._package_tree, refresh_core.digest)
so this check cannot disagree with the real verifier about the file set or about
how files are hashed. It checks both directions: a changed file with an old hash,
and a changed hash with an unchanged file. Lives in tests/, outside the updater's
PACKAGE_ROOTS, so adding it does not change the package tree.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "updater" / "refresh"))

import source_verifier  # noqa: E402
from refresh_core import digest  # noqa: E402


class ManifestHashes(unittest.TestCase):
    def test_pinned_files_match_manifest(self):
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, check=True,
                                stdout=subprocess.PIPE, text=True).stdout.strip()
        # Raises RefreshError if the manifest or the package file set is wrong.
        source_verifier._package_tree(REPO, commit)
        manifest = json.loads((REPO / "package-manifest.json").read_text())
        mismatches = []
        for section in ("files", "source_only"):
            for name, entry in manifest[section].items():
                actual = digest((REPO / name).read_bytes())
                if actual != entry["sha256"]:
                    mismatches.append(
                        f"{name}: file {actual}, package-manifest.json {entry['sha256']}")
        self.assertEqual(
            mismatches, [],
            "Update the hash in package-manifest.json in the same PR "
            "(sha256sum <file>). See README-refresh-rules.md.\n" + "\n".join(mismatches))


if __name__ == "__main__":
    unittest.main()
