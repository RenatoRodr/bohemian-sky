import subprocess
import tempfile
import unittest
from pathlib import Path


DIAGNOSTICS = Path(__file__).resolve().parents[1] / "diagnostics"
CLASSIFIER = DIAGNOSTICS / "classify_sandbox_startup.sh"


class SandboxDiagnosticClassificationTests(unittest.TestCase):
    def classify(self, stderr):
        with tempfile.TemporaryDirectory() as temp_dir:
            stderr_path = Path(temp_dir) / "stderr.txt"
            stderr_path.write_text(stderr)
            result = subprocess.run(
                [
                    "/bin/bash",
                    "-c",
                    'source "$1"; classify_sandbox_startup "$2"',
                    "bash",
                    str(CLASSIFIER),
                    str(stderr_path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()

    def test_explicit_sandbox_apply_error_is_host_failure(self):
        self.assertEqual(
            self.classify("sandbox_apply: Operation not permitted\n"),
            "HOST_FAILURE",
        )

    def test_broken_command_line_tools_is_host_failure(self):
        self.assertEqual(
            self.classify("xcrun: error: invalid active developer path\n"),
            "HOST_FAILURE",
        )

    def test_generic_permission_error_is_not_a_denial_pass(self):
        self.assertEqual(
            self.classify("sandbox-exec: execvp failed: Operation not permitted\n"),
            "STARTUP_PERMISSION_ERROR",
        )

    def test_other_pre_marker_error_is_startup_failure(self):
        self.assertEqual(self.classify("unexpected wrapper error\n"), "STARTUP_FAILURE")


if __name__ == "__main__":
    unittest.main()
