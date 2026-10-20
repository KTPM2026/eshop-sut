"""Fixture-only tests for a candidate scope; not actual human labels or AI runs."""

from copy import deepcopy
import csv
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ai.A1_ai_triage.parser import parse_alerts
from Nhu.common import ContractError, file_digest, read_json, validate_dataset
from Nhu.N2_gan_nhan.import_bundle import BUNDLE, import_bundle, sha, verify_source, write_candidate


def fixture():
    source = {"site": [{"alerts": [{"name": "SYNTHETIC TEST ONLY", "riskcode": "1",
               "instances": [{"uri": "http://localhost:3000/a"},
                             {"uri": "http://localhost:3000/b"},
                             {"uri": "http://localhost:5173/c"}]}]}]}
    raw = (json.dumps(source, indent=2) + "\n").encode()
    rows = parse_alerts(source, allowed_origins={"http://localhost:3000"})
    document = {"_meta": {"data_origin": "real_zap_redacted", "origin": "http://localhost:3000",
                           "model_inference_performed": False}, "alerts": rows}
    alerts = (json.dumps(document, indent=2) + "\n").encode()
    manifest = {"status": "frozen_input_pending_human_review", "origin": "http://localhost:3000",
                "source": "alert/TEST_ONLY.json", "source_sha256": sha(raw),
                "record_count": 2, "alert_ids": [row["alert_id"] for row in rows],
                "files": {"alerts.json": sha(alerts)}}
    return raw, alerts, manifest


class BundleImportTests(unittest.TestCase):
    def write(self, output, **changes):
        raw, alerts, manifest = fixture()
        return write_candidate(changes.pop("alert_bytes", alerts), changes.pop("manifest", manifest),
                               changes.pop("source_bytes", raw), output,
                               dataset_id="SYNTHETIC TEST DATASET", git_commit="a" * 40, **changes)

    def test_candidate_preserves_exact_a1_bytes_ids_and_blank_sheet(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / "candidate"
            report = self.write(folder)
            dataset = read_json(folder / "dataset.json")
            self.assertEqual((folder / "a1-input.json").read_bytes(), fixture()[1])
            self.assertEqual(dataset["_meta"]["source_sha256"], file_digest(folder / "a1-input.json"))
            self.assertEqual(len(validate_dataset(dataset)), 2)
            self.assertFalse(report["is_active_dataset"])
            self.assertFalse(report["scope_approved"])
            self.assertFalse(report["human_labels_assigned"])
            self.assertFalse(report["ai_inference_performed"])
            self.assertEqual(report["source_verification"], "exact_bytes")
            with (folder / "nhu-labels.blank.csv").open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 2)
            self.assertTrue(all(row["is_real"] == row["elapsed_seconds"] == row["priority"] == "" for row in rows))
            self.assertFalse((folder / "review_phat.json").exists())

    def test_candidate_does_not_overwrite_any_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / "candidate"
            self.write(folder)
            before = {path.name: path.read_bytes() for path in folder.iterdir()}
            with self.assertRaises(ContractError):
                self.write(folder)
            self.assertEqual(before, {path.name: path.read_bytes() for path in folder.iterdir()})

    def test_tampered_frozen_alert_bytes_rejected_before_any_output(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / "blocked"
            with self.assertRaises(ContractError):
                self.write(folder, alert_bytes=fixture()[1] + b" ")
            self.assertFalse(folder.exists())

    def test_wrong_source_or_fake_approval_hash_rejected(self):
        raw = fixture()[0]
        self.assertEqual(verify_source(raw, sha(raw)), "exact_bytes")
        with self.assertRaises(ContractError):
            verify_source(raw + b" ", sha(raw))
        with self.assertRaises(ContractError):
            verify_source(raw, "invalid")

    def test_source_line_ending_difference_explicitly_recorded_without_changing_a1_hash(self):
        raw, alerts, manifest = fixture()
        manifest["source_sha256"] = sha(raw.replace(b"\n", b"\r\n"))
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / "candidate"
            report = self.write(folder, manifest=manifest)
            self.assertEqual(report["source_verification"], "line_endings_only")
            self.assertEqual(report["source_sha256"], sha(alerts))
            self.assertNotEqual(report["raw_zap_sha256"], report["observed_source_blob_sha256"])

    def test_wrong_count_ids_origin_status_or_model_metadata_rejected(self):
        changes = ({"record_count": 3}, {"alert_ids": []}, {"origin": "https://example.invalid"},
                   {"status": "adjudicated"})
        with tempfile.TemporaryDirectory() as directory:
            for change in changes:
                manifest = deepcopy(fixture()[2])
                manifest.update(change)
                with self.subTest(change=change), self.assertRaises(ContractError):
                    self.write(Path(directory) / "blocked", manifest=manifest)

    def test_labels_hidden_fields_or_changed_parser_rows_are_not_imported(self):
        for change in ("label", "hidden", "model", "changed_rows"):
            raw, alerts, manifest = fixture()
            document = json.loads(alerts)
            if change == "label":
                document["alerts"][0]["is_real"] = True
            elif change == "hidden":
                document["hidden_truth"] = "TEST ONLY"
            elif change == "model":
                document["_meta"]["model_inference_performed"] = True
            else:
                document["alerts"][0]["evidence"] = "changed source evidence"
            edited = json.dumps(document).encode()
            manifest["files"]["alerts.json"] = sha(edited)
            with tempfile.TemporaryDirectory() as directory:
                folder = Path(directory) / "blocked"
                with self.subTest(change=change), self.assertRaises(ContractError):
                    self.write(folder, alert_bytes=edited, manifest=manifest)
                self.assertFalse(folder.exists())

    def test_git_import_never_reads_either_reviewer_sheet(self):
        raw, alerts, manifest = fixture()
        responses = {f"{'a' * 40}:{BUNDLE}/manifest.json": json.dumps(manifest).encode(),
                     f"{'a' * 40}:{BUNDLE}/alerts.json": alerts,
                     f"{'a' * 40}:alert/TEST_ONLY.json": raw}
        def read_blob(command, target):
            self.assertEqual(command, "show")
            self.assertNotIn("review_phat", target)
            self.assertNotIn("review_nhu", target)
            return responses[target]
        with tempfile.TemporaryDirectory() as directory:
            with patch("Nhu.N2_gan_nhan.import_bundle.resolve_ref", return_value="a" * 40), \
                    patch("Nhu.N2_gan_nhan.import_bundle.git_bytes", side_effect=read_blob):
                report = import_bundle("TEST_REF", Path(directory) / "candidate", dataset_id="TEST ONLY")
            self.assertEqual(report["record_count"], 2)


if __name__ == "__main__":
    unittest.main()
