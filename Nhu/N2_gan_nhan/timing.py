"""Interactive human stopwatches; never infer labels or reconstruct past timings."""

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
import sys
import time

from Nhu.common import (ContractError, ID_PATTERN, digest, indexed_rows, nonempty,
                        read_json, require, seconds, validate_dataset, write_json)
from .labels import COLUMNS


TIMING_VERSION = "nhu-human-timing-v1"
SOURCE_KEYS = ("dataset_id", "source_sha256", "data_origin")


def now():
    return datetime.now(timezone.utc)


def validate_record(document, dataset, reviewer):
    alerts = validate_dataset(dataset)
    require(isinstance(document, dict) and document.get("schema_version") == TIMING_VERSION,
            "Invalid timing record.")
    meta = document.get("_meta", {})
    require(isinstance(meta, dict) and all(meta.get(key) == dataset["_meta"][key]
                                          for key in SOURCE_KEYS),
            "Timing belongs to another dataset/source.")
    require(nonempty(reviewer) and meta.get("reviewer") == reviewer,
            "Timing belongs to another reviewer.")
    require(meta.get("measurement_method") == "interactive_monotonic" and
            meta.get("completion_declared_by_user") is True and nonempty(meta.get("scope_note")),
            "Missing measurement method, scope or completion declaration.")
    purpose = document.get("purpose")
    require(purpose in ("label", "manual-total", "ai-review"), "Unknown timing purpose.")
    if purpose == "label":
        require(document.get("alert_id") in alerts and document.get("run_id") is None and
                meta.get("independence_declared_by_user") is True,
                "Label timing requires a dataset alert and independence declaration.")
    else:
        require(document.get("alert_id") is None, "Whole-pipeline timing cannot be per-alert.")
        run_id = document.get("run_id")
        require((purpose == "manual-total" and run_id is None) or
                (purpose == "ai-review" and isinstance(run_id, str) and ID_PATTERN.fullmatch(run_id)),
                "AI review requires its run ID; manual-total must not have one.")
    duration = seconds(document.get("elapsed_seconds"))
    require(duration > 0, "Timing must be measured, not zero.")
    instants = []
    for key in ("started_at_utc", "finished_at_utc"):
        value = document.get(key)
        require(isinstance(value, str), "Missing start/end timestamp.")
        instant = datetime.fromisoformat(value)
        require(instant.tzinfo is not None, "Timing timestamps require a timezone.")
        instants.append(instant)
    wall_seconds = (instants[1] - instants[0]).total_seconds()
    require(wall_seconds > 0 and abs(wall_seconds - duration) <= max(2, duration * 0.01),
            "Clock changed during measurement; repeat instead of inventing a duration.")
    return document


def measure(dataset, reviewer, output, *, purpose, scope_note, alert_id=None, run_id=None,
            confirmed_independent=False, prompt=input, wall_clock=now, counter=time.perf_counter):
    """Only the interval between two explicit user actions counts; interruption saves nothing."""
    validate_dataset(dataset)
    require(not Path(output).exists(), "Timing output already exists; refusing overwrite.")
    require(nonempty(reviewer) and nonempty(scope_note), "Reviewer and scope note are required.")
    # Validate identity/purpose before starting a stopwatch, using no measured output.
    require(purpose in ("label", "manual-total", "ai-review"), "Unknown timing purpose.")
    require(purpose != "label" or (confirmed_independent is True and
            alert_id in indexed_rows(dataset["alerts"])), "Confirm independent labeling first.")
    require(purpose == "label" or alert_id is None, "Unexpected alert ID.")
    require((purpose == "ai-review" and isinstance(run_id, str) and ID_PATTERN.fullmatch(run_id)) or
            (purpose != "ai-review" and run_id is None), "Invalid run ID for timing purpose.")
    require(not prompt("Enter to START, or q to cancel: ").strip(), "Cancelled.")
    started = wall_clock()
    tick = counter()
    require(not prompt("Work now. Enter only when FINISHED; Ctrl+C cancels this interval: ").strip(),
            "Cancelled; no timing recorded for this interval.")
    elapsed = seconds(counter() - tick)
    finished = wall_clock()
    document = {
        "schema_version": TIMING_VERSION,
        "_meta": {**{key: dataset["_meta"][key] for key in SOURCE_KEYS},
                  "reviewer": reviewer, "scope_note": scope_note,
                  "measurement_method": "interactive_monotonic",
                  "completion_declared_by_user": True,
                  "independence_declared_by_user": confirmed_independent,
                  "notice": "User-operated stopwatch; timestamps do not prove who worked or independence."},
        "purpose": purpose, "alert_id": alert_id, "run_id": run_id,
        "started_at_utc": started.isoformat(), "finished_at_utc": finished.isoformat(),
        "elapsed_seconds": elapsed,
    }
    validate_record(document, dataset, reviewer)
    write_json(output, document)
    return document


