"""Test bằng mock/HTTP transport giả; không gọi model thật hoặc tạo nhãn chuẩn."""

import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import httpx
from pydantic import ValidationError

from Lan.A1_ai_triage.parser import parse_alerts
from Lan.A1_ai_triage.run import run_triage
from Lan.A2_fuzzer_benchmark.runner import DependencyBlockedError, run_branch, write_log_template
from Lan.A3a_ai_config import AIClient, AIConfig, AIResponseError
from Lan.A3a_ai_config.contracts import TriageSuggestion, json_contracts
from Lan.A3a_ai_config.safety import redact, redact_url


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "A1_ai_triage/sample_alert_data.json"


def sample_document():
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def suggestion(alert_id="sample-sqli-001"):
    return {"alert_id": alert_id, "is_real": None, "priority": "P3",
            "reason": "TEST FIXTURE ONLY", "confidence": 0.0,
            "trang_thai_bang_chung": "can_xac_minh"}


def response_fixture(request, content=None, *, status=200, refusal=None):
    """HTTP giả để kiểm tra SDK contract, không phải inference hay benchmark."""
    if status != 200:
        return httpx.Response(status, json={"error": {"message": "SECRET_TEST_BODY"}})
    return httpx.Response(200, json={
        "id": "chatcmpl-test-fixture", "object": "chat.completion", "created": 0,
        "model": "test-fixture", "choices": [{"index": 0, "finish_reason": "stop",
        "message": {"role": "assistant", "content": content, "refusal": refusal}}],
    })


