"""Handoff metadata tests; no peer labels, AI calls or real ground truth."""

from copy import deepcopy
import json
import unittest

from Nhu.check_handoff import (hash_status, id_comparison, inspect_flat_export,
                               markdown_ids, summarize_handoffs)
from Nhu.common import ContractError
from Nhu.N3_benchmark_triage.make_sample import sample_pack


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.dataset = sample_pack()[0]
        self.ids = [row["alert_id"] for row in self.dataset["alerts"]]
        self.peer = ("| # | Alert | Risk | Label |\n|---|---|---|---|\n" +
                     "\n".join(f"| {item_id} | PRIVATE NAME | High | PRIVATE VERDICT |" for item_id in self.ids) +
                     "\n\n| Alert # | Other labels |\n|---|---|\n| another | DO NOT READ |\n")
        self.lan = {"status": "awaiting_two_independent_reviewers",
                    "alerts": deepcopy(self.dataset["alerts"][:2])}
        for row in self.lan["alerts"]:
            row.update({"is_real": "PRIVATE VERDICT", "reason": "PRIVATE REASON"})
        self.cache = {"status": "awaiting_real_results", "results": [], "is_replay": True,
                      "model_inference_performed": False, "source_sha256": None}

    def summarize(self, **changes):
        args = {"input_sha256": self.dataset["_meta"]["source_sha256"], "phat_document": self.peer,
                "lan_document": self.lan, "cache": self.cache}
        args.update(changes)
        return summarize_handoffs(self.dataset, {"alerts": self.dataset["alerts"]}, **args)

    def test_only_id_column_read_and_second_table_not_mixed(self):
        self.assertEqual(markdown_ids(self.peer), set(self.ids))

    def test_missing_duplicate_or_unrecognized_ids_rejected(self):
        for document in ("no table", "| # | Label |\n|---|---|\n| x | private |\n| x | private |",
                         "| # | Label |\n|---|---|\n| =bad | private |"):
            with self.subTest(document=document), self.assertRaises(ContractError):
                markdown_ids(document)

    def test_comparison_never_auto_maps_group_labels_to_instances(self):
        result = id_comparison(set(self.ids), {"1", "2"})
        self.assertEqual(result["matching_ids"], 0)
        self.assertEqual(result["extra_ids"], 2)
        self.assertFalse(result["exact_id_set"])

    def test_summary_does_not_expose_peer_verdicts_or_ai_reasons(self):
        result = self.summarize()
        serialized = json.dumps(result)
        for private in ("PRIVATE VERDICT", "PRIVATE REASON", "PRIVATE NAME", "DO NOT READ"):
            self.assertNotIn(private, serialized)
        self.assertEqual(result["local_dataset"]["record_count"], 6)
        self.assertEqual(result["lan_label_template"]["matching_ids"], 2)
        self.assertEqual(result["lan_label_template"]["missing_reference_ids"], 4)
        self.assertFalse(result["ready_to_benchmark"])
        self.assertFalse(result["is_benchmark_result"])

    def test_local_input_hash_or_ids_must_match(self):
        with self.assertRaises(ContractError):
            self.summarize(input_sha256="f" * 64)
        with self.assertRaises(ContractError):
            summarize_handoffs(self.dataset, {"alerts": self.dataset["alerts"][:2]},
                               input_sha256=self.dataset["_meta"]["source_sha256"],
                               phat_document=self.peer, lan_document=self.lan, cache=self.cache)

    def test_empty_triage_cache_is_not_a_live_run(self):
        cache = self.summarize()["lan_triage_cache"]
        self.assertEqual(cache["record_count"], 0)
        self.assertTrue(cache["is_replay"])
        self.assertFalse(cache["model_inference_performed"])
        self.assertEqual(cache["source_hash_status"], "missing")

    def test_missing_hash_is_not_reported_as_changed_content(self):
        expected = "a" * 64
        self.assertEqual(hash_status(None, expected), "missing")
        self.assertEqual(hash_status("invalid", expected), "invalid")
        self.assertEqual(hash_status("b" * 64, expected), "different")
        self.assertEqual(hash_status(expected, expected), "match")

    def test_flat_export_collisions_are_reported_not_deduplicated(self):
        record = {"name": "SYNTHETIC TEST", "risk": "Informational",
                  "url": "http://localhost:3000/a?token=TEST_ONLY_SECRET", "evidence": ""}
        document = {"alerts": [record, {**record, "id": "another-zap-event"}]}
        original = deepcopy(document)
        result = inspect_flat_export(document)
        self.assertEqual(document, original)
        self.assertEqual(result["raw_records"], 2)
        self.assertEqual(result["unique_normalized_ids"], 1)
        self.assertEqual(result["duplicate_records"], 1)
        self.assertFalse(result["direct_parser_input_ready"])
        self.assertNotIn("TEST_ONLY_SECRET", json.dumps(result))

    def test_flat_export_origin_filter_does_not_visit_external_urls(self):
        record = {"name": "SYNTHETIC TEST", "risk": "Low", "url": "https://example.invalid/a"}
        result = inspect_flat_export({"alerts": [record]})
        self.assertEqual(result["in_scope_records"], 0)
        self.assertFalse(result["direct_parser_input_ready"])


if __name__ == "__main__":
    unittest.main()
