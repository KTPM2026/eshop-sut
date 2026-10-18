import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import parse_qs, urlsplit

from ai.A1_ai_triage.freeze_dataset import freeze
from ai.A2_fuzzer_benchmark.offline import checkpoint, run_branch
from ai.A3b_video_cache.artifacts import build, replay


SNAPSHOT = [{"id": 1, "name": "phone"}, {"id": 2, "name": "laptop"}]


class PreparationTests(unittest.TestCase):
    def test_cache_replay_verifies_hash_and_missing_source_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "run.json"
            target = Path(directory) / "cache.json"
            source.write_text('{"rows":[{"mode":"offline"}]}')
            build(source, target)
            self.assertTrue(replay(target)["is_replay"])
            with self.assertRaises(FileExistsError):
                build(source, target)
            data = json.loads(target.read_text(encoding="utf-8"))
            data["payload"]["rows"][0]["mode"] = "live"
            target.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                replay(target)
            with self.assertRaises(FileNotFoundError):
                replay(Path(directory) / "missing.json")

    def request(self, method, path):
        if path == "/api/waf/reset":
            return 200, "{}"
        if path == "/api/waf/status":
            return 200, json.dumps({"waf_enabled": True, "waf_level": 1})
        if path == "/api/products":
            return 200, json.dumps(SNAPSHOT)
        query = parse_qs(urlsplit(path).query)["search"][0]
        if query.startswith("__no_product_"):
            return 200, "[]"
        return 403, json.dumps({"blocked_keyword": " OR "})

    def test_normal_search_is_not_sqli(self):
        result = checkpoint(SNAPSHOT, "phone", 200, json.dumps(SNAPSHOT[:1]))
        self.assertFalse(result["bypass"])

    def test_differential_oracle_and_wrong_result(self):
        payload = "'/**/OR/**/'1'='1"
        self.assertTrue(checkpoint(SNAPSHOT, payload, 200, json.dumps(SNAPSHOT))["bypass"])
        self.assertFalse(checkpoint(SNAPSHOT, payload, 200, json.dumps(SNAPSHOT[:1]))["bypass"])
        self.assertIsNone(checkpoint(SNAPSHOT, payload, 0, "timeout")["bypass"])

    def test_budget_and_source_exhaustion(self):
        row = run_branch("wordlist_static", 2, self.request)
        self.assertEqual(row["attack_requests"], 2)
        self.assertEqual(row["stop_reason"], "budget_exhausted")
        self.assertEqual(row["total_sut_requests"], 6)
        row = run_branch("fixed_candidates", 50, self.request)
        self.assertEqual(row["stop_reason"], "source_exhausted")
        self.assertIsNone(row["request_to_first_success"])

    def test_preconditions_fail_closed(self):
        for waf in ({"waf_enabled": False, "waf_level": 1}, {"waf_enabled": True, "waf_level": 2}):
            def request(method, path):
                return (200, json.dumps(waf)) if path.endswith("status") else self.request(method, path)
            self.assertEqual(run_branch("wordlist_static", request=request)["attack_requests"], 0)
        def bad_baseline(method, path):
            return (200, json.dumps(SNAPSHOT)) if "__no_product_" in path else self.request(method, path)
        self.assertEqual(run_branch("wordlist_static", request=bad_baseline)["attack_requests"], 0)

    def test_timeout_kept_and_feedback_success_is_per_attempt(self):
        calls = []
        def request(method, path):
            if "search=" in path and "__no_product_" not in path:
                calls.append(path)
                return (403, '{"blocked_keyword":" OR "}') if len(calls) == 1 else (200, json.dumps(SNAPSHOT))
            return self.request(method, path)
        row = run_branch("heuristic_feedback", request=request)
        self.assertEqual([a["bypass"] for a in row["attempts"]], [False, True])
        self.assertEqual(row["request_to_first_success"], 2)
        def timeout(method, path):
            return (0, "transport_error") if "search=" in path and "__no_product_" not in path else self.request(method, path)
        row = run_branch("heuristic_feedback", request=timeout)
        self.assertEqual(row["stop_reason"], "transport_error")
        self.assertIsNone(row["attempts"][0]["bypass"])

    def test_freeze_refuses_overwrite_and_has_no_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.json"
            source.write_text(json.dumps([{"alert_id": "one", "name": "Test", "risk": "Low",
                "url": "http://localhost:3000/test", "param": "", "evidence": "token=secretvalue", "cweid": None}]))
            output = Path(directory) / "bundle"
            manifest = freeze(source, output, "http://localhost:3000")
            self.assertEqual(manifest["record_count"], 1)
            sheet = json.loads((output / "review_nhu.json").read_text(encoding="utf-8"))
            self.assertIsNone(sheet["alerts"][0]["is_real"])
            self.assertNotIn("secretvalue", (output / "alerts.json").read_text(encoding="utf-8"))
            with self.assertRaises(FileExistsError):
                freeze(source, output, "http://localhost:3000")
