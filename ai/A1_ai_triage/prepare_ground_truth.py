"""Create an unlabelled review sheet from the real EShop ZAP export."""

import argparse
import json
from pathlib import Path

from .parser import parse_alerts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--host", action="append")
    parser.add_argument("--origin", action="append", required=True)
    args = parser.parse_args()

    document = json.loads(args.input.read_text(encoding="utf-8-sig"))
    alerts = parse_alerts(
        document,
        allowed_hosts=set(args.host) if args.host else None,
        allowed_origins=set(args.origin),
    )
    rows = [
        {
            **alert,
            "review_status": "pending_independent_review",
            "is_real": None,
            "priority": None,
            "reviewer_reason": "",
            "evidence_reference": "",
        }
        for alert in alerts
    ]
    output = {
        "status": "awaiting_two_independent_reviewers",
        "data_origin": "real_zap_export_filtered_by_host",
        "source": str(args.input),
        "allowed_hosts": args.host,
        "allowed_origins": args.origin,
        "notice": (
            "Chưa phải ground truth; không được dùng để tính benchmark "
            "cho tới khi Như và Phát khóa nhãn độc lập."
        ),
        "alerts": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"records={len(rows)}; output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
