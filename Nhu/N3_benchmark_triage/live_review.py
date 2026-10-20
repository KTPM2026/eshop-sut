"""Compare archived live A1 outputs with an explicitly non-independent reference."""

import argparse
from collections import Counter
from copy import deepcopy
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from ai.A3a_ai_config.client import TRIAGE_SYSTEM
from ai.A3a_ai_config.contracts import TriageSuggestion
from ai.A3a_ai_config.safety import redact
from Nhu.common import (ID_PATTERN, digest, indexed_rows, read_json, require, seconds, utc_now,
                        validate_dataset, write_json)
from Nhu.N2_gan_nhan.import_bundle import BUNDLE, git_bytes, import_bundle, resolve_ref
from .run import METRIC_COLUMNS
from .scoring import RISK_BASELINE, score_predictions, summarize, validate_result


SOURCE_COMMIT = "9fd85126f44a0b323c3b6b475a248bd409272c18"
RUN_PATHS = [f"ai/A1_ai_triage/results/live_2026-10-20_run{i}.json" for i in range(1, 4)]
ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "Nhu/N2_gan_nhan/assisted-review/nhu-review.json"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def compare(dataset, input_raw, reference, runs, *, accept_assisted=False):
    require(accept_assisted is True, "Explicit acceptance of a non-independent reference is required.")
    alerts = validate_dataset(dataset)
    require(dataset["_meta"]["data_origin"] == "real_zap", "A real source dataset is required.")
    require(indexed_rows(json.loads(input_raw.decode("utf-8-sig")).get("alerts")) == alerts,
            "Input content differs from the projected dataset.")
    original = indexed_rows(reference.get("labels"))
    meta = reference.get("_meta", {})
    require(meta.get("is_ground_truth") is False and meta.get("independent_human_review") is False,
            "This comparison only accepts an explicitly assisted, non-ground-truth reference.")
    require(meta.get("raw_zap_sha256") == dataset["_meta"].get("raw_zap_sha256"),
            "Reference and live input must share the original ZAP source.")
    require(alerts.keys() <= original.keys(), "Reference does not cover every live input ID.")
    labels = [deepcopy(original[item_id]) for item_id in alerts]
    for row in labels:
        require(row.get("risk") == alerts[row["alert_id"]]["risk"], "Reference risk/source mismatch.")
        require(type(row.get("is_real")) is bool or row.get("is_real") is None,
                "Invalid assisted reference label.")
        require(row.get("priority") in ("P1", "P2", "P3", "P4") or
                (row["is_real"] is None and row.get("priority") is None), "Invalid reference priority.")
        require(bool(row.get("reason")) and bool(row.get("evidence_ref")), "Missing reference evidence.")
        require(row.get("independent_human_review") is False and row.get("human_approved") is False and
                row.get("human_elapsed_seconds") is None, "Do not invent human review or timing.")
    # Preserve original run hashes: only recognize the two verified LF/CRLF byte variants.
    lf = input_raw.replace(b"\r\n", b"\n")
    variants = {"lf": sha(lf), "crlf": sha(lf.replace(b"\n", b"\r\n"))}
    require(dataset["_meta"]["source_sha256"] == sha(input_raw), "Archived input hash mismatch.")
    require(len(runs) >= 3, "At least three live runs are required.")
    expected_prompt = sha(TRIAGE_SYSTEM.encode())
    expected_schema = sha(json.dumps(TriageSuggestion.model_json_schema(), sort_keys=True).encode())
    seen_ids, seen_dates, seen_responses = set(), set(), set()
    config, reports = None, []
    for document in runs:
        require(redact(document) == document, "Live artifact contains unredacted sensitive fields.")
        run_meta = document.get("_meta", {})
        require(run_meta.get("source_sha256") in variants.values(), "Unrecognized live input bytes.")
        run_dataset = deepcopy(dataset)
        run_dataset["_meta"]["source_sha256"] = run_meta["source_sha256"]
        predictions = validate_result(document, run_dataset, synthetic=False)
        require(run_meta.get("status") == "completed", "Incomplete live run.")
        require(run_meta.get("prompt_sha256") == expected_prompt and
                run_meta.get("schema_sha256") == expected_schema, "Prompt/schema provenance mismatch.")
        require(run_meta.get("alert_ids") == list(alerts), "Live input inventory/order mismatch.")
        run_id = run_meta.get("run_id")
        require(isinstance(run_id, str) and ID_PATTERN.fullmatch(run_id) and run_id not in seen_ids,
                "Invalid or repeated run ID.")
        created = datetime.fromisoformat(run_meta["created_at_utc"])
        updated = datetime.fromisoformat(run_meta["updated_at_utc"])
        require(updated.tzinfo is not None and updated >= created and created not in seen_dates,
                "Invalid or repeated live run timestamps.")
        seen_ids.add(run_id)
        seen_dates.add(created)
        require(config is None or config == run_meta["config"], "Runs must share one configuration.")
        config = run_meta["config"]
        attempts = document.get("attempts")
        require(isinstance(attempts, list) and attempts, "Missing provider attempt records.")
        successes, failures, latency, tokens, missing_usage, response_ids = 0, 0, 0.0, 0, 0, []
        success_alerts = []
        for attempt in attempts:
            require(attempt.get("alert_id") in alerts and attempt.get("status") in ("success", "error"),
                    "Invalid provider attempt.")
            if attempt["status"] == "success":
                success_alerts.append(attempt["alert_id"])
            calls = attempt.get("api_calls")
            require(isinstance(calls, list) and calls, "Attempt has no API call provenance.")
            for call in calls:
                require(call.get("status") in ("success", "error"), "Invalid API call status.")
                latency += seconds(call.get("latency_ms")) / 1000
                if call["status"] == "success":
                    successes += 1
                    response_id = call.get("response_id")
                    require(isinstance(response_id, str) and response_id and response_id not in seen_responses,
                            "Missing/reused successful provider response ID.")
                    seen_responses.add(response_id)
                    response_ids.append(response_id)
                else:
                    failures += 1
                usage = call.get("usage")
                if usage is None:
                    missing_usage += 1
                else:
                    require(isinstance(usage, dict) and type(usage.get("total_tokens")) is int and
                            usage["total_tokens"] >= 0, "Invalid token usage.")
                    tokens += usage["total_tokens"]
        require(len(success_alerts) == len(alerts) and set(success_alerts) == set(alerts) and
                successes == len(alerts), "Successful calls must cover each input exactly once.")
        comparisons = []
        for label in labels:
            predicted = predictions[label["alert_id"]]
            known = label["is_real"] is not None
            comparisons.append({
                "alert_id": label["alert_id"], "reference_is_real": label["is_real"],
                "reference_priority": label["priority"], "ai_is_real": predicted["is_real"],
                "ai_priority": predicted["priority"],
                "classification_agrees": predicted["is_real"] == label["is_real"] if known else None,
                "priority_agrees": predicted["priority"] == label["priority"] if known else None,
            })
        reports.append({
            "run_id": run_id, "result_content_sha256": digest(document),
            "source_sha256_reported_by_run": run_meta["source_sha256"],
            "created_at_utc": run_meta["created_at_utc"], "updated_at_utc": run_meta["updated_at_utc"],
            "conditional_metrics_against_assisted_reference": score_predictions(labels, list(predictions.values())),
            "comparisons": comparisons, "api_calls": successes + failures,
            "successful_calls": successes, "failed_calls": failures, "response_ids": response_ids,
            "reported_tokens": tokens, "calls_without_usage": missing_usage,
            "prediction_counts": dict(Counter("unknown" if r["is_real"] is None else
                                               str(r["is_real"]).lower() for r in predictions.values())),
            "priority_counts": dict(Counter(r["priority"] for r in predictions.values())),
            "timing": {"api_latency_seconds": round(latency, 6),
                       "first_to_last_checkpoint_seconds": (updated - created).total_seconds(),
                       "pipeline_seconds": None, "human_review_seconds": None,
                       "manual_total_seconds": None, "time_saved_fraction": None,
                       "notice": "API latency excludes throttling/I-O; checkpoint span can include resume pauses. Neither is human timing or a measured complete pipeline."},
        })
    baseline = [{"alert_id": key, "is_real": RISK_BASELINE[row["risk"]][0],
                 "priority": RISK_BASELINE[row["risk"]][1]} for key, row in alerts.items()]
    return {
        "schema_version": "nhu-live-assisted-comparison-v1",
        "_meta": {"created_at_utc": utc_now(), "evaluation_mode": "non_independent_assisted_reference",
                  "live_outputs_observed": True, "is_synthetic": False, "is_benchmark_result": False,
                  "is_ground_truth": False, "independent_human_review": False,
                  "assisted_method_accepted_by_student": True,
                  "acceptance_source": "User confirmation in conversation on 2026-10-20",
                  "human_labels_verified": False, "human_adjudication_confirmed": False,
                  "human_timing_measured": False, "run_count": len(runs),
                  "notice": "Actual live artifacts compared with an AI-assisted reference, not adjudicated truth. Metrics are conditional agreement only, not independently validated vulnerability detection quality. No claim of time saving."},
        "dataset": {**dataset["_meta"], "records": len(alerts), "source_byte_variants": variants},
        "reference": {"source": "Nhu/N2_gan_nhan/assisted-review/nhu-review.json",
                      "source_content_sha256": digest(reference), "source_record_count": len(original),
                      "projected_record_count": len(labels), "labels": labels,
                      "independent_human_review": False, "is_ground_truth": False,
                      "counts": dict(Counter("unknown" if r["is_real"] is None else
                                             str(r["is_real"]).lower() for r in labels))},
        "config": config, "baseline_risk_against_assisted_reference": score_predictions(labels, baseline),
        "runs": reports,
        "summary": {key: summarize([r["conditional_metrics_against_assisted_reference"][key] for r in reports])
                    for key in ("precision", "recall", "f1", "accuracy", "classification_coverage", "priority_accuracy")},
    }


