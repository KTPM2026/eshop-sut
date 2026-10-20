"""Synthetic clocks in temporary folders, never student timing evidence."""

import csv
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock

from Nhu.common import ContractError, read_json, write_json
from Nhu.N2_gan_nhan.labels import COLUMNS, create_sheet
from Nhu.N2_gan_nhan.timing import (apply_timings, label_records, measure,
                                   measure_labels, validate_record)
from Nhu.N3_benchmark_triage.make_sample import sample_pack


ROOT = Path(__file__).resolve().parents[2]


class TimingTests(unittest.TestCase):
    def setUp(self):
        self.dataset = sample_pack()[0]
        self.reviewer = "SYNTHETIC CLOCK TEST ONLY"
        self.instant = datetime(2000, 1, 1, tzinfo=timezone.utc)

    def timed(self, target, *, index=0, purpose="label", **overrides):
        start = self.instant + timedelta(seconds=index * 20)
        args = {"purpose": purpose, "scope_note": "SYNTHETIC TEST, NOT HUMAN WORK",
                "alert_id": self.dataset["alerts"][index]["alert_id"] if purpose == "label" else None,
                "run_id": "test-run" if purpose == "ai-review" else None,
                "confirmed_independent": purpose == "label", "prompt": Mock(return_value=""),
                "wall_clock": Mock(side_effect=[start, start + timedelta(seconds=10)]),
                "counter": Mock(side_effect=[100, 110])}
        args.update(overrides)
        return measure(self.dataset, self.reviewer, target, **args)

    def test_measure_records_start_end_monotonic_and_source(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "clock.json"
            record = self.timed(path)
            self.assertEqual(record, read_json(path))
            self.assertEqual(record["elapsed_seconds"], 10)
            self.assertEqual(record["started_at_utc"], "2000-01-01T00:00:00+00:00")
            self.assertEqual(record["finished_at_utc"], "2000-01-01T00:00:10+00:00")
            self.assertEqual(record["_meta"]["source_sha256"], self.dataset["_meta"]["source_sha256"])
            self.assertNotIn("is_real", record)
            self.assertNotIn("priority", record)

    def test_overwrite_rejected_before_prompting(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "clock.json"
            self.timed(path)
            prompt = Mock(return_value="")
            with self.assertRaises(ContractError):
                self.timed(path, prompt=prompt)
            prompt.assert_not_called()

    def test_independence_and_target_validated_before_prompt(self):
        invalid = ({"confirmed_independent": False}, {"alert_id": "missing"},
                   {"run_id": "unrelated"}, {"scope_note": ""}, {"purpose": "invented"})
        with tempfile.TemporaryDirectory() as directory:
            for change in invalid:
                prompt = Mock(return_value="")
                with self.subTest(change=change), self.assertRaises(ContractError):
                    self.timed(Path(directory) / "blocked.json", prompt=prompt, **change)
                prompt.assert_not_called()

    def test_interruption_or_cancellation_saves_no_record(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "blocked.json"
            for replies in (["q"], ["", "q"], ["", KeyboardInterrupt()], ["", EOFError()]):
                with self.subTest(replies=replies), self.assertRaises((ContractError, KeyboardInterrupt, EOFError)):
                    self.timed(path, prompt=Mock(side_effect=replies))
                self.assertFalse(path.exists())

    def test_clock_jumps_and_zero_negative_nonfinite_durations_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "blocked.json"
            changes = [{"counter": Mock(side_effect=[100, finish])}
                       for finish in (100, 99, float("nan"), float("inf"))]
            changes.append({"wall_clock": Mock(side_effect=[self.instant, self.instant - timedelta(seconds=10)])})
            changes.append({"wall_clock": Mock(side_effect=[self.instant, self.instant + timedelta(seconds=100)])})
            for change in changes:
                with self.subTest(change=change), self.assertRaises(ContractError):
                    self.timed(path, **change)
                self.assertFalse(path.exists())

    def test_pipeline_and_ai_review_are_separate_from_label_timing(self):
        with tempfile.TemporaryDirectory() as directory:
            for purpose in ("manual-total", "ai-review"):
                record = self.timed(Path(directory) / f"{purpose}.json", purpose=purpose)
                self.assertEqual(record["purpose"], purpose)
                self.assertIsNone(record["alert_id"])
            with self.assertRaises(ContractError):
                label_records(self.dataset, directory, self.reviewer)

    def test_foreign_source_reviewer_timezone_and_unconfirmed_record_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            original = self.timed(Path(directory) / "clock.json")
            changes = ({"source_sha256": "f" * 64}, {"reviewer": "ANOTHER TEST"},
                       {"completion_declared_by_user": False}, {"independence_declared_by_user": False})
            for change in changes:
                record = deepcopy(original)
                record["_meta"].update(change)
                with self.subTest(change=change), self.assertRaises(ContractError):
                    validate_record(record, self.dataset, self.reviewer)
            record = deepcopy(original)
            record["started_at_utc"] = "2000-01-01T00:00:00"
            with self.assertRaises(ContractError):
                validate_record(record, self.dataset, self.reviewer)

    def test_duplicate_and_overlapping_intervals_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            first = self.timed(folder / "one.json")
            write_json(folder / "duplicate.json", first)
            with self.assertRaises(ContractError):
                label_records(self.dataset, folder, self.reviewer)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            self.timed(folder / "one.json")
            self.timed(folder / "overlap.json", index=1,
                       wall_clock=Mock(side_effect=[self.instant, self.instant + timedelta(seconds=10)]))
            with self.assertRaises(ContractError):
                label_records(self.dataset, folder, self.reviewer)

    def test_apply_preserves_labels_and_original_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            records = folder / "records"
            sheet, output = folder / "original.csv", folder / "timed.csv"
            create_sheet(self.dataset, sheet)
            with sheet.open(encoding="utf-8", newline="") as stream:
                original_rows = list(csv.DictReader(stream))
            for row in original_rows:
                row.update({"is_real": "unknown", "priority": "", "reason": "TEST reason, kept verbatim",
                            "evidence_ref": "TEST evidence only"})
            with sheet.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=COLUMNS)
                writer.writeheader()
                writer.writerows(original_rows)
            before = sheet.read_bytes()
            for index in range(len(self.dataset["alerts"])):
                self.timed(records / f"test-{index}.json", index=index)
            self.assertEqual(apply_timings(self.dataset, sheet, records, output, reviewer=self.reviewer), 6)
            self.assertEqual(before, sheet.read_bytes())
            with output.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertTrue(all(row["elapsed_seconds"] == "10.0" for row in rows))
            for original, timed in zip(original_rows, rows):
                self.assertEqual({key: value for key, value in original.items() if key != "elapsed_seconds"},
                                 {key: value for key, value in timed.items() if key != "elapsed_seconds"})
            with self.assertRaises(FileExistsError):
                apply_timings(self.dataset, sheet, records, output, reviewer=self.reviewer)
            with self.assertRaises(ContractError):
                apply_timings(self.dataset, output, records, folder / "double.csv", reviewer=self.reviewer)

    def test_missing_or_foreign_sheet_rows_rejected_without_output(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            sheet, output = folder / "labels.csv", folder / "blocked.csv"
            create_sheet(self.dataset, sheet)
            self.timed(folder / "records/one.json")
            with self.assertRaises(ContractError):
                apply_timings(self.dataset, sheet, folder / "records", output, reviewer=self.reviewer)
            self.assertFalse(output.exists())
            for index in range(1, 6):
                self.timed(folder / f"records/{index}.json", index=index)
            with sheet.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=COLUMNS)
                writer.writeheader()
            with self.assertRaises(ContractError):
                apply_timings(self.dataset, sheet, folder / "records", output, reviewer=self.reviewer)
            self.assertFalse(output.exists())

    def test_completed_batch_resumes_without_starting_another_timer(self):
        with tempfile.TemporaryDirectory() as directory:
            for index in range(6):
                self.timed(Path(directory) / f"test-{index}.json", index=index)
            measure_labels(self.dataset, self.reviewer, directory,
                           scope_note="SYNTHETIC TEST", confirmed_independent=True)

    def test_cli_rejects_headless_human_timing(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            write_json(folder / "dataset.json", self.dataset)
            result = subprocess.run([sys.executable, "-m", "Nhu.N2_gan_nhan.timing", "record",
                                     "--dataset", str(folder / "dataset.json"), "--reviewer", self.reviewer,
                                     "--purpose", "manual-total", "--scope-note", "TEST ONLY",
                                     "--output", str(folder / "blocked.json")],
                                    cwd=ROOT, input=b"\n\n", capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertFalse((folder / "blocked.json").exists())


if __name__ == "__main__":
    unittest.main()
