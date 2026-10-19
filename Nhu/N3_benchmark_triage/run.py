"""Chấm offline manifest gồm dataset, nhãn đã chốt, ít nhất ba file A1 và timing."""

import argparse
import csv
from pathlib import Path
import sys

from Nhu.common import SCHEMA_VERSION, digest, read_json, require, write_json
from .scoring import evaluate_benchmark


METRIC_COLUMNS = ("precision", "recall", "f1", "accuracy", "classification_coverage",
                  "priority_accuracy", "true_labeled_false", "true_assigned_P4",
                  "true_labeled_false_or_P4", "excluded_unresolved_truth")
CSV_COLUMNS = ("run_id", "is_benchmark_result", *METRIC_COLUMNS,
               "total_seconds", "time_saved_fraction")


def evaluate_manifest(path, *, allow_synthetic=False):
    path = Path(path)
    manifest = read_json(path)
    require(isinstance(manifest, dict) and manifest.get("schema_version") == SCHEMA_VERSION,
            "Manifest cần đúng phiên bản hợp đồng.")
    base = path.parent
    dataset = read_json(base / manifest["dataset_path"])
    truth = read_json(base / manifest["ground_truth_path"])
    entries = manifest.get("runs")
    require(isinstance(entries, list), "Manifest thiếu runs.")
    runs = []
    for item in entries:
        require(isinstance(item, dict), "Mỗi run cần là object.")
        runs.append({**item, "result": read_json(base / item["result_path"])})
    report = evaluate_benchmark(
        dataset, truth, runs, manual_total_seconds=manifest.get("manual_total_seconds"),
        protocol_approved=manifest.get("protocol_approved") is True, allow_synthetic=allow_synthetic,
    )
    report["_meta"]["manifest_sha256"] = digest(manifest)
    return report


def write_report(report, output_dir):
    target = Path(output_dir)
    json_path, csv_path = target / "benchmark.json", target / "benchmark.csv"
    require(not json_path.exists() and not csv_path.exists(), "Không ghi đè báo cáo đang có.")
    write_json(json_path, report)
    with csv_path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for run in report["runs"]:
            writer.writerow({
                "run_id": run["run_id"], "is_benchmark_result": report["_meta"]["is_benchmark_result"],
                **{key: run["metrics"][key] for key in METRIC_COLUMNS},
                "total_seconds": run["timing"]["total_seconds"],
                "time_saved_fraction": run["timing"]["time_saved_fraction"],
            })


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--allow-synthetic", action="store_true")
    args = parser.parse_args()
    try:
        report = evaluate_manifest(args.manifest, allow_synthetic=args.allow_synthetic)
        write_report(report, args.output_dir)
    except (OSError, ValueError, TypeError, KeyError):
        print("Không chấm được: kiểm tra ID/hash/schema, nhãn, số lượt, replay, cấu hình và thời gian review.")
        return 1
    print(f"runs={report['_meta']['run_count']}; is_benchmark_result={report['_meta']['is_benchmark_result']}")
    print(report["_meta"]["notice"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
