"""CLI Triage: mặc định mock, mọi kết quả chỉ là gợi ý để người rà soát."""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from ai.A3a_ai_config import AIClient, AIResponseError
from ai.A3a_ai_config.safety import redact
from .parser import parse_alerts


def run_triage(
    document: dict | list,
    client: AIClient,
    *,
    source_sha256: str,
    allowed_hosts: set[str] | None = None,
    allowed_origins: set[str] | None = None,
) -> dict:
    """Xử lý mọi record; không lọc/bỏ alert, không sinh quyết định review cuối."""
    alerts = parse_alerts(
        document, allowed_hosts=allowed_hosts, allowed_origins=allowed_origins
    )
    results = [client.classify_alert(alert) for alert in alerts]
    meta = document.get("_meta", {}) if isinstance(document, dict) else {}
    synthetic = isinstance(meta, dict) and meta.get("data_origin") == "synthetic"
    return {
        "schema_version": "lan-ai-v1-proposed",
        "_meta": {
            "execution_mode": client.mode,
            "data_origin": "synthetic" if synthetic else "unverified_external",
            "model_inference_performed": client.mode == "live" and bool(results),
            "is_replay": False,
            "review_required": True,
            "final_decision": "pending_human_review",
            "is_benchmark_result": False,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_sha256": source_sha256,
            "record_count": len(results),
            "allowed_hosts": sorted(allowed_hosts) if allowed_hosts else None,
            "allowed_origins": sorted(allowed_origins) if allowed_origins else None,
            "config": client.config.model_dump(),
            "notice": "Mẫu/mock không phải kết quả model, nhãn chuẩn hay số liệu benchmark.",
        },
        "results": results,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path(__file__).with_name("sample_alert_data.json"))
    parser.add_argument("--output", type=Path, default=Path("ai/outputs/triage_result.json"))
    parser.add_argument("--mode", choices=["mock", "live"], default="mock")
    parser.add_argument(
        "--host",
        action="append",
        dest="hosts",
        help="Chỉ nhận alert từ hostname này; có thể lặp lại. Dùng với ZAP report thật.",
    )
    parser.add_argument(
        "--origin",
        action="append",
        dest="origins",
        help="Chỉ nhận origin đầy đủ, ví dụ http://localhost:3000.",
    )
    args = parser.parse_args()
    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError("Không được ghi đè file input.")
        raw = args.input.read_bytes()
        document = json.loads(raw.decode("utf-8-sig"))
        with AIClient(mode=args.mode) as client:
            report = run_triage(
                document,
                client,
                source_sha256=hashlib.sha256(raw).hexdigest(),
                allowed_hosts=set(args.hosts) if args.hosts else None,
                allowed_origins=set(args.origins) if args.origins else None,
            )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(redact(report), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, TypeError, ValidationError, AIResponseError) as error:
        # Không in ValidationError/body vì có thể kèm nguyên văn dữ liệu nhạy cảm.
        print(f"Triage không hoàn tất ({type(error).__name__}). Kiểm tra input/cấu hình; không có fallback mock.")
        return 1
    print(f"mode={args.mode}; records={report['_meta']['record_count']}; output={args.output}")
    print("Chỉ là gợi ý để người review; chưa phải kết quả benchmark.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
