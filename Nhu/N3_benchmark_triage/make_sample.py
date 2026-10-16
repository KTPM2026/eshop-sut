"""Sinh bộ fixture TỰ TẠO, không gọi A1/AI, không tạo nhãn của Như/Phát."""

import argparse
from copy import deepcopy
from pathlib import Path
import sys

from Nhu.common import SCHEMA_VERSION, read_json, require, write_json


def sample_pack():
    dataset = read_json(Path(__file__).with_name("sample_dataset.json"))
    # Chỉ là giá trị test công thức TP/FP/FN/abstain, không phải nhãn do người gán.
    actuals = [(True, "P1"), (False, "P4"), (True, "P2"),
               (True, "P1"), (None, None), (False, "P3")]
    proposals = [(True, "P1"), (True, "P2"), (False, "P4"),
                 (None, "P4"), (False, "P4"), (False, "P3")]
    truth = {
        "schema_version": SCHEMA_VERSION,
        "_meta": {**dataset["_meta"], "review_status": "synthetic_fixture",
                  "human_adjudication_confirmed": False, "reviewers": [],
                  "independent_lock_sha256": []},
        "labels": [
            {"alert_id": row["alert_id"], "is_real": label, "priority": priority,
             "reason": "SYNTHETIC TEST FIXTURE, NOT HUMAN LABEL",
             "evidence_ref": "TEST FIXTURE ONLY"}
            for row, (label, priority) in zip(dataset["alerts"], actuals)
        ],
    }
    runs = []
    for index in range(3):
        result = {
            "schema_version": "lan-ai-v1-proposed",
            "_meta": {
                "data_origin": "synthetic", "execution_mode": "mock",
                "source_sha256": dataset["_meta"]["source_sha256"],
                "created_at_utc": f"2000-01-01T00:00:0{index}+00:00",
                "is_replay": False, "model_inference_performed": False,
                "review_required": True, "record_count": len(proposals),
                "final_decision": "pending_human_review", "is_benchmark_result": False,
                "config": {"provider": "test-fixture", "model": "NOT-A-REAL-MODEL",
                           "base_url": "https://example.invalid",
                           "temperature": 0, "max_completion_tokens": 1200,
                           "timeout_seconds": 30, "group_approved": False},
                "notice": "NOT A1 EXECUTION; hand-built SDK-shape fixture, no real model calls.",
            },
            "results": [
                {"alert_id": row["alert_id"], "is_real": label, "priority": priority,
                 "reason": "SYNTHETIC TEST ONLY", "confidence": 0.0,
                 "trang_thai_bang_chung": "can_xac_minh"}
                for row, (label, priority) in zip(dataset["alerts"], proposals)
            ],
        }
        runs.append({"run_id": f"synthetic-{index + 1}", "result": result,
                     "inference_seconds": 5, "review_seconds": 10, "review_completed": True})
    return deepcopy((dataset, truth, runs))


def write_sample(directory):
    directory = Path(directory)
    require(not directory.exists(), "Thư mục sample phải mới để tránh ghi đè dữ liệu.")
    dataset, truth, runs = sample_pack()
    write_json(directory / "dataset.json", dataset)
    write_json(directory / "truth_fixture.json", truth)
    manifest = {
        "schema_version": SCHEMA_VERSION, "protocol_approved": False,
        "dataset_path": "dataset.json", "ground_truth_path": "truth_fixture.json",
        "manual_total_seconds": 60,
        "notice": "ALL TIMINGS/LABELS/RESULTS ARE SYNTHETIC TEST VALUES, NOT MEASURED.",
        "runs": [],
    }
    for index, run in enumerate(runs, 1):
        name = f"a1_fixture_{index}.json"
        write_json(directory / name, run["result"])
        manifest["runs"].append({key: value for key, value in run.items() if key != "result"} |
                                {"result_path": name})
    write_json(directory / "manifest.json", manifest)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("Nhu/outputs/sample-input"))
    args = parser.parse_args()
    try:
        write_sample(args.output_dir)
    except (OSError, ValueError, TypeError):
        print("Không tạo sample: đường dẫn đã có hoặc dữ liệu không hợp lệ.")
        return 1
    print("Đã tạo FIXTURE TỰ TẠO; không có scan, inference, nhãn người hay thời gian đo thật.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
