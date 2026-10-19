"""Bộ chấm offline. Quy ước mẫu số/baseline là TỰ ĐỀ XUẤT - CẦN NHÓM CHỐT."""

import math
from datetime import datetime, timezone
import statistics
from urllib.parse import urlsplit

from Nhu.common import (ID_PATTERN, PRIORITIES, SCHEMA_VERSION, digest, indexed_rows, nonempty,
                        require, seconds, utc_now, valid_hash, validate_dataset)


OUTPUT_FIELDS = {"alert_id", "is_real", "priority", "reason", "confidence", "trang_thai_bang_chung"}
EVIDENCE_STATES = {"can_xac_minh", "co_bang_chung_ho_tro", "khong_du_bang_chung"}
CONFIG_FIELDS = {"provider", "model", "base_url", "temperature", "max_completion_tokens",
                 "timeout_seconds", "group_approved"}
# [TỰ ĐỀ XUẤT - CẦN NHÓM CHỐT] Baseline cố định trước khi xem kết quả.
RISK_BASELINE = {
    "High": (True, "P1"), "Medium": (True, "P2"), "Low": (False, "P3"),
    "Informational": (False, "P4"), "Unknown": (None, "P3"),
}


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def score_predictions(truth_rows, predictions):
    """Recall tính cả AI abstain trên lỗi thật là chưa nhận diện, không loại để nâng điểm."""
    truth, predicted = indexed_rows(truth_rows), indexed_rows(predictions)
    require(truth.keys() == predicted.keys(), "Kết quả thiếu/thừa ID; không được bỏ alert.")
    known = {key: row for key, row in truth.items() if row["is_real"] is not None}
    tp = fp = tn = fn = abstain_positive = abstain_negative = priority_matches = 0
    false_ids, p4_ids, low_ids, abstain_ids = [], [], [], []
    for item_id, actual in known.items():
        proposed = predicted[item_id]
        label = proposed["is_real"]
        if label is None:
            if actual["is_real"]:
                abstain_positive += 1
                abstain_ids.append(item_id)
            else:
                abstain_negative += 1
        elif label is True and actual["is_real"] is True:
            tp += 1
        elif label is True:
            fp += 1
        elif actual["is_real"] is True:
            fn += 1
            false_ids.append(item_id)
        else:
            tn += 1
        priority_matches += proposed["priority"] == actual["priority"]
        if actual["is_real"] is True:
            if proposed["priority"] == "P4":
                p4_ids.append(item_id)
            if actual["priority"] in ("P1", "P2") and proposed["priority"] in ("P3", "P4"):
                low_ids.append(item_id)
    total_positive = tp + fn + abstain_positive
    return {
        "total_records": len(truth), "scored_records": len(known),
        "excluded_unresolved_truth": len(truth) - len(known),
        "tp": tp, "fp": fp, "tn": tn, "fn_explicit_false": fn,
        "abstain_on_true": abstain_positive, "abstain_on_false": abstain_negative,
        "precision": ratio(tp, tp + fp),
        "recall": ratio(tp, total_positive),
        "f1": ratio(2 * tp, 2 * tp + fp + fn + abstain_positive),
        "accuracy": ratio(tp + tn, len(known)),
        "classification_coverage": ratio(tp + fp + tn + fn, len(known)),
        "priority_accuracy": ratio(priority_matches, len(known)),
        "priority_matches": priority_matches,
        "true_labeled_false": len(false_ids), "true_assigned_P4": len(p4_ids),
        "true_labeled_false_or_P4": len(set(false_ids) | set(p4_ids)),
        "true_downgraded_from_P1_P2_to_P3_P4": len(low_ids),
        "safety_alert_ids": {"false": false_ids, "P4": p4_ids,
                             "downgraded_to_low": low_ids, "abstain": abstain_ids},
        "notice": "Mẫu số 0 là null. Recall/F1 tính abstain trên lỗi thật là bỏ sót; "
                  "Accuracy tính mọi abstain là chưa đúng, không loại khỏi mẫu số.",
    }


