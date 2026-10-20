"""Inspect Git handoff metadata/IDs only, without disclosing other reviewers' labels or AI verdicts."""

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlsplit

from Nhu.common import (ContractError, ID_PATTERN, digest, file_digest, indexed_rows, read_json,
                        require, utc_now, valid_hash, validate_dataset, write_json)


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "Nhu/N2_gan_nhan/data/h1-20261014"
PHAT_PATH = "Phat/P2_nhan_alert/alert-labeling-template.md"
LAN_TEMPLATE = "A1_ai_triage/ground_truth_template.json"
LAN_CACHE = "A3b_video_cache/cache/triage_result.json"
AUTH_EXPORT = "alert/zap-alerts-auth.json"
TRACKED_TRIAGE = "Lan/outputs/triage_zap_report.json"


def git_bytes(*args):
    result = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True)
    require(result.returncode == 0, "Cannot read the requested Git ref/path; fetch it first.")
    return result.stdout


def git(*args):
    return git_bytes(*args).decode("utf-8")


def resolve_ref(ref):
    return git("rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}").strip()


def markdown_ids(text):
    """Read only the first column of the primary alert table, never label/reason columns."""
    lines = text.splitlines()
    for index, line in enumerate(lines[:-1]):
        header = [cell.strip().strip("`*").casefold() for cell in line.strip().strip("|").split("|")]
        if not (line.lstrip().startswith("|") and header[0] in ("#", "id", "alert_id", "alert id") and
                re.fullmatch(r"\|(?:\s*:?-+:?\s*\|)+\s*", lines[index + 1])):
            continue
        result = []
        for row in lines[index + 2:]:
            if not row.lstrip().startswith("|"):
                break
            item_id = row.strip().strip("|").split("|", 1)[0].strip().strip("`*")
            require(ID_PATTERN.fullmatch(item_id) is not None, "Unrecognized P2 ID column.")
            result.append(item_id)
        require(result and len(set(result)) == len(result), "P2 ID column is empty or duplicated.")
        return set(result)
    raise ContractError("Cannot identify the P2 primary alert table; no labels were displayed.")


def id_comparison(reference_ids, candidate_ids):
    return {"record_count": len(candidate_ids), "matching_ids": len(reference_ids & candidate_ids),
            "missing_reference_ids": len(reference_ids - candidate_ids),
            "extra_ids": len(candidate_ids - reference_ids),
            "exact_id_set": reference_ids == candidate_ids}


def hash_status(value, expected):
    if value is None:
        return "missing"
    if not valid_hash(value):
        return "invalid"
    return "match" if value == expected else "different"


def inspect_flat_export(document):
    """Inventory singleton parses, but never drop colliding records to make a runnable dataset."""
    from ai.A1_ai_triage.parser import parse_alerts
    rows = document.get("alerts")
    require(isinstance(rows, list) and rows and all(isinstance(row, dict) for row in rows),
            "Expected a nonempty flat ZAP export.")
    ids, risks, origins = Counter(), Counter(), Counter()
    included = 0
    for row in rows:
        parsed = urlsplit(str(row.get("url", "")))
        require(parsed.hostname and not (parsed.username or parsed.password), "Invalid export origin.")
        origin = f"{parsed.scheme}://{parsed.hostname}" + (f":{parsed.port}" if parsed.port else "")
        origins[origin] += 1
        normalized = parse_alerts({"alerts": [row]},
                                  allowed_origins={"http://localhost:3000", "http://localhost:5173"})
        included += len(normalized)
        for alert in normalized:
            ids[alert["alert_id"]] += 1
            risks[alert["risk"]] += 1
    return {"source_content_sha256": digest(document), "raw_records": len(rows),
            "in_scope_records": included, "origins": dict(origins), "scanner_risk_counts": dict(risks),
            "unique_normalized_ids": len(ids), "duplicate_records": sum(count - 1 for count in ids.values()),
            "direct_parser_input_ready": included > 0 and all(count == 1 for count in ids.values()),
            "notice": "No deduplication, labels or scope change performed. Normalized identities are not bug counts. "
                      "An export filename is not proof of a successful authenticated session."}


