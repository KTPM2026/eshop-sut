"""Freeze redacted alerts and separate unlabelled reviewer sheets, without AI."""

import argparse
import hashlib
import json
from pathlib import Path

from .parser import parse_alerts
from ai.A3a_ai_config.safety import redact


def freeze(source, output, origin):
    if output.exists():
        raise FileExistsError("Refusing to overwrite a frozen review bundle")
    raw = source.read_bytes()
    alerts = redact(parse_alerts(json.loads(raw.decode("utf-8-sig")), allowed_origins={origin}))
    if not alerts:
        raise ValueError("Empty dataset")
    files = {"alerts.json": {"_meta": {"data_origin": "real_zap_redacted",
             "origin": origin, "model_inference_performed": False}, "alerts": alerts}}
    for reviewer in ("nhu", "phat"):
        files[f"review_{reviewer}.json"] = {"reviewer": reviewer, "status": "pending_independent_review",
            "model_output_included": False, "started_at_utc": None, "locked_at_utc": None,
            "alerts": [{**alert, "is_real": None, "priority": None,
                        "review_status": "pending", "reviewer_reason": "",
                        "evidence_reference": "", "review_seconds": None} for alert in alerts]}
    encoded = {name: (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
               for name, value in files.items()}
    manifest = {"status": "frozen_input_pending_human_review", "origin": origin,
        "source": source.as_posix(), "source_sha256": hashlib.sha256(raw).hexdigest(),
        "record_count": len(alerts), "alert_ids": [a["alert_id"] for a in alerts],
        "files": {name: hashlib.sha256(data).hexdigest() for name, data in encoded.items()},
        "notice": "Hashes of review sheets describe blank handoff copies, not completed labels."}
    output.mkdir(parents=True)
    for name, data in encoded.items():
        (output / name).write_bytes(data)
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--origin", required=True)
    args = parser.parse_args()
    result = freeze(args.input, args.output, args.origin)
    print(f"records={result['record_count']}; output={args.output}")


if __name__ == "__main__":
    main()