def validate_truth(document, dataset, *, synthetic):
    require(isinstance(document, dict) and document.get("schema_version") == SCHEMA_VERSION,
            "Sai hợp đồng nhãn chuẩn.")
    meta = document.get("_meta", {})
    require(isinstance(meta, dict), "Thiếu metadata nhãn chuẩn.")
    for key in ("dataset_id", "source_sha256", "data_origin"):
        require(meta.get(key) == dataset["_meta"][key], "Nhãn chuẩn không khớp dataset/nguồn.")
    if not synthetic:
        require(meta.get("review_status") == "adjudicated" and
                meta.get("human_adjudication_confirmed") is True,
                "Chờ Như/Phát chốt nhãn; không dùng nhãn draft làm ground truth.")
        reviewers = meta.get("reviewers")
        require(isinstance(reviewers, list) and len(reviewers) == 2 and
                all(nonempty(name) for name in reviewers) and
                reviewers[0].casefold() != reviewers[1].casefold(),
                "Nhãn chuẩn cần hai người review độc lập khác nhau.")
        locks = meta.get("independent_lock_sha256")
        require(isinstance(locks, list) and len(locks) == 2 and all(valid_hash(item) for item in locks),
                "Thiếu hash hai bản khóa nhãn độc lập.")
    records = indexed_rows(document.get("labels"))
    require(records.keys() == validate_dataset(dataset).keys(), "Nhãn chuẩn thiếu/thừa ID.")
    for row in records.values():
        require(type(row.get("is_real")) is bool or row.get("is_real") is None,
                "is_real của nhãn chuẩn phải là boolean hoặc null.")
        require("is_real" in row, "Thiếu trường is_real.")
        require(row.get("priority") in PRIORITIES or
                (row["is_real"] is None and row.get("priority") is None),
                "Priority nhãn đã chốt phải thuộc P1–P4.")
        require(nonempty(row.get("reason")) and nonempty(row.get("evidence_ref")),
                "Nhãn chuẩn cần lý do và bằng chứng.")
    return records


def validate_result(document, dataset, *, synthetic):
    require(isinstance(document, dict) and document.get("schema_version") == "lan-ai-v1-proposed",
            "Kết quả A1 không đúng schema đã bàn giao.")
    meta = document.get("_meta", {})
    require(isinstance(meta, dict), "Thiếu metadata A1.")
    require(meta.get("source_sha256") == dataset["_meta"]["source_sha256"],
            "Hash nguồn A1 khác input H1 đã khóa.")
    require(meta.get("is_replay") is False, "Không tính replay thành lượt benchmark mới.")
    require(meta.get("review_required") is True, "A1 phải giữ yêu cầu người review.")
    require(nonempty(meta.get("created_at_utc")), "Thiếu thời điểm lượt A1.")
    try:
        timestamp = datetime.fromisoformat(meta["created_at_utc"])
        require(timestamp.tzinfo is not None, "Thời điểm lượt A1 cần timezone.")
    except ValueError:
        require(False, "Thời điểm lượt A1 không hợp lệ.")
    config = meta.get("config", {})
    require(isinstance(config, dict) and config.keys() == CONFIG_FIELDS,
            "Cấu hình A1 thiếu trường hoặc có trường ngoài hợp đồng, có thể chứa secret.")
    require(nonempty(config.get("provider")) and nonempty(config.get("model")),
            "Thiếu provider/model cố định.")
    require(isinstance(config.get("base_url"), str), "Thiếu base URL cấu hình.")
    url = urlsplit(config["base_url"])
    require(url.scheme == "https" and bool(url.hostname) and
            not (url.username or url.password or url.query or url.fragment),
            "Base URL không được chứa thông tin đăng nhập/query/fragment.")
    for key in ("temperature", "timeout_seconds", "max_completion_tokens"):
        require(type(config.get(key)) in (int, float) and math.isfinite(config[key]),
                "Cấu hình số không hợp lệ.")
    require(0 <= config["temperature"] <= 2 and 0 < config["timeout_seconds"] <= 120 and
            type(config["max_completion_tokens"]) is int and 1 <= config["max_completion_tokens"] <= 16384 and
            type(config.get("group_approved")) is bool, "Cấu hình ngoài giới hạn A3a.")
    if not synthetic:
        require(meta.get("execution_mode") == "live" and
                meta.get("model_inference_performed") is True and
                meta.get("data_origin") in ("real_zap", "unverified_external") and
                config.get("group_approved") is True,
                "Chỉ nhận run AI thật được duyệt; mock/sample không phải benchmark.")
    rows = indexed_rows(document.get("results"))
    require(rows.keys() == validate_dataset(dataset).keys(), "A1 thiếu/thừa ID so với dataset.")
    require(type(meta.get("record_count")) is int and meta["record_count"] == len(rows),
            "record_count A1 không khớp kết quả.")
    for row in rows.values():
        require(row.keys() == OUTPUT_FIELDS, "A1 phải có đúng sáu trường, không có hành động đóng alert.")
        require(type(row["is_real"]) is bool or row["is_real"] is None, "is_real A1 sai kiểu.")
        require(row["priority"] in PRIORITIES, "A1 có priority không hợp lệ.")
        require(type(row["confidence"]) in (int, float) and math.isfinite(row["confidence"]) and
                0 <= row["confidence"] <= 1, "Confidence không hợp lệ.")
        require(nonempty(row["reason"]) and row["trang_thai_bang_chung"] in EVIDENCE_STATES,
                "A1 thiếu lý do/trạng thái bằng chứng.")
    return rows


