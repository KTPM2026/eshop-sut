"""Không tự sinh nhãn; không đọc file kết quả AI trong quy trình N2."""

import argparse
import csv
from pathlib import Path
import sys

from Nhu.common import (ContractError, PRIORITIES, SCHEMA_VERSION, file_digest,
                        indexed_rows, nonempty, read_json, require, seconds,
                        utc_now, valid_hash, validate_dataset, write_json)


COLUMNS = ("alert_id", "risk", "is_real", "priority", "reason", "evidence_ref", "elapsed_seconds")


def create_sheet(dataset, output):
    records = validate_dataset(dataset)
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        for row in records.values():
            writer.writerow({"alert_id": row["alert_id"], "risk": row["risk"]})
    return len(records)


def read_sheet(path, dataset):
    records = validate_dataset(dataset)
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        require(tuple(reader.fieldnames or ()) == COLUMNS, "Header phiếu nhãn không đúng hợp đồng.")
        rows = list(reader)
    labels = indexed_rows(rows)
    require(labels.keys() == records.keys(), "Phiếu nhãn thiếu/thừa ID so với dataset.")
    normalized = {}
    for item_id, row in labels.items():
        require(set(row) == set(COLUMNS), "Phiếu có cột thừa/thiếu.")
        require(row["risk"] == records[item_id]["risk"], "Risk khác dataset đã khóa.")
        require(row["is_real"] in ("true", "false", "unknown"),
                "Người gán nhãn phải điền true/false/unknown; ô trống chưa phải nhãn.")
        label = {"true": True, "false": False, "unknown": None}[row["is_real"]]
        require(row["priority"] in PRIORITIES or (label is None and row["priority"] == ""),
                "Nhãn đã kết luận cần P1–P4; unknown có thể để priority trống.")
        require(nonempty(row["reason"]) and nonempty(row["evidence_ref"]),
                "Mỗi nhãn cần lý do và tham chiếu bằng chứng, kể cả chưa đủ bằng chứng.")
        try:
            duration = seconds(float(row["elapsed_seconds"]))
        except (ValueError, TypeError):
            raise ContractError("Cần thời gian đã đo cho từng alert, không tự điền 0.") from None
        normalized[item_id] = {
            "alert_id": item_id, "is_real": label, "priority": row["priority"] or None,
            "reason": row["reason"], "evidence_ref": row["evidence_ref"], "elapsed_seconds": duration,
        }
    return normalized


def lock_sheet(dataset, sheet_path, output, *, reviewer, confirmed_independent=False):
    require(nonempty(reviewer), "Cần danh tính người thực sự gán nhãn.")
    require(confirmed_independent is True,
            "Người gán nhãn cần xác nhận chưa xem P2/kết quả AI trước khi khóa.")
    labels = read_sheet(sheet_path, dataset)
    document = {
        "schema_version": SCHEMA_VERSION,
        "_meta": {
            "dataset_id": dataset["_meta"]["dataset_id"],
            "source_sha256": dataset["_meta"]["source_sha256"],
            "data_origin": dataset["_meta"]["data_origin"],
            "reviewer": reviewer, "locked_at_utc": utc_now(),
            "label_csv_sha256": file_digest(sheet_path),
            "independence_declared_by_user": True,
            "notice": "Hash ghi nhận phiên bản phiếu, không chứng minh độc lập hay tính đúng của nhãn.",
        },
        "labels": list(labels.values()),
    }
    write_json(output, document)
    return document


def compare_locks(first, second):
    """Chỉ đối chiếu sau khi khóa cả hai; không tự chốt nhãn chuẩn."""
    for document in (first, second):
        require(isinstance(document, dict) and document.get("schema_version") == SCHEMA_VERSION and
                isinstance(document.get("_meta"), dict),
                "Cần hai bản khóa nhãn.")
        meta = document["_meta"]
        require(meta.get("independence_declared_by_user") is True,
                "Thiếu xác nhận độc lập từ người gán nhãn.")
        require(nonempty(meta.get("dataset_id")) and valid_hash(meta.get("source_sha256")) and
                valid_hash(meta.get("label_csv_sha256")), "Bản khóa thiếu hash/nguồn.")
        for row in indexed_rows(document.get("labels")).values():
            require("is_real" in row and (type(row["is_real"]) is bool or row["is_real"] is None),
                    "Bản khóa có nhãn sai kiểu.")
            require(row.get("priority") in PRIORITIES or
                    (row["is_real"] is None and row.get("priority") is None),
                    "Bản khóa có priority không hợp lệ.")
            require(nonempty(row.get("reason")) and nonempty(row.get("evidence_ref")),
                    "Bản khóa thiếu lý do/bằng chứng.")
            seconds(row.get("elapsed_seconds"))
    meta1, meta2 = first["_meta"], second["_meta"]
    require(nonempty(meta1.get("reviewer")) and nonempty(meta2.get("reviewer")) and
            meta1["reviewer"].casefold() != meta2["reviewer"].casefold(),
            "Cần hai người gán nhãn khác nhau.")
    for key in ("dataset_id", "source_sha256", "data_origin"):
        require(meta1.get(key) == meta2.get(key), "Hai phiếu không cùng dataset/nguồn.")
    left, right = indexed_rows(first.get("labels")), indexed_rows(second.get("labels"))
    require(left.keys() == right.keys() and bool(left), "Hai phiếu không cùng tập ID.")
    disagreements = []
    class_matches = priority_matches = 0
    for item_id in left:
        a, b = left[item_id], right[item_id]
        class_matches += a["is_real"] == b["is_real"]
        priority_matches += a["priority"] == b["priority"]
        if (a["is_real"], a["priority"]) != (b["is_real"], b["priority"]):
            disagreements.append({"alert_id": item_id, "first": a, "second": b})
    return {
        "status": "pending_human_adjudication", "is_ground_truth": False,
        "dataset_id": meta1["dataset_id"], "record_count": len(left),
        "classification_agreement": class_matches / len(left),
        "priority_agreement": priority_matches / len(left),
        "notice": "Độ đồng thuận có tính cả unknown; không phải độ đúng của nhãn.",
        "disagreements": disagreements,
    }


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--dataset", type=Path, required=True)
    prepare.add_argument("--output", type=Path, required=True)
    lock = commands.add_parser("lock")
    lock.add_argument("--dataset", type=Path, required=True)
    lock.add_argument("--sheet", type=Path, required=True)
    lock.add_argument("--output", type=Path, required=True)
    lock.add_argument("--reviewer", required=True)
    lock.add_argument("--confirm-independent", action="store_true")
    compare = commands.add_parser("compare")
    compare.add_argument("--first", type=Path, required=True)
    compare.add_argument("--second", type=Path, required=True)
    compare.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            count = create_sheet(read_json(args.dataset), args.output)
            print(f"Tạo {count} dòng TRỐNG; chưa gán nhãn hay đo thời gian.")
        elif args.command == "lock":
            lock_sheet(read_json(args.dataset), args.sheet, args.output,
                       reviewer=args.reviewer, confirmed_independent=args.confirm_independent)
            print("Đã khóa bản phiếu do người gán nhãn cung cấp; chưa phải nhãn chuẩn chung.")
        else:
            write_json(args.output, compare_locks(read_json(args.first), read_json(args.second)))
            print("Đã lập danh sách bất đồng; Như/Phát tự kiểm chứng và chốt.")
    except (OSError, ValueError, TypeError, KeyError):
        print("Không hoàn tất: kiểm tra hợp đồng/đường dẫn, phiếu hoặc xác nhận độc lập; không có dữ liệu thay thế.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