def label_records(dataset, directory, reviewer):
    """Resume completed alerts; reject duplicates, foreign data and overlapping intervals."""
    records = {}
    intervals = []
    for path in sorted(Path(directory).glob("*.json")):
        record = validate_record(read_json(path), dataset, reviewer)
        require(record["purpose"] == "label", "Keep whole-pipeline timings in a separate folder.")
        item_id = record["alert_id"]
        require(item_id not in records, "Duplicate alert timing; do not double-count work.")
        records[item_id] = record
        intervals.append(tuple(datetime.fromisoformat(record[key])
                               for key in ("started_at_utc", "finished_at_utc")))
    intervals.sort()
    require(all(previous[1] <= following[0] for previous, following in zip(intervals, intervals[1:])),
            "Per-alert intervals overlap; one reviewer cannot time two alerts simultaneously.")
    return records


def measure_labels(dataset, reviewer, directory, *, scope_note, confirmed_independent=False):
    require(confirmed_independent is True, "Confirm independence before opening other labels/AI.")
    completed = label_records(dataset, directory, reviewer)
    for item_id, row in validate_dataset(dataset).items():
        if item_id in completed:
            continue
        print(f"Alert {item_id}; scanner risk={row['risk']} (not a human verdict).")
        measure(dataset, reviewer, Path(directory) / f"label-{digest(item_id)}.json",
                purpose="label", alert_id=item_id, scope_note=scope_note, confirmed_independent=True)
    print("All alert stopwatches saved. Labels still need human completion and locking.")


def apply_timings(dataset, sheet, directory, output, *, reviewer):
    alerts = validate_dataset(dataset)
    measurements = label_records(dataset, directory, reviewer)
    require(measurements.keys() == alerts.keys(), "Time every alert before exporting the timed sheet.")
    with Path(sheet).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        require(tuple(reader.fieldnames or ()) == COLUMNS, "Invalid label CSV header.")
        rows = list(reader)
    labels = indexed_rows(rows)
    require(labels.keys() == alerts.keys(), "Label CSV has missing/extra alerts.")
    for item_id, row in labels.items():
        require(set(row) == set(COLUMNS) and all(isinstance(value, str) for value in row.values()),
                "Malformed CSV row.")
        require(row["risk"] == alerts[item_id]["risk"], "Scanner risk changed.")
        require(not row["elapsed_seconds"].strip(), "Existing time must not be silently replaced.")
        row["elapsed_seconds"] = repr(measurements[item_id]["elapsed_seconds"])
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(labels.values())
    return len(labels)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    label = commands.add_parser("labels", help="Time each independently labeled alert; resume safely.")
    record = commands.add_parser("record", help="Time one complete manual pipeline or AI review.")
    apply = commands.add_parser("apply", help="Copy measured seconds to a NEW CSV, without changing labels.")
    for command in (label, record, apply):
        command.add_argument("--dataset", type=Path, required=True)
        command.add_argument("--reviewer", required=True)
    label.add_argument("--output-dir", type=Path, required=True)
    label.add_argument("--confirm-independent", action="store_true")
    for command in (label, record):
        command.add_argument("--scope-note", required=True)
    record.add_argument("--purpose", choices=("manual-total", "ai-review"), required=True)
    record.add_argument("--run-id")
    record.add_argument("--output", type=Path, required=True)
    apply.add_argument("--sheet", type=Path, required=True)
    apply.add_argument("--records-dir", type=Path, required=True)
    apply.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        dataset = read_json(args.dataset)
        if args.command == "apply":
            count = apply_timings(dataset, args.sheet, args.records_dir, args.output, reviewer=args.reviewer)
            print(f"Copied measured seconds for {count} alerts; labels were not generated or changed.")
        else:
            require(sys.stdin.isatty(), "Run interactively in your own terminal; no headless human timings.")
            if args.command == "labels":
                measure_labels(dataset, args.reviewer, args.output_dir, scope_note=args.scope_note,
                               confirmed_independent=args.confirm_independent)
            else:
                record = measure(dataset, args.reviewer, args.output, purpose=args.purpose,
                                 scope_note=args.scope_note, run_id=args.run_id)
                print(f"Measured seconds: {record['elapsed_seconds']:.3f}; keep the original JSON.")
    except (KeyboardInterrupt, EOFError):
        print("Current interval cancelled; completed records and label CSV are unchanged.")
        return 1
    except (OSError, ValueError, TypeError, KeyError) as error:
        # Only our ContractError messages are safe; never dump CSV contents or paths.
        print(str(error) if isinstance(error, ContractError) else "Unable to record/export timings; check inputs.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
