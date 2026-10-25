"""Checkpointed triage of a frozen, redacted dataset; no mock fallback."""

import argparse
import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ai.A3a_ai_config import AIClient, AIResponseError
from ai.A3a_ai_config.client import TRIAGE_SYSTEM
from ai.A3a_ai_config.contracts import TriageSuggestion
from ai.A3a_ai_config.environment import load_environment
from ai.A3a_ai_config.safety import redact
from .parser import parse_alerts


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(redact(data), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Windows readers (editors, indexers, antivirus) may briefly deny replacement.
    # Keep the previous checkpoint and the new .tmp intact if retries fail.
    for attempt in range(6):
        try:
            temporary.replace(path)
            break
        except PermissionError as error:
            if getattr(error, "winerror", None) not in {5, 32, 33} or attempt == 5:
                raise
            time.sleep(0.1 * (attempt + 1))


def execute(source, output, client, *, resume=False, max_calls=11):
    raw = source.read_bytes()
    document = json.loads(raw.decode("utf-8-sig"))
    alerts = parse_alerts(document)
    if not alerts or redact(document) != document:
        raise ValueError("Expected nonempty, already redacted input")
    identity = {"source_sha256": sha(raw), "config": client.config.model_dump(),
                "prompt_sha256": sha(TRIAGE_SYSTEM.encode()),
                "schema_sha256": sha(json.dumps(TriageSuggestion.model_json_schema(), sort_keys=True).encode()),
                "alert_ids": [a["alert_id"] for a in alerts]}
    if output.exists():
        if not resume:
            raise FileExistsError("Use --resume explicitly")
        report = json.loads(output.read_text(encoding="utf-8"))
        if any(report["_meta"].get(k) != v for k, v in identity.items()):
            raise ValueError("Checkpoint input/config/prompt/schema differs")
        ids = [r["alert_id"] for r in report["results"]]
        if len(set(ids)) != len(ids) or not set(ids) <= set(identity["alert_ids"]):
            raise ValueError("Invalid checkpoint IDs")
        for result in report["results"]:
            TriageSuggestion.model_validate(result)
    else:
        report = {"schema_version": "lan-ai-v1-proposed", "_meta": {
            **identity, "run_id": str(uuid.uuid4()), "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "execution_mode": client.mode, "data_origin": document.get("_meta", {}).get("data_origin"),
            "endpoint": client.config.base_url, "model_inference_performed": False,
            "is_replay": False, "review_required": True, "final_decision": "pending_human_review",
            "is_benchmark_result": False, "record_count": 0, "status": "pending",
            "notice": "Inference suggestions only; not human ground truth or N3 evaluation."},
            "results": [], "attempts": []}
    done = {r["alert_id"] for r in report["results"]}
    report["_meta"]["status"] = "incomplete"
    save(output, report)
    calls = 0
    for alert in alerts:
        if alert["alert_id"] in done:
            continue
        if calls >= max_calls:
            break
        calls += 1
        before = len(client.calls)
        try:
            result = client.classify_alert(alert)
            report["results"].append(result)
            done.add(alert["alert_id"])
            status = "success"
        except AIResponseError:
            status = "error"
        report["attempts"].append({"alert_id": alert["alert_id"], "status": status,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "api_calls": client.calls[before:]})
        report["_meta"].update(record_count=len(done),
            model_inference_performed=client.mode == "live" and bool(report["results"]),
            updated_at_utc=datetime.now(timezone.utc).isoformat())
        save(output, report)
        # Fail fast on provider/auth/schema issues; resume never repeats successes.
        if status == "error":
            break
    report["_meta"]["status"] = "completed" if len(done) == len(alerts) else "incomplete"
    save(output, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("ai/A1_ai_triage/review_bundle_v1/alerts.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, default=Path("ai/.env"))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-calls", type=int, default=11)
    parser.add_argument("--interval", type=float, default=20)
    args = parser.parse_args()
    try:
        if args.max_calls <= 0 or args.input.resolve() == args.output.resolve():
            raise ValueError("Invalid call budget/output")
        load_environment(args.env_file)
        with AIClient(mode="live", min_interval_seconds=args.interval) as client:
            report = execute(args.input, args.output, client, resume=args.resume, max_calls=args.max_calls)
        print(f"status={report['_meta']['status']}; records={len(report['results'])}; output={args.output}")
        return 0 if report["_meta"]["status"] == "completed" else 1
    except (OSError, ValueError, TypeError, AIResponseError) as error:
        print(f"Live triage stopped ({type(error).__name__}); no mock fallback.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