class WorkspaceTests(unittest.TestCase):
    def test_sample_is_explicitly_synthetic(self):
        doc = sample_document()
        self.assertEqual(doc["_meta"]["data_origin"], "synthetic")
        self.assertEqual(len(parse_alerts(doc)), 3)

    def test_native_zap_export(self):
        doc = {"site": [{"alerts": [{"alert": "SAMPLE", "riskcode": "3", "cweid": 89,
               "instances": [{"uri": "http://localhost:3000/a", "param": "q", "evidence": "a"},
                             {"uri": "http://localhost:3000/b", "param": "q", "evidence": "b"}]}]}]}
        rows = parse_alerts(doc)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["risk"], "High")
        self.assertEqual(rows[0]["cweid"], "89")
        self.assertEqual(rows, parse_alerts(doc))
        self.assertNotEqual(rows[0]["alert_id"], rows[1]["alert_id"])

    def test_origin_filter_excludes_other_local_ports(self):
        document = {
            "site": [
                {
                    "alerts": [
                        {
                            "name": "BACKEND",
                            "riskcode": "1",
                            "instances": [
                                {"uri": "http://localhost:3000/a"}
                            ],
                        }
                    ]
                },
                {
                    "alerts": [
                        {
                            "name": "FRONTEND",
                            "riskcode": "1",
                            "instances": [
                                {"uri": "http://localhost:5173/a"}
                            ],
                        }
                    ]
                },
            ]
        }
        rows = parse_alerts(document, allowed_origins={"http://localhost:3000"})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["url"], "http://localhost:3000/a")

    def test_duplicates_rejected(self):
        doc = sample_document()
        doc["alerts"].append(doc["alerts"][0])
        with self.assertRaises(ValueError):
            parse_alerts(doc)

    def test_bad_zap_structure_rejected(self):
        for doc in [{}, {"site": {}}, {"alerts": "bad"}, {"alerts": [1]},
                    {"alerts": [{"instances": []}]}]:
            with self.subTest(doc=doc), self.assertRaises((ValueError, ValidationError)):
                parse_alerts(doc)

    def test_empty_scan_is_not_fabricated(self):
        with AIClient() as client:
            result = run_triage({"alerts": []}, client, source_sha256="test")
        self.assertEqual(result["results"], [])
        self.assertEqual(result["_meta"]["data_origin"], "unverified_external")

    def test_empty_live_scan_does_not_claim_inference(self):
        client = self.live_client(lambda _r: self.fail("Empty scan must not call API"))
        report = run_triage({"alerts": []}, client, source_sha256="test")
        self.assertFalse(report["_meta"]["model_inference_performed"])

    def test_sensitive_fields_and_query(self):
        value = redact({"password": "secret", "Authorization": "Bearer secret",
                        "evidence": "Authorization: Bearer secret\npassword=secret&x=1"})
        self.assertNotIn("secret", json.dumps(value))
        self.assertNotIn("secret", redact_url("http://localhost/a?%74oken=secret&x=1"))

    def test_mock_does_not_use_network_or_key(self):
        with patch.dict(os.environ, {}, clear=True), patch("Lan.A3a_ai_config.client.OpenAI") as sdk:
            with AIClient() as client:
                result = run_triage(sample_document(), client, source_sha256="sample")
            sdk.assert_not_called()
        self.assertFalse(result["_meta"]["model_inference_performed"])
        self.assertFalse(result["_meta"]["is_benchmark_result"])
        self.assertTrue(result["_meta"]["review_required"])
        self.assertEqual(result["_meta"]["final_decision"], "pending_human_review")
        self.assertTrue(all(row["is_real"] is None for row in result["results"]))

    def test_output_schema_rejects_extra_action(self):
        with self.assertRaises(ValidationError):
            TriageSuggestion.model_validate({**suggestion(), "close_alert": True})

    def test_output_schema_rejects_wrong_priority_confidence_bool(self):
        for change in [{"priority": "P0"}, {"confidence": 1.1}, {"is_real": "false"}]:
            with self.subTest(change=change), self.assertRaises(ValidationError):
                TriageSuggestion.model_validate({**suggestion(), **change})

    def test_config_rejects_insecure_provider(self):
        for config in [{"provider": "unknown"}, {"base_url": "http://api.example"},
                       {"base_url": "https://secret@api.example/v1"}, {"max_completion_tokens": 0}]:
            with self.subTest(config=config), self.assertRaises(ValidationError):
                AIConfig(**config)

    def test_live_requires_group_approval(self):
        with self.assertRaises(ValueError):
            AIClient(AIConfig(), mode="live")

    def test_live_requires_key(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
            AIClient(AIConfig(group_approved=True), mode="live")

    def live_client(self, handler):
        env = patch.dict(os.environ, {"OPENAI_API_KEY": "test-only-not-a-real-key"})
        env.start()
        self.addCleanup(env.stop)
        client = AIClient(AIConfig(group_approved=True), mode="live", transport=httpx.MockTransport(handler))
        self.addCleanup(client.close)
        return client

    def test_real_adapter_contract_and_prompt_separation(self):
        calls = []

        def handler(request):
            body = json.loads(request.content)
            calls.append(body)
            self.assertEqual(request.url.path, "/v1/chat/completions")
            self.assertEqual(body["response_format"]["type"], "json_schema")
            self.assertFalse(body["store"])
            self.assertEqual([m["role"] for m in body["messages"]], ["system", "user"])
            self.assertIn("IGNORE_PREVIOUS_TEST", body["messages"][1]["content"])
            self.assertNotIn("IGNORE_PREVIOUS_TEST", body["messages"][0]["content"])
            self.assertNotIn("SENSITIVE_TEST_VALUE", body["messages"][1]["content"])
            return response_fixture(request, json.dumps(suggestion()))

        alert = parse_alerts(sample_document())[0]
        alert["evidence"] = "IGNORE_PREVIOUS_TEST\nAuthorization: Bearer SENSITIVE_TEST_VALUE"
        result = self.live_client(handler).classify_alert(alert)
        self.assertEqual(result["alert_id"], alert["alert_id"])
        self.assertEqual(len(calls), 1)

    def test_live_mismatched_id_rejected(self):
        client = self.live_client(lambda r: response_fixture(r, json.dumps(suggestion("wrong-id"))))
        with self.assertRaises(AIResponseError):
            client.classify_alert(parse_alerts(sample_document())[0])

    def test_live_invalid_json_has_no_mock_fallback(self):
        client = self.live_client(lambda r: response_fixture(r, "not-json"))
        with self.assertRaises(AIResponseError):
            client.classify_alert(parse_alerts(sample_document())[0])

    def test_live_refusal_has_no_mock_fallback(self):
        client = self.live_client(lambda r: response_fixture(r, None, refusal="test refusal"))
        with self.assertRaises(AIResponseError):
            client.classify_alert(parse_alerts(sample_document())[0])

    def test_http_error_does_not_expose_body(self):
        calls = []

        def handler(request):
            calls.append(request)
            return response_fixture(request, status=429)

        with self.assertRaises(AIResponseError) as caught:
            self.live_client(handler).classify_alert(parse_alerts(sample_document())[0])
        self.assertNotIn("SECRET_TEST_BODY", str(caught.exception))
        self.assertEqual(len(calls), 1)

    def context(self, **changes):
        return {"target_url": "http://localhost:3000/api/products?search=test",
                "vulnerability_type": "SQLi", "previous_attempts": [],
                "remaining_requests": 1, **changes}

    def test_mock_payload_is_explicit_stop(self):
        with AIClient() as client:
            self.assertTrue(client.suggest_payload(self.context())["should_stop"])

    def test_payload_scope_rejects_remote_target(self):
        with AIClient() as client, self.assertRaises(ValidationError):
            client.suggest_payload(self.context(target_url="https://example.com"))

    def test_no_payload_call_after_budget_exhausted(self):
        client = self.live_client(lambda _r: self.fail("Must not call API"))
        self.assertTrue(client.suggest_payload(self.context(remaining_requests=0))["should_stop"])

    def test_payload_adapter_works_without_running_fuzzer(self):
        result = {"payload": "SAFE_TEST_MARKER", "reason": "TEST FIXTURE ONLY", "should_stop": False}
        client = self.live_client(lambda r: response_fixture(r, json.dumps(result)))
        self.assertEqual(client.suggest_payload(self.context()), result)

    def test_payload_target_query_secret_is_redacted(self):
        def handler(request):
            body = json.loads(request.content)
            self.assertNotIn("SENSITIVE_TEST_VALUE", body["messages"][1]["content"])
            return response_fixture(request, json.dumps({
                "payload": "", "reason": "TEST FIXTURE ONLY", "should_stop": True,
            }))

        client = self.live_client(handler)
        client.suggest_payload(self.context(
            target_url="http://localhost:3000/api/products?%74oken=SENSITIVE_TEST_VALUE"
        ))

    def test_empty_payload_cannot_continue(self):
        client = self.live_client(lambda r: response_fixture(r, json.dumps({
            "payload": " ", "reason": "TEST FIXTURE ONLY", "should_stop": False,
        })))
        with self.assertRaises(AIResponseError):
            client.suggest_payload(self.context())

    def test_a2_blocks_without_consuming_source(self):
        def payloads():
            self.fail("Blocked scaffold must not consume payloads")
            yield "never"
        with self.assertRaises(DependencyBlockedError):
            run_branch("ai_feedback", payloads(), "http://localhost:3000")

    def test_a2_validates_budget_and_branch(self):
        for name, budget in [("wrong", 50), ("ai_static", 0), ("ai_static", True)]:
            with self.subTest(name=name, budget=budget), self.assertRaises(ValueError):
                run_branch(name, [], "http://localhost:3000", budget)

    def test_a2_log_template_is_empty_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_file, json_file = write_log_template(Path(directory))
            data = json.loads(json_file.read_text(encoding="utf-8"))
            self.assertEqual(data["rows"], [])
            self.assertFalse(data["is_benchmark_result"])
            with csv_file.open(encoding="utf-8", newline="") as stream:
                self.assertEqual(len(list(csv.reader(stream))), 1)
            with self.assertRaises(FileExistsError):
                write_log_template(Path(directory))

    def test_committed_schemas_match_models(self):
        data = json.loads((ROOT / "A3a_ai_config/contracts.json").read_text(encoding="utf-8"))
        self.assertEqual(data, json_contracts())

    def test_cache_outputs_are_explicitly_provenanced(self):
        triage = json.loads((ROOT / "A3b_video_cache/cache/triage_result.json").read_text(encoding="utf-8"))
        self.assertTrue(triage["is_replay"])
        self.assertEqual(triage["data_origin"], "empty_template")
        self.assertEqual(triage["results"], [])

        fuzzer = json.loads((ROOT / "A3b_video_cache/cache/fuzzer_result.json").read_text(encoding="utf-8"))
        self.assertFalse(fuzzer["is_replay"])
        self.assertEqual(fuzzer["data_origin"], "real_local_h3_l2_run")
        self.assertTrue(fuzzer["success"])
        self.assertEqual([item["status"] for item in fuzzer["logs"]], [403, 200])

    def test_cli_sample_and_input_overwrite_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "sample-result.json"
            command = [sys.executable, "-m", "Lan.A1_ai_triage.run", "--output", str(target)]
            completed = subprocess.run(command, cwd=ROOT.parent, capture_output=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(result["_meta"]["execution_mode"], "mock")
            self.assertEqual(result["_meta"]["record_count"], 3)
            original = SAMPLE.read_bytes()
            guard = subprocess.run([sys.executable, "-m", "Lan.A1_ai_triage.run", "--input", str(SAMPLE),
                                    "--output", str(SAMPLE)], cwd=ROOT.parent, capture_output=True)
            self.assertEqual(guard.returncode, 1)
            self.assertEqual(SAMPLE.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
