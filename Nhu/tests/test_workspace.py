"""Chỉ kiểm thử code bằng dữ liệu tự tạo, không chạy AI/EShop hoặc gán nhãn thật."""

import csv
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from Nhu.common import ContractError, file_digest, read_json, validate_dataset
from Nhu.N2_gan_nhan.labels import COLUMNS, compare_locks, create_sheet, lock_sheet, read_sheet
from Nhu.N3_benchmark_triage.make_sample import sample_pack, write_sample
from Nhu.N3_benchmark_triage.run import evaluate_manifest, write_report
from Nhu.N3_benchmark_triage.scoring import evaluate_benchmark, score_predictions


ROOT = Path(__file__).resolve().parents[2]


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.dataset, self.truth, self.runs = sample_pack()

    def evaluate(self, **changes):
        return evaluate_benchmark(
            changes.pop("dataset", self.dataset), changes.pop("ground_truth", self.truth),
            changes.pop("runs", self.runs), allow_synthetic=True, **changes,
        )

    def as_real_fixture(self):
        """Chỉ đổi cờ trong RAM để test guard, KHÔNG phải tạo ground truth thật."""
        dataset, truth, runs = deepcopy((self.dataset, self.truth, self.runs))
        dataset["_meta"]["data_origin"] = truth["_meta"]["data_origin"] = "real_zap"
        truth["_meta"].update({
            "review_status": "adjudicated", "human_adjudication_confirmed": True,
            "reviewers": ["TEST_REVIEWER_1", "TEST_REVIEWER_2"],
            "independent_lock_sha256": ["a" * 64, "b" * 64],
        })
        for run in runs:
            run["result"]["_meta"].update({
                "data_origin": "unverified_external", "execution_mode": "live",
                "model_inference_performed": True,
            })
            run["result"]["_meta"]["config"]["group_approved"] = True
        return dataset, truth, runs

    def test_expected_confusion_and_abstention(self):
        metrics = self.evaluate()["runs"][0]["metrics"]
        self.assertEqual([metrics[key] for key in ("tp", "fp", "tn", "fn_explicit_false")], [1, 1, 1, 1])
        self.assertEqual(metrics["abstain_on_true"], 1)
        self.assertEqual(metrics["precision"], 0.5)
        self.assertAlmostEqual(metrics["recall"], 1 / 3)
        self.assertEqual(metrics["classification_coverage"], 0.8)
        self.assertEqual(metrics["priority_accuracy"], 0.4)

    def test_unresolved_truth_is_reported_not_treated_as_false(self):
        metrics = self.evaluate()["runs"][0]["metrics"]
        self.assertEqual(metrics["excluded_unresolved_truth"], 1)
        self.assertEqual(metrics["scored_records"], 5)

    def test_safety_union_is_not_double_counted(self):
        metrics = self.evaluate()["runs"][0]["metrics"]
        self.assertEqual(metrics["true_labeled_false"], 1)
        self.assertEqual(metrics["true_assigned_P4"], 2)
        self.assertEqual(metrics["true_labeled_false_or_P4"], 2)
        self.assertEqual(metrics["true_downgraded_from_P1_P2_to_P3_P4"], 2)

    def test_synthetic_requires_explicit_flag(self):
        with self.assertRaises(ContractError):
            evaluate_benchmark(self.dataset, self.truth, self.runs)
        self.assertFalse(self.evaluate()["_meta"]["is_benchmark_result"])

    def test_zero_denominators_are_null(self):
        truth = [{"alert_id": "x", "is_real": False, "priority": "P4"}]
        predicted = [{"alert_id": "x", "is_real": False, "priority": "P4"}]
        metrics = score_predictions(truth, predicted)
        self.assertIsNone(metrics["precision"])
        self.assertIsNone(metrics["recall"])
        truth[0]["is_real"] = None
        metrics = score_predictions(truth, predicted)
        self.assertIsNone(metrics["priority_accuracy"])
        self.assertIsNone(metrics["classification_coverage"])

    def test_review_time_is_included(self):
        timing = self.evaluate(manual_total_seconds=60)["runs"][0]["timing"]
        self.assertEqual(timing["total_seconds"], 15)
        self.assertEqual(timing["time_saved_fraction"], 0.75)

    def test_no_review_no_time_saving_claim(self):
        self.runs[0]["review_completed"] = False
        timing = self.evaluate(manual_total_seconds=60)["runs"][0]["timing"]
        self.assertIsNone(timing["total_seconds"])
        self.assertIsNone(timing["time_saved_fraction"])

    def test_no_manual_time_or_zero_no_time_saving_claim(self):
        for manual in (None, 0):
            with self.subTest(manual=manual):
                self.assertIsNone(self.evaluate(manual_total_seconds=manual)["runs"][0]["timing"]["time_saved_fraction"])

    def test_invalid_time_rejected(self):
        for value in (-1, float("nan"), float("inf"), True, "10"):
            with self.subTest(value=value), self.assertRaises(ContractError):
                self.evaluate(manual_total_seconds=value)

    def test_at_least_three_runs(self):
        with self.assertRaises(ContractError):
            self.evaluate(runs=self.runs[:2])

    def test_duplicate_run_id_and_timestamp_rejected(self):
        for key in ("id", "timestamp"):
            runs = deepcopy(self.runs)
            if key == "id":
                runs[1]["run_id"] = runs[0]["run_id"]
            else:
                runs[1]["result"]["_meta"]["created_at_utc"] = runs[0]["result"]["_meta"]["created_at_utc"]
            with self.subTest(key=key), self.assertRaises(ContractError):
                self.evaluate(runs=runs)

    def test_replay_rejected(self):
        self.runs[0]["result"]["_meta"]["is_replay"] = True
        with self.assertRaises(ContractError):
            self.evaluate()

    def test_same_instant_different_timezone_is_not_a_new_run(self):
        self.runs[1]["result"]["_meta"]["created_at_utc"] = "2000-01-01T07:00:00+07:00"
        with self.assertRaises(ContractError):
            self.evaluate()

    def test_different_model_or_config_rejected(self):
        self.runs[1]["result"]["_meta"]["config"]["model"] = "different"
        with self.assertRaises(ContractError):
            self.evaluate()

    def test_missing_extra_duplicate_alert_id_rejected(self):
        for change in ("missing", "extra", "duplicate"):
            runs = deepcopy(self.runs)
            rows = runs[0]["result"]["results"]
            if change == "missing":
                rows.pop()
            else:
                rows.append({**rows[0], "alert_id": "extra" if change == "extra" else rows[0]["alert_id"]})
            runs[0]["result"]["_meta"]["record_count"] = len(rows)
            with self.subTest(change=change), self.assertRaises(ContractError):
                self.evaluate(runs=runs)

    def test_source_hash_mismatch_rejected(self):
        self.runs[0]["result"]["_meta"]["source_sha256"] = "f" * 64
        with self.assertRaises(ContractError):
            self.evaluate()

    def test_output_types_and_extra_action_rejected(self):
        for change in ({"confidence": float("nan")}, {"is_real": "false"},
                       {"priority": "P0"}, {"close_alert": True}):
            runs = deepcopy(self.runs)
            runs[0]["result"]["results"][0].update(change)
            with self.subTest(change=change), self.assertRaises(ContractError):
                self.evaluate(runs=runs)

    def test_real_mode_requires_protocol_and_human_truth(self):
        dataset, truth, runs = self.as_real_fixture()
        with self.assertRaises(ContractError):
            evaluate_benchmark(dataset, truth, runs)
        truth["_meta"]["human_adjudication_confirmed"] = False
        with self.assertRaises(ContractError):
            evaluate_benchmark(dataset, truth, runs, protocol_approved=True)

    def test_real_mode_rejects_mock_or_missing_review(self):
        dataset, truth, runs = self.as_real_fixture()
        runs[0]["result"]["_meta"]["execution_mode"] = "mock"
        with self.assertRaises(ContractError):
            evaluate_benchmark(dataset, truth, runs, protocol_approved=True)
        runs[0]["result"]["_meta"]["execution_mode"] = "live"
        runs[0]["review_seconds"] = None
        with self.assertRaises(ContractError):
            evaluate_benchmark(dataset, truth, runs, protocol_approved=True)

    def test_validated_real_shape_only_not_real_experiment(self):
        dataset, truth, runs = self.as_real_fixture()
        report = evaluate_benchmark(dataset, truth, runs, protocol_approved=True)
        self.assertTrue(report["_meta"]["is_benchmark_result"])
        self.assertIsNone(report["summary"]["time_saved_fraction"]["mean"])

    def test_risk_baseline_has_unknown_abstention(self):
        metrics = self.evaluate()["baseline_risk"]
        self.assertEqual(metrics["tp"], 1)
        self.assertEqual(metrics["fp"], 1)
        self.assertEqual(metrics["fn_explicit_false"], 1)
        self.assertEqual(metrics["abstain_on_true"], 1)

    def test_csv_formula_run_id_rejected(self):
        self.runs[0]["run_id"] = "=DANGEROUS_FORMULA"
        with self.assertRaises(ContractError):
            self.evaluate()

    def test_dataset_cannot_contain_ai_labels(self):
        self.dataset["alerts"][0]["is_real"] = True
        with self.assertRaises(ContractError):
            validate_dataset(self.dataset)

    def test_secret_config_field_or_url_rejected(self):
        for key, value in (("api_key", "TEST-NOT-REAL"), ("base_url", "https://secret@api.example/v1")):
            runs = deepcopy(self.runs)
            runs[0]["result"]["_meta"]["config"][key] = value
            with self.subTest(key=key), self.assertRaises(ContractError):
                self.evaluate(runs=runs)

    def test_sample_generator_and_report_export(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / "input"
            write_sample(folder)
            report = evaluate_manifest(folder / "manifest.json", allow_synthetic=True)
            self.assertFalse(report["_meta"]["is_benchmark_result"])
            out = Path(directory) / "report"
            write_report(report, out)
            self.assertEqual(read_json(out / "benchmark.json")["_meta"]["run_count"], 3)
            with (out / "benchmark.csv").open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 3)
            self.assertTrue(all(row["is_benchmark_result"] == "False" for row in rows))
            with self.assertRaises(ContractError):
                write_report(report, out)
            with self.assertRaises(ContractError):
                write_sample(folder)

    def filled_sheet(self, folder):
        path = folder / "labels.csv"
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=COLUMNS)
            writer.writeheader()
            for row in self.dataset["alerts"]:
                writer.writerow({
                    "alert_id": row["alert_id"], "risk": row["risk"], "is_real": "unknown",
                    "priority": "", "reason": "TEST ONLY UNKNOWN", "evidence_ref": "TEST ONLY",
                    "elapsed_seconds": "1",
                })
        return path

    def test_prepare_sheet_is_blank_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            sheet = Path(directory) / "blank.csv"
            self.assertEqual(create_sheet(self.dataset, sheet), 6)
            with sheet.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertTrue(all(row["is_real"] == row["priority"] == row["elapsed_seconds"] == "" for row in rows))
            with self.assertRaises(FileExistsError):
                create_sheet(self.dataset, sheet)
            with self.assertRaises(ContractError):
                read_sheet(sheet, self.dataset)

    def test_lock_requires_human_declaration_and_keeps_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            sheet = self.filled_sheet(folder)
            with self.assertRaises(ContractError):
                lock_sheet(self.dataset, sheet, folder / "blocked.json", reviewer="TEST")
            result = lock_sheet(self.dataset, sheet, folder / "lock.json",
                                reviewer="TEST-NOT-NHU", confirmed_independent=True)
            self.assertEqual(result["_meta"]["label_csv_sha256"], file_digest(sheet))
            self.assertTrue(all(row["is_real"] is None for row in result["labels"]))

    def test_compare_only_lists_disagreement_not_ground_truth(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            sheet = self.filled_sheet(folder)
            first = lock_sheet(self.dataset, sheet, folder / "first.json",
                               reviewer="TEST-1", confirmed_independent=True)
            second = deepcopy(first)
            second["_meta"]["reviewer"] = "TEST-2"
            second["labels"][0].update({"is_real": True, "priority": "P1"})
            report = compare_locks(first, second)
            self.assertFalse(report["is_ground_truth"])
            self.assertEqual(len(report["disagreements"]), 1)
            self.assertAlmostEqual(report["classification_agreement"], 5 / 6)
            with self.assertRaises(ContractError):
                compare_locks(first, first)

    def test_compare_rejects_malformed_external_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            first = lock_sheet(self.dataset, self.filled_sheet(folder), folder / "first.json",
                               reviewer="TEST-1", confirmed_independent=True)
            second = deepcopy(first)
            second["_meta"]["reviewer"] = "TEST-2"
            second["labels"][0]["is_real"] = "false"
            with self.assertRaises(ContractError):
                compare_locks(first, second)

    def test_cli_synthetic_guard_and_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / "input"
            write_sample(folder)
            cmd = [sys.executable, "-m", "Nhu.N3_benchmark_triage.run", "--manifest",
                   str(folder / "manifest.json"), "--output-dir", str(Path(directory) / "out")]
            blocked = subprocess.run(cmd, cwd=ROOT, capture_output=True)
            self.assertEqual(blocked.returncode, 1)
            self.assertFalse((Path(directory) / "out").exists())
            allowed = subprocess.run(cmd + ["--allow-synthetic"], cwd=ROOT, capture_output=True)
            self.assertEqual(allowed.returncode, 0, allowed.stderr)


if __name__ == "__main__":
    unittest.main()
