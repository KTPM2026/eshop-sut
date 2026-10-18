"""Create verifiable cache envelopes or replay them without network access."""

import argparse
import hashlib
import json
from pathlib import Path

from ai.A3a_ai_config.safety import redact


def build(source, output):
    raw = source.read_bytes()
    data = json.loads(raw.decode("utf-8-sig"))
    # Never silently modify source evidence: redact before creating an artifact.
    if redact(data) != data:
        raise ValueError("Source requires redaction before caching")
    if not isinstance(data, dict) or not (data.get("rows") or data.get("results")):
        raise ValueError("No results to cache")
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    envelope = {"schema_version": "lan-cache-v1", "is_replay": False,
        "source": source.as_posix(), "source_sha256": hashlib.sha256(raw).hexdigest(),
        "payload_sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "notice": "Preserves source mode/status; this envelope does not validate results or labels.",
        "payload": data}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(envelope, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return envelope


def replay(source):
    data = json.loads(source.read_text(encoding="utf-8"))
    payload = json.dumps(data["payload"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if hashlib.sha256(payload.encode("utf-8")).hexdigest() != data["payload_sha256"]:
        raise ValueError("Cache payload hash mismatch")
    return {**data, "is_replay": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    if args.replay:
        print("PHÁT LẠI KẾT QUẢ ĐÃ LƯU — không gọi mạng")
        print(json.dumps(replay(args.source), ensure_ascii=False, indent=2))
    elif args.output:
        build(args.source, args.output)
        print(f"cache={args.output}")
    else:
        parser.error("--output is required when not replaying")


if __name__ == "__main__":
    main()