def export(ref, output, reference_path=REFERENCE, *, accept_assisted=False):
    target = Path(output)
    require(not target.exists(), "Use a new output directory; never overwrite archived evidence.")
    commit = resolve_ref(ref)
    with TemporaryDirectory(prefix="nhu-live-input-") as temporary:
        pack = Path(temporary) / "input"
        import_bundle(commit, pack, dataset_id="lan-review-v1-api3000-live-comparison")
        dataset, raw = read_json(pack / "dataset.json"), (pack / "a1-input.json").read_bytes()
        blobs = {"input.json": (f"{BUNDLE}/alerts.json", raw)}
        for i, path in enumerate(RUN_PATHS, 1):
            blobs[f"run-{i}.json"] = (path, git_bytes("show", f"{commit}:{path}"))
        documents = [json.loads(blobs[f"run-{i}.json"][1].decode("utf-8-sig")) for i in range(1, 4)]
        report = compare(dataset, raw, read_json(reference_path), documents, accept_assisted=accept_assisted)
    report["provenance"] = {
        "source_commit": commit, "source_repository": "https://github.com/KTPM2026/eshop-sut",
        "source_pull_request": 5, "inference_reissued_by_this_tool": False,
        "archive_files": [{"file": name, "upstream_path": path, "sha256": sha(content)}
                          for name, (path, content) in blobs.items()],
    }
    write_json(target / "comparison.json", report)
    for name, (_, content) in blobs.items():
        with (target / name).open("xb") as stream:
            stream.write(content)
    fields = ("run_id", "evaluation_mode", "is_benchmark_result", *METRIC_COLUMNS,
              "api_latency_seconds", "human_review_seconds", "time_saved_fraction")
    with (target / "comparison.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for run in report["runs"]:
            writer.writerow({"run_id": run["run_id"], "evaluation_mode": report["_meta"]["evaluation_mode"],
                             "is_benchmark_result": False,
                             **{k: run["conditional_metrics_against_assisted_reference"][k] for k in METRIC_COLUMNS},
                             **{k: run["timing"][k] for k in fields[-3:]}})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default=SOURCE_COMMIT)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--accept-assisted-reference", action="store_true")
    args = parser.parse_args()
    try:
        report = export(args.ref, args.output_dir, accept_assisted=args.accept_assisted_reference)
    except (OSError, ValueError, TypeError, KeyError):
        print("Cannot compare: check frozen input, reference, live metadata and a new output path.")
        return 1
    print(f"live_runs={report['_meta']['run_count']}; reference=AI-assisted; independent_benchmark=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
