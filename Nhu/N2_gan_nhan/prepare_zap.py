"""Prepare a scoped H1 dataset using Lan's parser, without assigning labels."""

import argparse
from collections import Counter
from copy import deepcopy
from pathlib import Path
from urllib.parse import urlsplit

from Lan.A1_ai_triage.parser import parse_alerts
from Nhu.common import (SCHEMA_VERSION, digest, file_digest, read_json, require,
                        text_file_digest, validate_dataset, write_json)
from .labels import create_sheet


ALLOWED_ORIGINS = frozenset({"http://localhost:3000", "http://localhost:5173"})


def origin(url):
    require(isinstance(url, str), "ZAP instance needs an absolute URL.")
    parsed = urlsplit(url)
    require(parsed.scheme in {"http", "https"} and parsed.hostname and
            not (parsed.username or parsed.password), "Invalid ZAP origin.")
    port = parsed.port
    host = parsed.hostname
    if ":" in host:
        host = "[" + host + "]"
    return parsed.scheme + "://" + host + (":" + str(port) if port is not None else "")


def scope_report(document):
    """Check both the site and instance; never visit any exported URL."""
    require(isinstance(document, dict) and isinstance(document.get("site"), list),
            "Expected a native ZAP report with a site list.")
    sites, mapping, excluded = [], [], Counter()
    raw_count = raw_groups = 0
    for site_index, site in enumerate(document["site"]):
        require(isinstance(site, dict) and isinstance(site.get("alerts"), list),
                "Malformed ZAP site.")
        site_origin = origin(site.get("@name"))
        groups = []
        for group_index, group in enumerate(site["alerts"]):
            require(isinstance(group, dict) and isinstance(group.get("instances"), list)
                    and group["instances"], "Malformed ZAP alert instances.")
            raw_groups += 1
            instances = []
            for instance_index, instance in enumerate(group["instances"]):
                require(isinstance(instance, dict), "Malformed ZAP instance.")
                instance_origin = origin(instance.get("uri") or instance.get("url"))
                raw_count += 1
                if site_origin not in ALLOWED_ORIGINS or instance_origin not in ALLOWED_ORIGINS:
                    excluded[instance_origin] += 1
                    continue
                instances.append(deepcopy(instance))
                mapping.append({
                    "source_pointer": f"/site/{site_index}/alerts/{group_index}/instances/{instance_index}",
                    "site": site_origin, "plugin_id": str(group.get("pluginid", "")),
                    "zap_instance_id": str(instance.get("id", "")),
                    "method": instance.get("method"),
                })
            if instances:
                groups.append({**deepcopy(group), "instances": instances})
        if groups:
            sites.append({"@name": site_origin, "alerts": groups})
    require(bool(mapping), "No in-scope localhost instances.")
    rows = parse_alerts({"site": sites})
    require(len(rows) == len(mapping), "Parser changed the instance count.")
    # Explicit IDs in the canonical flat input must survive another A1 parse.
    require(parse_alerts({"alerts": rows}) == rows, "A1 normalization is not stable.")
    return rows, {
        "raw_instance_count": raw_count, "raw_site_alert_group_count": raw_groups,
        "included_instance_count": len(rows),
        "included_site_alert_group_count": sum(len(site["alerts"]) for site in sites),
        "excluded_instance_count": sum(excluded.values()),
        "excluded_by_origin": dict(sorted(excluded.items())),
        "risk_counts": dict(Counter(row["risk"] for row in rows)),
        "mapping": [{"alert_id": row["alert_id"], **entry} for row, entry in zip(rows, mapping)],
    }


def write_pack(source, output, *, dataset_id):
    source, output = Path(source), Path(output)
    require(not output.exists(), "Use a new output directory; existing work is never overwritten.")
    document = read_json(source)
    rows, inventory = scope_report(document)
    source_hash = file_digest(source)
    scan_meta = {
        "dataset_id": dataset_id, "data_origin": "real_zap",
        "raw_zap_sha256": source_hash, "zap_version": document.get("@version"),
        "scan_created_at": document.get("created"),
    }
    canonical = {"_meta": scan_meta, "alerts": rows}
    write_json(output / "a1-input.json", canonical)
    canonical_hash = file_digest(output / "a1-input.json")
    dataset = {
        "schema_version": SCHEMA_VERSION,
        "_meta": {**scan_meta, "source_sha256": canonical_hash}, "alerts": rows,
    }
    validate_dataset(dataset)
    write_json(output / "dataset.json", dataset)
    create_sheet(dataset, output / "nhu-labels.blank.csv")
    provenance = {
        **scan_meta, **inventory, "source_sha256": canonical_hash,
        "raw_zap_content_sha256": digest(document),
        "allowed_origins": sorted(ALLOWED_ORIGINS),
        "raw_source": "alert/" + source.name,
        "canonical_input": "a1-input.json",
        "normalizer": "Lan/A1_ai_triage/parser.py",
        "normalizer_sha256": file_digest(Path(__file__).resolve().parents[2] / "Lan/A1_ai_triage/parser.py"),
        "redactor_sha256": file_digest(Path(__file__).resolve().parents[2] / "Lan/A3a_ai_config/safety.py"),
        "normalizer_text_sha256": text_file_digest(Path(__file__).resolve().parents[2] / "Lan/A1_ai_triage/parser.py"),
        "redactor_text_sha256": text_file_digest(Path(__file__).resolve().parents[2] / "Lan/A3a_ai_config/safety.py"),
        "scan_sut_commit": None,
        "human_labels_assigned": False, "ai_inference_performed": False,
        "protocol_approved": False,
        "notice": "One instance per record. IDs come from Lan's parser. No deduplication or labels. "
                  "The original export does not record the exact SUT commit or full HTTP responses. "
                  "Keep the original private when reviewing unredacted query values; never send it to AI.",
    }
    write_json(output / "provenance.json", provenance)
    return provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("alert/2026-10-14-ZAP-Report-.json"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--dataset-id", default="h1-zap-20261014-localhost-v1")
    args = parser.parse_args()
    try:
        report = write_pack(args.source, args.output_dir, dataset_id=args.dataset_id)
    except (OSError, ValueError, TypeError, KeyError):
        print("Preparation failed: check ZAP structure, scope, unique IDs and a new output path.")
        return 1
    print(f"included={report['included_instance_count']}; excluded={report['excluded_instance_count']}; labels=blank")
    print("source_sha256=" + report["source_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
