"""Hợp đồng dữ liệu N2/N3 đề xuất; không phân loại alert hay gọi AI."""

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
import re


SCHEMA_VERSION = "nhu-benchmark-v1-proposed"
PRIORITIES = ("P1", "P2", "P3", "P4")
RISKS = ("High", "Medium", "Low", "Informational", "Unknown")
ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,199}")
HASH_PATTERN = re.compile(r"[a-f0-9]{64}")


class ContractError(ValueError):
    """Lỗi hợp đồng, chỉ chứa mô tả an toàn, không chứa nội dung alert."""


def require(condition, message):
    if not condition:
        raise ContractError(message)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False).encode("utf-8")).hexdigest()


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text_file_digest(path):
    """Compare source text across Git checkouts without CRLF/LF differences."""
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def write_json(path, document):
    """Không ghi đè input/kết quả cũ; output sinh bởi chương trình."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    with target.open("x", encoding="utf-8") as stream:
        stream.write(content)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def valid_hash(value):
    return isinstance(value, str) and HASH_PATTERN.fullmatch(value) is not None


def seconds(value, *, nullable=False):
    if value is None and nullable:
        return None
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0,
            "Thời gian phải là số giây hữu hạn không âm, hoặc null khi chưa đo.")
    return float(value)


def indexed_rows(rows):
    require(isinstance(rows, list), "Cần danh sách record.")
    result = {}
    for row in rows:
        require(isinstance(row, dict), "Mỗi record phải là object.")
        item_id = row.get("alert_id")
        require(isinstance(item_id, str) and ID_PATTERN.fullmatch(item_id),
                "alert_id phải ổn định, không rỗng và chỉ dùng ký tự ID cho phép.")
        require(item_id not in result, "Có alert_id trùng; không tự loại trùng.")
        result[item_id] = row
    return result


def validate_dataset(document):
    require(isinstance(document, dict), "Dataset phải là object.")
    require(document.get("schema_version") == SCHEMA_VERSION, "Sai phiên bản dataset.")
    meta = document.get("_meta")
    require(isinstance(meta, dict), "Dataset thiếu metadata.")
    require(nonempty(meta.get("dataset_id")), "Thiếu dataset_id.")
    require(meta.get("data_origin") in ("synthetic", "real_zap"), "Nguồn dataset không hợp lệ.")
    require(valid_hash(meta.get("source_sha256")), "Thiếu SHA256 của input H1/A1.")
    records = indexed_rows(document.get("alerts"))
    require(bool(records), "Dataset rỗng không dùng để gán nhãn/chấm điểm.")
    for row in records.values():
        require(row.get("risk") in RISKS, "Risk chưa chuẩn hóa.")
        require(not {"is_real", "priority", "trang_thai_bang_chung"} & row.keys(),
                "Dataset gán nhãn không được chứa nhãn/kết quả AI.")
    return records
