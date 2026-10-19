"""Check cached assisted review/provenance, without calling an app or model."""

from copy import deepcopy
import csv
from pathlib import Path
import subprocess
import tempfile
import unittest

from Nhu.common import ContractError, file_digest, read_json, text_file_digest
from Nhu.N2_gan_nhan.build_review import CSV_FIELDS, make_review, peer_rows, write_review
from Nhu.N2_gan_nhan.labels import read_sheet
from Nhu.N3_benchmark_triage.scoring import validate_truth


ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "Nhu/N2_gan_nhan"


class AssistedReviewTests(unittest.TestCase):
    def setUp(self):
        self.dataset = read_json(HERE / "data/h1-20261014/dataset.json")
        self.provenance = read_json(HERE / "data/h1-20261014/provenance.json")
        self.raw = read_json(ROOT / "alert/2026-10-14-ZAP-Report-.json")
        self.decisions = read_json(HERE / "review_decisions.json")
        self.verification = read_json(HERE / "evidence/main-13f4d88/verification.json")
        self.peer = peer_rows((ROOT / "Phat/P2_nhan_alert/alert-labeling-template.md").read_text(encoding="utf-8-sig"))

    def review(self, **changes):
        values = {"dataset": self.dataset, "provenance": self.provenance, "raw": self.raw,
                  "decisions": self.decisions, "verification": self.verification, "peer": self.peer}
        values.update(changes)
        return make_review(**values)

    def test_29_records_13_local_groups_and_2_exclusions(self):
        report = self.review()
        self.assertEqual(len(report["labels"]), 29)
        self.assertEqual(len(report["groups"]), 15)
        self.assertEqual(report["summary"]["instances"], {"true": 14, "unknown": 5, "false": 10})
        self.assertEqual(report["summary"]["groups"], {"excluded": 2, "true": 6, "unknown": 3, "false": 4})
        self.assertEqual({row["alert_id"] for row in report["labels"]},
                         {row["alert_id"] for row in self.dataset["alerts"]})
        self.assertTrue(all(not row["alert_ids"] for row in report["groups"][:2]))

    def test_no_independence_human_timing_or_ground_truth_claims(self):
        report = self.review()
        for key in ("independent_human_review", "human_approved", "is_ground_truth", "is_benchmark_result"):
            self.assertIs(report["_meta"][key], False)
        self.assertTrue(report["_meta"]["reference_to_phat_read"])
        self.assertIsNone(report["_meta"]["human_total_seconds"])
        self.assertTrue(all(row["human_elapsed_seconds"] is None and row["human_approved"] is False
                            for row in report["labels"]))
        with self.assertRaises(ContractError):
            validate_truth(report, self.dataset, synthetic=False)

    def test_three_pending_groups_not_auto_agreement_or_adjudication(self):
        report = self.review()
        pending = {row["group"] for row in report["groups"]
                   if row["comparison_status"] == "pending_joint_verification"}
        self.assertEqual(pending, {4, 8, 13})
        self.assertEqual(report["summary"]["comparison"]["same_provisional_classification"], 10)
        self.assertNotIn("accuracy", report["summary"])

    def test_artifact_bytes_match_actual_runner_and_screenshots(self):
        self.assertEqual(self.verification["runner_sha256"], file_digest(HERE / "verify_local.cjs"))
        for filename, recorded_hash in self.verification["screenshots"].items():
            image = HERE / "evidence/main-13f4d88" / filename
            self.assertEqual(file_digest(image), recorded_hash)
            self.assertGreater(image.stat().st_size, 10000)

    def test_published_review_keeps_actual_provenance_and_no_victim_delivery_claim(self):
        published = read_json(HERE / "assisted-review/nhu-review.json")
        self.assertEqual(published["labels"], self.review()["labels"])
        self.assertEqual(published["_meta"]["verification_sha256"],
                         file_digest(HERE / "evidence/main-13f4d88/verification.json"))
        self.assertEqual(published["_meta"]["decisions_text_sha256"], text_file_digest(HERE / "review_decisions.json"))
        self.assertFalse(self.verification["checkpoints"]["victim_delivery_demonstrated"])
        self.assertFalse(self.verification["checkpoints"]["url_query_delivery_executed"])

    def test_failed_controls_or_manual_execution_claim_refused(self):
        for change in ("sql", "student", "constant"):
            verification = deepcopy(self.verification)
            if change == "sql":
                verification["requests"]["sql-false"]["response"]["json_array_count"] = 5
            elif change == "student":
                verification["student_performed"] = True
            else:
                verification["checkpoints"]["react_numeric_constant"]["found"] = False
            with self.subTest(change=change), self.assertRaises(ContractError):
                self.review(verification=verification)

    def test_mapping_and_decision_duplicates_or_external_negatives_refused(self):
        for change in ("mapping", "duplicate", "external"):
            provenance, decisions = deepcopy((self.provenance, self.decisions))
            if change == "mapping":
                provenance["mapping"].pop()
            elif change == "duplicate":
                decisions["groups"].append(decisions["groups"][0])
            else:
                decisions["groups"][0].update({"status": "false", "is_real": False, "priority": "P4"})
            with self.subTest(change=change), self.assertRaises(ContractError):
                self.review(provenance=provenance, decisions=decisions)

    def test_export_is_distinct_from_independent_sheet_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "review"
            report = write_review(output)
            self.assertEqual(read_json(output / "nhu-review.json")["labels"], report["labels"])
            with (output / "nhu-review.csv").open(encoding="utf-8", newline="") as stream:
                reader = csv.DictReader(stream)
                self.assertEqual(tuple(reader.fieldnames), CSV_FIELDS)
                rows = list(reader)
            self.assertEqual(len(rows), 29)
            self.assertTrue(all(row["human_elapsed_seconds"] == "" for row in rows))
            with self.assertRaises(ContractError):
                read_sheet(output / "nhu-review.csv", self.dataset)
            with self.assertRaises(ContractError):
                write_review(output)

    def test_peer_format_change_fails_instead_of_guessing(self):
        with self.assertRaises(ContractError):
            peer_rows("| 1 | changed format |")

    def test_runner_redacts_query_secrets_without_running_main(self):
        code = ("const {safeUrl}=require('./Nhu/N2_gan_nhan/verify_local.cjs');"
                "console.log(safeUrl('http://127.0.0.1:5173/?token=TEST_SECRET&reset_token=OTHER_SECRET&q=ok'));")
        result = subprocess.run(["node", "-e", code], cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertNotIn("TEST_SECRET", result.stdout)
        self.assertNotIn("OTHER_SECRET", result.stdout)
        self.assertIn("q=ok", result.stdout)


if __name__ == "__main__":
    unittest.main()
