"""Chỉ xuất log template. Chạy benchmark thật bị chặn cho tới khi có H3/L2."""

import argparse
import csv
import json
import sys
from pathlib import Path


# [TỰ ĐỀ XUẤT - CẦN NHÓM CHỐT] Theo ngân sách gợi ý trong proposal, không phải kết quả đo.
DEFAULT_BUDGET = 50
BRANCHES = ("wordlist_static", "ai_static", "ai_feedback")
LOG_COLUMNS = ("branch", "attempt_no", "payload", "response_code", "bypass", "note")
ASSUMPTION_NOTICE = "TỰ ĐỀ XUẤT - CẦN NHÓM CHỐT"


class DependencyBlockedError(RuntimeError):
    """Chưa có giao diện bộ lọc H3/Fuzzer L2 và checkpoint đã được nhóm duyệt."""


def run_branch(branch_name, payload_source, filter_endpoint, budget=DEFAULT_BUDGET):
    """Khung giao diện A2; hiện không kết nối endpoint và không tiêu thụ payload.

    [TỰ ĐỀ XUẤT - CẦN NHÓM CHỐT] bypass = status không thuộc {400,403}
    VÀ checkpoint xác nhận hiệu ứng mong đợi. Status khác 400/403 một mình
    không đủ: lỗi 500, redirect, timeout hoặc response không rõ phải xác minh.
    Cách xác định blocked/hiệu ứng cuối cùng chờ Hùng/Long/Như/Phát thống nhất.
    """
    if branch_name not in BRANCHES:
        raise ValueError("Nhánh benchmark không hợp lệ.")
    if type(budget) is not int or budget <= 0:
        raise ValueError("budget phải là số nguyên dương.")
    raise DependencyBlockedError(
        "BLOCK: chờ H3 (bộ lọc), L2 (Fuzzer) và checkpoint được Như/Phát rà soát; chưa gửi request."
    )


def write_log_template(output_dir: Path) -> tuple[Path, Path]:
    """Tạo log RỖNG có metadata, không ghi số liệu benchmark giả."""
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "benchmark_template.csv"
    json_path = output_dir / "benchmark_template.json"
    for target in (csv_path, json_path):
        if target.exists():
            raise FileExistsError("Không ghi đè log đang có.")
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        csv.writer(stream).writerow(LOG_COLUMNS)
    json_path.write_text(json.dumps({
        "status": "blocked",
        "is_benchmark_result": False,
        "request_count": 0,
        "assumption_notice": ASSUMPTION_NOTICE,
        "budget_proposed": DEFAULT_BUDGET,
        "columns": list(LOG_COLUMNS),
        "rows": [],
        "waiting_for": ["H3", "L2", "checkpoint_review"],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return csv_path, json_path


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-template", type=Path, required=True)
    args = parser.parse_args()
    try:
        paths = write_log_template(args.write_template)
    except OSError:
        print("Không ghi template: đường dẫn không hợp lệ hoặc file đã tồn tại.")
        return 1
    print("BLOCK H3/L2: chỉ tạo template rỗng, KHÔNG chạy benchmark.")
    for file in paths:
        print(file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
