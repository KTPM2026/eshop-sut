"""Verify scoped handoff and real-file provenance, without lab/model requests."""

from copy import deepcopy
import csv
from pathlib import Path
import tempfile
import unittest

from Lan.A1_ai_triage.parser import parse_alerts
from Nhu.common import ContractError, digest, file_digest, read_json, text_file_digest, write_json
from Nhu.N2_gan_nhan.prepare_zap import scope_report, write_pack


ROOT = Path(__file__).resolve().parents[2]


def fixture():
    def site(host, instance_host):
        return {"@name": host, "alerts": [{
            "pluginid": "10024", "name": "TEST ONLY", "riskcode": "0", "cweid": "0",
            "instances": [{"id": "1", "uri": instance_host + "/?token=FAKE_NOT_A_SECRET",
                           "method": "GET", "param": "token", "evidence": "token=FAKE_NOT_A_SECRET"}],
        }]}
    return {"@version": "TEST", "created": "2000-01-01T00:00:00Z", "site": [
        site("http://localhost:3000", "http://localhost:3000"),
        site("https://example.invalid", "https://example.invalid"),
        site("http://localhost:5173", "https://example.invalid"),
    ]}


class ZapHandoffTests(unittest.TestCase):
    def test_text_hash_ignores_only_platform_line_endings(self):
        with tempfile.TemporaryDirectory() as directory:
            lf, crlf = Path(directory) / "lf.py", Path(directory) / "crlf.py"
            lf.write_bytes(b"line1\nline2\n")
            crlf.write_bytes(b"line1\r\nline2\r\n")
            self.assertNotEqual(file_digest(lf), file_digest(crlf))
            self.assertEqual(text_file_digest(lf), text_file_digest(crlf))
            crlf.write_bytes(b"changed\r\nline2\r\n")
            self.assertNotEqual(text_file_digest(lf), text_file_digest(crlf))

    def test_scope_checks_both_site_and_instance_and_redacts(self):
        document = fixture()
        original = deepcopy(document)
        rows, inventory = scope_report(document)
        self.assertEqual(document, original)
        self.assertEqual(len(rows), 1)
        self.assertEqual(inventory["excluded_instance_count"], 2)
        self.assertEqual(inventory["mapping"][0]["source_pointer"], "/site/0/alerts/0/instances/0")
        self.assertNotIn("FAKE_NOT_A_SECRET", rows[0]["url"] + rows[0]["evidence"])
        self.assertEqual(parse_alerts({"alerts": rows}), rows)

    def test_duplicate_is_rejected_not_silently_dropped(self):
        document = fixture()
        document["site"][0]["alerts"][0]["instances"] *= 2
        with self.assertRaises(ValueError):
            scope_report(document)

    def test_credentials_or_no_lab_records_rejected(self):
        document = fixture()
        document["site"][0]["alerts"][0]["instances"][0]["uri"] = "http://user:pass@localhost:3000/"
        with self.assertRaises(ContractError):
            scope_report(document)
        document = fixture()
        document["site"].pop(0)
        with self.assertRaises(ContractError):
            scope_report(document)

    def test_pack_has_exact_source_hash_blank_labels_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.json"
            target = Path(directory) / "pack"
            write_json(source, fixture())
            raw_hash = file_digest(source)
            provenance = write_pack(source, target, dataset_id="TEST-ONLY")
            dataset = read_json(target / "dataset.json")
            self.assertEqual(dataset["_meta"]["source_sha256"], file_digest(target / "a1-input.json"))
            self.assertEqual(file_digest(source), raw_hash)
            self.assertEqual(provenance["raw_zap_sha256"], raw_hash)
            self.assertFalse(provenance["human_labels_assigned"])
            self.assertFalse(provenance["ai_inference_performed"])
            with (target / "nhu-labels.blank.csv").open(encoding="utf-8", newline="") as stream:
                sheet = list(csv.DictReader(stream))
            self.assertEqual(len(sheet), 1)
            self.assertTrue(all(sheet[0][key] == "" for key in (
                "is_real", "priority", "reason", "evidence_ref", "elapsed_seconds")))
            with self.assertRaises(ContractError):
                write_pack(source, target, dataset_id="TEST-ONLY")

    def test_hung_export_inventory_and_checked_in_pack_match(self):
        source = ROOT / "alert/2026-10-14-ZAP-Report-.json"
        folder = ROOT / "Nhu/N2_gan_nhan/data/h1-20261014"
        rows, inventory = scope_report(read_json(source))
        self.assertEqual((inventory["raw_instance_count"], inventory["included_instance_count"],
                          inventory["excluded_instance_count"], inventory["included_site_alert_group_count"]),
                         (31, 29, 2, 13))
        self.assertEqual(inventory["risk_counts"], {"High": 2, "Medium": 7, "Low": 10, "Informational": 10})
        dataset = read_json(folder / "dataset.json")
        provenance = read_json(folder / "provenance.json")
        self.assertEqual(dataset["alerts"], rows)
        self.assertEqual(dataset["_meta"]["source_sha256"], file_digest(folder / "a1-input.json"))
        self.assertEqual(provenance["raw_zap_content_sha256"], digest(read_json(source)))
        self.assertEqual(provenance["normalizer_text_sha256"], text_file_digest(ROOT / "Lan/A1_ai_triage/parser.py"))
        self.assertEqual(provenance["redactor_text_sha256"], text_file_digest(ROOT / "Lan/A3a_ai_config/safety.py"))


if __name__ == "__main__":
    unittest.main()
