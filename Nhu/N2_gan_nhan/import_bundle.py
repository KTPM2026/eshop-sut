"""Prepare a candidate N2/N3 pack from Lan's frozen Git bundle; never activate it or import peer labels."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

from ai.A1_ai_triage.parser import parse_alerts
from Nhu.check_handoff import git_bytes, resolve_ref
from Nhu.common import (SCHEMA_VERSION, digest, indexed_rows, require, valid_hash,
                        validate_dataset, write_json)
from .labels import create_sheet


BUNDLE = "ai/A1_ai_triage/review_bundle_v1"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_source(raw, expected):
    require(valid_hash(expected), "Missing original source hash in Lan manifest.")
    if sha(raw) == expected:
        return "exact_bytes"
    lf = raw.replace(b"\r\n", b"\n")
    require(expected in {sha(lf), sha(lf.replace(b"\n", b"\r\n"))},
            "Original source differs beyond Git line endings; refusing to import.")
    return "line_endings_only"


def write_candidate(alert_bytes, manifest, source_bytes, output, *, dataset_id, git_commit):
    output = Path(output)
    require(not output.exists(), "Use a new candidate output folder; never overwrite a locked dataset.")
    require(isinstance(manifest, dict) and manifest.get("status") == "frozen_input_pending_human_review",
            "Expected an unlabelled frozen input manifest.")
    files = manifest.get("files", {})
    require(isinstance(files, dict) and sha(alert_bytes) == files.get("alerts.json"),
            "Frozen alerts file does not match Lan's exact byte hash.")
    source_verification = verify_source(source_bytes, manifest.get("source_sha256"))
    document = json.loads(alert_bytes.decode("utf-8-sig"))
    require(isinstance(document, dict) and document.keys() == {"_meta", "alerts"} and
            isinstance(document.get("_meta"), dict),
            "Frozen alerts wrapper is missing metadata.")
    meta = document["_meta"]
    require(meta.keys() == {"data_origin", "origin", "model_inference_performed"} and
            meta.get("data_origin") == "real_zap_redacted" and
            meta.get("model_inference_performed") is False, "Not an unlabelled real ZAP handoff.")
    origin = manifest.get("origin")
    require(origin in {"http://localhost:3000", "http://localhost:5173"} and meta.get("origin") == origin,
            "Only the declared local EShop origin is allowed.")
    records = indexed_rows(document.get("alerts"))
    require(bool(records) and type(manifest.get("record_count")) is int and
            len(records) == manifest["record_count"] and
            manifest.get("alert_ids") == list(records), "Bundle IDs/count/order do not match its manifest.")
    require(parse_alerts(document, allowed_origins={origin}) == list(records.values()),
            "Current A1 parser does not preserve the frozen records exactly.")
    source = json.loads(source_bytes.decode("utf-8-sig"))
    require(parse_alerts(source, allowed_origins={origin}) == list(records.values()),
            "Frozen alerts no longer match their scoped original ZAP source.")
    canonical_hash = sha(alert_bytes)
    dataset = {
        "schema_version": SCHEMA_VERSION,
        "_meta": {"dataset_id": dataset_id, "data_origin": "real_zap", "source_sha256": canonical_hash,
                  "raw_zap_sha256": manifest["source_sha256"], "origin": origin},
        "alerts": list(records.values()),
    }
    validate_dataset(dataset)
    provenance = {
        **dataset["_meta"], "git_commit": git_commit, "bundle_path": BUNDLE,
        "upstream_manifest_content_sha256": digest(manifest),
        "source_path": manifest.get("source"), "observed_source_blob_sha256": sha(source_bytes),
        "source_verification": source_verification,
        "canonical_input": "a1-input.json", "canonical_bytes_preserved": True,
        "record_count": len(records), "scope_approved": False, "is_active_dataset": False,
        "human_labels_assigned": False, "ai_inference_performed": False,
        "notice": "CANDIDATE ONLY: agree with Phat/Lan before switching scope. "
                  "A1 source_sha256 is the exact frozen alerts file, NOT the original raw ZAP hash. "
                  "No review_phat.json, human verdicts or model output were imported. "
                  "Do not reuse locks/results from the 29-record pack for this 11-record candidate.",
    }
    output.mkdir(parents=True)
    with (output / "a1-input.json").open("xb") as stream:
        stream.write(alert_bytes)
    write_json(output / "dataset.json", dataset)
    write_json(output / "provenance.json", provenance)
    create_sheet(dataset, output / "nhu-labels.blank.csv")
    return provenance


def import_bundle(ref, output, *, dataset_id):
    commit = resolve_ref(ref)
    manifest = json.loads(git_bytes("show", f"{commit}:{BUNDLE}/manifest.json").decode("utf-8-sig"))
    source = PurePosixPath(manifest.get("source", ""))
    require(not source.is_absolute() and source.parts and source.parts[0] == "alert" and
            ".." not in source.parts and source.suffix == ".json", "Unexpected raw source location.")
    return write_candidate(
        git_bytes("show", f"{commit}:{BUNDLE}/alerts.json"), manifest,
        git_bytes("show", f"{commit}:{source.as_posix()}"), output,
        dataset_id=dataset_id, git_commit=commit,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="origin/feat(ai)/benchmark_offline")
    parser.add_argument("--dataset-id", default="lan-review-v1-api3000-candidate")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = import_bundle(args.ref, args.output_dir, dataset_id=args.dataset_id)
    except (OSError, ValueError, TypeError, KeyError):
        print("Cannot import: check ref, original source, exact hashes, IDs and a new output directory.")
        return 1
    print(f"candidate_records={report['record_count']}; scope_approved=False; human_labels=blank")
    print("A1 input sha256=" + report["source_sha256"])
    print("Existing pack/private labels unchanged. Agree on scope before using this candidate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
