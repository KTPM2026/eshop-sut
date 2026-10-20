"""Failure recovery and cloud provenance, using fake APIs only."""

import json
from pathlib import Path
import tempfile
import unittest
import contextlib
import io
from unittest.mock import patch

from ai.A1_ai_triage.live import execute
from ai.A2_fuzzer_benchmark.live import benchmark
from ai.A2_fuzzer_benchmark.offline import run_branch
from ai.A3a_ai_config import AIConfig, AIResponseError
from ai.tests import test_preparation as preparation


class FakeClient:
    config = AIConfig(group_approved=True)
    mode = "live"

    def __init__(self, fail=None):
        self.calls = []
        self.fail = fail

    def classify_alert(self, alert):
        self.calls.append({"status": "error" if alert["alert_id"] == self.fail else "success"})
        if alert["alert_id"] == self.fail:
            raise AIResponseError("fixture")
        return {"alert_id": alert["alert_id"], "is_real": None, "priority": "P3",
            "reason": "fixture", "confidence": 0.0, "trang_thai_bang_chung": "can_xac_minh"}


class LiveTests(unittest.TestCase):
    def test_legacy_playback_does_not_invent_missing_cache_or_success(self):
        from demo.ai_fuzzer import ai_fuzzer
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.json"
            with patch.object(ai_fuzzer, "CACHE_FILE", path), contextlib.redirect_stdout(io.StringIO()):
                ai_fuzzer.run_playback()
            self.assertFalse(path.exists())
            path.write_text(json.dumps({"logs": [{"attempt": 1, "payload": "normal",
                "blocked": False, "status": 200}]}))
            output = io.StringIO()
            with patch.object(ai_fuzzer, "CACHE_FILE", path), patch.object(ai_fuzzer.time, "sleep"), contextlib.redirect_stdout(output):
                ai_fuzzer.run_playback()
            self.assertNotIn("85.7", output.getvalue())
            self.assertNotIn("THÀNH CÔNG", output.getvalue())

    def test_checkpoint_keeps_success_and_resume_checks_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "input.json", Path(directory) / "run.json"
            source.write_text(json.dumps({"alerts": [{"alert_id": i, "name": "Test", "risk": "Low",
                "url": "http://localhost/test", "param": "", "evidence": "", "cweid": None}
                for i in ("a", "b", "c")]}))
            failed = execute(source, output, FakeClient(fail="b"))
            self.assertEqual([r["alert_id"] for r in failed["results"]], ["a"])
            self.assertEqual(failed["_meta"]["status"], "incomplete")
            resumed = FakeClient()
            complete = execute(source, output, resumed, resume=True)
            self.assertEqual(len(resumed.calls), 2)
            self.assertEqual(complete["_meta"]["status"], "completed")
            self.assertEqual(len(complete["attempts"]), 4)
            with self.assertRaises(FileExistsError):
                execute(source, output, resumed)
            source.write_text(source.read_text() + "\n")
            with self.assertRaises(ValueError):
                execute(source, output, resumed, resume=True)

    def test_cloud_failure_does_not_send_heuristic_payload(self):
        request = preparation.PreparationTests().request
        def fail(*_):
            raise AIResponseError("fixture")
        row = run_branch("heuristic_feedback", request=request, proposer=fail)
        self.assertEqual(row["stop_reason"], "ai_error")
        self.assertEqual(row["attack_requests"], 0)

    def test_static_candidates_and_checkpoint_are_individual(self):
        def request(method, path):
            if "search=" in path and "__no_product_" not in path:
                return 200, json.dumps(preparation.SNAPSHOT)
            return preparation.PreparationTests().request(method, path)
        row = run_branch("fixed_candidates", candidates=["phone", "'/**/OR/**/'1'='1"], request=request)
        self.assertEqual([a["bypass"] for a in row["attempts"]], [False, True])
        self.assertEqual(row["request_to_first_success"], 2)

    def test_live_generation_failure_is_saved_without_fallback(self):
        class Broken(FakeClient):
            def _request(self, *_):
                self.calls.append({"status": "error"})
                raise AIResponseError("fixture")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run.json"
            report = benchmark(output, "http://localhost:3001", client=Broken())
            self.assertEqual(report["status"], "incomplete")
            self.assertFalse(report["rows"])
            self.assertFalse(report["model_inference_performed"])
            self.assertEqual(len(report["generation_calls"]), 1)