def summarize(values):
    measured = [value for value in values if value is not None]
    return {"defined_runs": len(measured), "undefined_runs": len(values) - len(measured),
            "mean": statistics.mean(measured) if measured else None,
            "min": min(measured) if measured else None,
            "max": max(measured) if measured else None}


def evaluate_benchmark(dataset, ground_truth, runs, *, manual_total_seconds=None,
                       protocol_approved=False, allow_synthetic=False):
    """runs chứa result A1 + timing sidecar; không import/call module AI."""
    alerts = validate_dataset(dataset)
    synthetic = dataset["_meta"]["data_origin"] == "synthetic"
    require(not synthetic or allow_synthetic is True,
            "Mẫu tự tạo cần --allow-synthetic và không được trình bày là số liệu thật.")
    require(synthetic or protocol_approved is True, "Nhóm cần chốt protocol trước khi benchmark thật.")
    truth = validate_truth(ground_truth, dataset, synthetic=synthetic)
    require(isinstance(runs, list) and len(runs) >= 3, "Cần ít nhất ba lượt A1 độc lập.")
    manual = seconds(manual_total_seconds, nullable=True)
    run_ids, seen_runs, reports = set(), set(), []
    fixed_config = None
    for run in runs:
        require(isinstance(run, dict) and isinstance(run.get("run_id"), str) and
                ID_PATTERN.fullmatch(run["run_id"]), "run_id không hợp lệ.")
        require(run["run_id"] not in run_ids, "run_id trùng.")
        run_ids.add(run["run_id"])
        result = run.get("result")
        proposed = validate_result(result, dataset, synthetic=synthetic)
        config = result["_meta"]["config"]
        require(fixed_config is None or fixed_config == config, "Các lượt phải cùng model/cấu hình.")
        fixed_config = config
        identity = datetime.fromisoformat(result["_meta"]["created_at_utc"]).astimezone(timezone.utc).isoformat()
        require(identity not in seen_runs, "Cùng lượt A1 bị tính lặp; cache không phải lượt mới.")
        seen_runs.add(identity)
        inference = seconds(run.get("inference_seconds"), nullable=True)
        review = seconds(run.get("review_seconds"), nullable=True)
        reviewed = run.get("review_completed") is True
        require(synthetic or (reviewed and inference is not None and review is not None),
                "Benchmark thật phải có thời gian inference + review và xác nhận review.")
        total = inference + review if reviewed and inference is not None and review is not None else None
        metrics = score_predictions(list(truth.values()), list(proposed.values()))
        reports.append({
            "run_id": run["run_id"], "result_sha256": digest(result),
            "metrics": metrics,
            "timing": {"inference_seconds": inference, "review_seconds": review,
                       "review_completed": reviewed, "total_seconds": total,
                       "manual_total_seconds": manual,
                       "time_saved_fraction": (manual - total) / manual
                       if manual and total is not None else None},
        })
    baseline = [{"alert_id": item_id, "is_real": RISK_BASELINE[row["risk"]][0],
                 "priority": RISK_BASELINE[row["risk"]][1]} for item_id, row in alerts.items()]
    return {
        "schema_version": SCHEMA_VERSION,
        "_meta": {
            "dataset_id": dataset["_meta"]["dataset_id"], "source_sha256": dataset["_meta"]["source_sha256"],
            "data_origin": dataset["_meta"]["data_origin"], "created_at_utc": utc_now(),
            "is_benchmark_result": not synthetic, "protocol_approved": protocol_approved,
            "is_replay": False, "run_count": len(reports),
            "dataset_sha256": digest(dataset), "ground_truth_sha256": digest(ground_truth),
            "notice": "MÔ PHỎNG, KHÔNG PHẢI SỐ LIỆU THẬT" if synthetic else
                      "Dữ liệu do nhóm cung cấp; kiểm tra metadata không chứng minh tính độc lập của nhãn.",
        },
        "protocol": {
            "status": "group_approved_by_input" if protocol_approved else "proposed_not_group_approved",
            "positive_class": "real_vulnerability", "abstention_in_recall_denominator": True,
            "f1_formula": "2*TP/(2*TP+FP+FN_explicit_false+abstain_on_true)",
            "accuracy_formula": "(TP+TN)/scored_records",
            "abstention_in_accuracy_denominator": True,
            "unresolved_truth_excluded_and_reported": True,
            "zero_denominator": None, "risk_baseline": RISK_BASELINE,
        },
        "config": fixed_config,
        "baseline_risk": score_predictions(list(truth.values()), baseline),
        "runs": reports,
        "summary": {
            **{key: summarize([report["metrics"][key] for report in reports])
               for key in ("precision", "recall", "f1", "accuracy", "priority_accuracy",
                           "classification_coverage")},
            "total_seconds": summarize([report["timing"]["total_seconds"] for report in reports]),
            "time_saved_fraction": summarize([report["timing"]["time_saved_fraction"] for report in reports]),
        },
    }