def summarize_handoffs(dataset, input_document, *, input_sha256, phat_document, lan_document, cache):
    ids = set(validate_dataset(dataset))
    input_ids = set(indexed_rows(input_document.get("alerts") if isinstance(input_document, dict)
                                else input_document))
    require(input_ids == ids and input_sha256 == dataset["_meta"]["source_sha256"],
            "Local canonical A1 input no longer matches the locked dataset.")
    phat_ids = markdown_ids(phat_document)
    lan_rows = indexed_rows(lan_document.get("alerts"))
    lan_ids = set(lan_rows)
    origins = set()
    for row in lan_rows.values():
        url = urlsplit(row.get("url", ""))
        if url.scheme and url.hostname:
            origins.add(f"{url.scheme}://{url.hostname}" + (f":{url.port}" if url.port else ""))
    cache_meta = cache.get("_meta", cache)
    require(isinstance(cache_meta, dict) and isinstance(cache.get("results"), list),
            "Unrecognized A1 cache metadata.")
    phat = {**id_comparison(ids, phat_ids), "format": "markdown_table_not_lock_contract",
            "shared_source_hash_mentioned": dataset["_meta"]["source_sha256"] in phat_document}
    lan = {**id_comparison(ids, lan_ids), "observed_origins": sorted(origins),
           "status": lan_document.get("status"),
           "source_hash_status": hash_status(lan_document.get("_meta", {}).get("source_sha256"), input_sha256)}
    triage = {"record_count": len(cache["results"]), "status": cache_meta.get("status"),
              "is_replay": cache_meta.get("is_replay"),
              "model_inference_performed": cache_meta.get("model_inference_performed"),
              "source_hash_status": hash_status(cache_meta.get("source_sha256"), input_sha256)}
    return {
        "created_at_utc": utc_now(), "is_benchmark_result": False,
        "ready_to_benchmark": False,
        "local_dataset": {"dataset_id": dataset["_meta"]["dataset_id"],
                          "source_sha256": input_sha256, "record_count": len(ids)},
        "phat_p2": phat, "lan_label_template": lan, "lan_triage_cache": triage,
        "notice": "Metadata/IDs only, not label verification or proof of independent work. "
                  "This audit does not load two locks, adjudicated truth or three reviewed live runs; "
                  "it cannot certify benchmark readiness. No scope, IDs or labels were changed.",
    }


def audit(dataset_path, input_path, phat_ref, lan_ref):
    phat_commit, lan_commit = resolve_ref(phat_ref), resolve_ref(lan_ref)
    files = set(git("ls-tree", "-r", "--name-only", lan_commit).splitlines())
    prefix = next((name for name in ("ai", "Lan") if f"{name}/{LAN_TEMPLATE}" in files), None)
    require(prefix is not None, "No known A1 handoff layout in the selected Lan ref.")
    report = summarize_handoffs(
        read_json(dataset_path), read_json(input_path), input_sha256=file_digest(input_path),
        phat_document=git("show", f"{phat_commit}:{PHAT_PATH}"),
        lan_document=json.loads(git("show", f"{lan_commit}:{prefix}/{LAN_TEMPLATE}")),
        cache=json.loads(git("show", f"{lan_commit}:{prefix}/{LAN_CACHE}")),
    )
    report["git_sources"] = {"phat": {"ref": phat_ref, "commit": phat_commit, "path": PHAT_PATH},
                             "lan": {"ref": lan_ref, "commit": lan_commit, "prefix": prefix}}
    main_commit = resolve_ref("origin/main")
    main_files = set(git("ls-tree", "-r", "--name-only", main_commit).splitlines())
    if AUTH_EXPORT in main_files:
        report["additional_h1_export"] = {**inspect_flat_export(json.loads(git("show", f"{main_commit}:{AUTH_EXPORT}"))),
                                           "git_commit": main_commit, "path": AUTH_EXPORT}
    if TRACKED_TRIAGE in main_files:
        tracked = json.loads(git("show", f"{main_commit}:{TRACKED_TRIAGE}"))
        meta = tracked.get("_meta", {})
        report["additional_triage_report"] = {
            "git_commit": main_commit, "path": TRACKED_TRIAGE,
            "record_count": len(tracked.get("results", [])), "execution_mode": meta.get("execution_mode"),
            "model_inference_performed": meta.get("model_inference_performed"),
            "is_benchmark_result": meta.get("is_benchmark_result"),
            "source_hash_status": hash_status(meta.get("source_sha256"), report["local_dataset"]["source_sha256"]),
            "notice": "Read metadata only. A committed mock file is not a live Triage run.",
        }
    return report


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=PACK / "dataset.json")
    parser.add_argument("--input", type=Path, default=PACK / "a1-input.json")
    parser.add_argument("--phat-ref", default="origin/phat/labs-workspace")
    parser.add_argument("--lan-ref", default="origin/main")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = audit(args.dataset, args.input, args.phat_ref, args.lan_ref)
        write_json(args.output, report)
    except (OSError, ValueError, TypeError, KeyError, IndexError) as error:
        print(str(error) if isinstance(error, ContractError) else "Cannot audit the handoff metadata.")
        return 1
    print(f"Nhu records={report['local_dataset']['record_count']}; "
          f"Phat rows={report['phat_p2']['record_count']}; "
          f"Lan records={report['lan_label_template']['record_count']}; "
          f"triage cache records={report['lan_triage_cache']['record_count']}")
    print("Metadata audit only. Agree on one scope/unit/ID set before labeling; no verdicts displayed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
