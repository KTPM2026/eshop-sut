"""Audit archived artifacts and input guards; never call an AI provider or time a human."""

from copy import deepcopy
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from Nhu.common import ContractError, SCHEMA_VERSION, digest, file_digest, read_json
from Nhu.N3_benchmark_triage.live_review import compare, export
from Nhu.N3_benchmark_triage.scoring import validate_truth


ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "Nhu/N3_benchmark_triage/evidence/live-20261020"


class LiveReviewTests(unittest.TestCase):
    def setUp(self):
        self.saved = read_json(ARCHIVE / "comparison.json")
        self.raw = (ARCHIVE / "input.json").read_bytes()
        self.dataset = {"schema_version": SCHEMA_VERSION, "_meta": deepcopy(self.saved["dataset"]),
                        "alerts": json.loads(self.raw)["alerts"]}
        self.reference = read_json(ROOT / "Nhu/N2_gan_nhan/assisted-review/nhu-review.json")
        self.runs = [read_json(ARCHIVE / f"run-{i}.json") for i in range(1, 4)]

    def evaluate(self, **changes):
        return compare(changes.get("dataset", self.dataset), changes.get("raw", self.raw),
                       changes.get("reference", self.reference), changes.get("runs", self.runs),
                       accept_assisted=changes.get("accept_assisted", True))

    def test_assisted_comparison_never_claims_human_ground_truth_or_timing(self):
        result = self.evaluate()
        for key in ("is_benchmark_result", "is_ground_truth", "independent_human_review",
                    "human_labels_verified", "human_adjudication_confirmed", "human_timing_measured"):
            self.assertIs(result["_meta"][key], False)
        self.assertEqual(result["reference"]["counts"], {"true": 7, "false": 1, "unknown": 3})
        for run in result["runs"]:
            for key in ("pipeline_seconds", "human_review_seconds", "manual_total_seconds", "time_saved_fraction"):
                self.assertIsNone(run["timing"][key])

    def test_conditional_metrics_and_unknown_denominators(self):
        result = self.evaluate()
        for run in result["runs"]:
            metrics = run["conditional_metrics_against_assisted_reference"]
            self.assertEqual((metrics["scored_records"], metrics["excluded_unresolved_truth"]), (8, 3))
            self.assertEqual((metrics["tp"], metrics["fp"], metrics["tn"], metrics["fn_explicit_false"]),
                             (6, 0, 0, 0))
            self.assertEqual((metrics["abstain_on_true"], metrics["abstain_on_false"]), (1, 1))
            self.assertEqual(metrics["precision"], 1)
            self.assertAlmostEqual(metrics["recall"], 6 / 7)
            self.assertAlmostEqual(metrics["f1"], 12 / 13)
            self.assertEqual(metrics["accuracy"], 6 / 8)
            self.assertEqual(metrics["priority_accuracy"], 1 / 8)
        self.assertEqual(result["baseline_risk_against_assisted_reference"]["accuracy"], 2 / 8)

    def test_original_input_reference_and_runs_are_not_mutated(self):
        before = deepcopy((self.dataset, self.reference, self.runs))
        self.evaluate()
        self.assertEqual(before, (self.dataset, self.reference, self.runs))

    def test_explicit_acceptance_and_no_fake_human_declarations(self):
        with self.assertRaises(ContractError):
            self.evaluate(accept_assisted=False)
        for field in ("is_ground_truth", "independent_human_review"):
            reference = deepcopy(self.reference)
            reference["_meta"][field] = True
            with self.assertRaises(ContractError):
                self.evaluate(reference=reference)
        reference = deepcopy(self.reference)
        reference["labels"][0]["human_elapsed_seconds"] = 10
        with self.assertRaises(ContractError):
            self.evaluate(reference=reference)

    def test_only_verified_lf_crlf_variants_are_accepted(self):
        runs = deepcopy(self.runs)
        for run in runs:
            run["_meta"]["source_sha256"] = self.saved["dataset"]["source_byte_variants"]["lf"]
        self.assertEqual(len(self.evaluate(runs=runs)["runs"]), 3)
        runs[0]["_meta"]["source_sha256"] = "a" * 64
        with self.assertRaises(ContractError):
            self.evaluate(runs=runs)
        with self.assertRaises(ContractError):
            self.evaluate(raw=self.raw + b" ")

    def test_missing_labels_source_or_ids_are_rejected(self):
        reference = deepcopy(self.reference)
        reference["labels"] = reference["labels"][1:]
        with self.assertRaises(ContractError):
            self.evaluate(reference=reference)
        reference = deepcopy(self.reference)
        reference["_meta"]["raw_zap_sha256"] = "0" * 64
        with self.assertRaises(ContractError):
            self.evaluate(reference=reference)
        runs = deepcopy(self.runs)
        runs[0]["results"].pop()
        with self.assertRaises(ContractError):
            self.evaluate(runs=runs)

    def test_mock_replay_incomplete_wrong_config_prompt_and_schema_rejected(self):
        for key, value in (("execution_mode", "mock"), ("is_replay", True), ("status", "incomplete"),
                           ("prompt_sha256", "a" * 64), ("schema_sha256", "a" * 64),
                           ("run_id", "=1+1")):
            with self.subTest(key=key):
                runs = deepcopy(self.runs)
                runs[0]["_meta"][key] = value
                with self.assertRaises(ContractError):
                    self.evaluate(runs=runs)
        runs = deepcopy(self.runs)
        runs[0]["_meta"]["config"]["temperature"] = 1
        with self.assertRaises(ContractError):
            self.evaluate(runs=runs)

    def test_repeated_run_timestamp_response_id_and_missing_attempts_rejected(self):
        for key in ("run_id", "created_at_utc"):
            runs = deepcopy(self.runs)
            runs[1]["_meta"][key] = runs[0]["_meta"][key]
            with self.assertRaises(ContractError):
                self.evaluate(runs=runs)
        runs = deepcopy(self.runs)
        runs[1]["attempts"][1]["api_calls"][0]["response_id"] = runs[1]["attempts"][0]["api_calls"][0]["response_id"]
        with self.assertRaises(ContractError):
            self.evaluate(runs=runs)
        runs = deepcopy(self.runs)
        runs[0]["attempts"] = []
        with self.assertRaises(ContractError):
            self.evaluate(runs=runs)

    def test_archive_hashes_metrics_and_csv_match_actual_bytes(self):
        for row in self.saved["provenance"]["archive_files"]:
            self.assertEqual(file_digest(ARCHIVE / row["file"]), row["sha256"])
        recomputed = self.evaluate()
        self.assertEqual(self.saved["summary"], recomputed["summary"])
        self.assertEqual(self.saved["reference"]["source_content_sha256"], digest(self.reference))
        with (ARCHIVE / "comparison.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(r["is_benchmark_result"] == "False" and r["human_review_seconds"] == "" for r in rows))

    def test_export_does_not_overwrite_or_read_git_first(self):
        with TemporaryDirectory() as temporary, patch("Nhu.N3_benchmark_triage.live_review.resolve_ref") as resolve:
            with self.assertRaises(ContractError):
                export("ignored", temporary, accept_assisted=True)
            resolve.assert_not_called()

    def test_strict_ground_truth_validator_still_refuses_assisted_reference(self):
        with self.assertRaises(ContractError):
            validate_truth(self.saved["reference"], self.dataset, synthetic=False)


if __name__ == "__main__":
    unittest.main()
