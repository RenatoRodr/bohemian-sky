import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import session_capture  # noqa: E402
import usage  # noqa: E402

START = datetime(2026, 10, 13, 10, 0, tzinfo=timezone.utc)
END = datetime(2026, 10, 13, 10, 30, tzinfo=timezone.utc)


def codex_session(root: Path, sid: str, stamp: str, model: str, effort: str = "low") -> None:
    day = root / "2026" / "10" / "13"
    day.mkdir(parents=True, exist_ok=True)
    rows = [
        {"timestamp": f"2026-10-13T{stamp}:00.000Z", "type": "session_meta", "payload": {"id": sid, "cwd": "/factory"}},
        {"timestamp": f"2026-10-13T{stamp}:05.000Z", "type": "turn_context", "payload": {"model": model, "effort": effort}},
        {"timestamp": f"2026-10-13T{stamp}:09.000Z", "type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 1200, "output_tokens": 80}}}},
    ]
    (day / f"rollout-2026-10-13T{stamp.replace(':', '-')}-00-{sid}.jsonl").write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")


class SessionCaptureTests(unittest.TestCase):
    def test_single_overlapping_session_gives_model_effort_and_tokens(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex_session(root, "aaa", "10:05", "gpt-6-luna")
            seen = session_capture.resolve("codex", START, END, root=root)
        self.assertEqual((seen["model"], seen["effort"], seen["source"]), ("gpt-6-luna", "low", "unique_model"))
        self.assertEqual((seen["input_tokens"], seen["output_tokens"]), (1200, 80))

    def test_session_id_selects_exact_thread(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex_session(root, "aaa", "10:05", "gpt-6-luna")
            codex_session(root, "bbb", "10:10", "gpt-6.1-sol")
            seen = session_capture.resolve("codex", START, END, "bbb", root=root)
        self.assertEqual((seen["model"], seen["source"]), ("gpt-6.1-sol", "session_id"))

    def test_disagreeing_sessions_claim_no_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex_session(root, "aaa", "10:05", "gpt-6-luna")
            codex_session(root, "bbb", "10:10", "gpt-6.1-sol")
            seen = session_capture.resolve("codex", START, END, root=root)
        self.assertIsNone(seen["model"])
        self.assertEqual((seen["source"], seen["candidate_models"]), ("ambiguous", ["gpt-6-luna", "gpt-6.1-sol"]))

    def test_no_session_means_unresolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            seen = session_capture.resolve("codex", START, END, root=Path(tmp))
        self.assertEqual((seen["model"], seen["source"]), (None, "none"))

    def test_unknown_runtime_is_empty(self):
        self.assertEqual(session_capture.resolve("other", START, END)["source"], "none")


class EffectiveModelTests(unittest.TestCase):
    def test_precedence_observed_then_inferred_then_declared(self):
        opened = {"model": "declared"}
        self.assertEqual(usage.effective(opened, {"model_observed": "seen"}, {"model_observed": "guess"}), "seen")
        self.assertEqual(usage.effective(opened, {"model_observed": None}, {"model_observed": "guess"}), "guess")
        self.assertEqual(usage.effective(opened, None, None), "declared")

    def test_unknown_and_missing_are_unresolved(self):
        self.assertIsNone(usage.effective({"model": "unknown"}, None, None))
        self.assertIsNone(usage.effective({"model": None}, {}, None))


if __name__ == "__main__":
    unittest.main()
