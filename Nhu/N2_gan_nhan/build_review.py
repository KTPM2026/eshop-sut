"""Export an explicitly AI-assisted review and peer comparison, never independent locks or ground truth."""

import argparse
from collections import Counter
import csv
import os
from pathlib import Path
import re

from Nhu.common import (digest, file_digest, read_json, require, text_file_digest,
                        validate_dataset, write_json)


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CSV_FIELDS = ("alert_id", "phat_group", "risk", "is_real", "priority", "reason", "evidence_ref",
              "review_method", "independent_human_review", "human_approved", "human_elapsed_seconds")


def peer_rows(text):
    result = {}
    for line in text.splitlines():
        if not re.match(r"^\|\s*\d+\s*\|", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        require(len(cells) == 9, "Peer table layout changed; do not guess a label mapping.")
        number = int(cells[0])
        require(number not in result, "Duplicate peer group number.")
        label = cells[5].replace("**", "")
        if label.casefold().startswith("th\u1eadt"):
            value = True
        elif label.casefold().startswith(("gi\u1ea3", "kh\u00f4ng ph\u1ea3i l\u1ed7 h\u1ed5ng")):
            value = False
        else:
            value = None
        priority = re.search(r"P[1-4]", cells[6])
        result[number] = {"label_text": label, "is_real": value,
                          "priority": priority.group() if priority else None}
    require(set(result) == set(range(1, 16)), "Expected the same 15 source groups as Phat.")
    return result


def make_review(dataset, provenance, raw, decisions, verification, peer):
    alerts = validate_dataset(dataset)
    require(dataset["_meta"]["source_sha256"] == provenance["source_sha256"], "Source hash mismatch.")
    require(verification.get("executed_by") == "Codex AI assistant" and
            verification.get("independent_human_review") is False and
            verification.get("student_performed") is False and
            verification.get("is_ground_truth") is False, "Do not misrepresent automated verification.")
    checks = verification["checkpoints"]
    require(checks["sql_boolean_effect_verified"] is True and checks["xss_dom_marker_executed"] is True and
            checks["cross_origin_frame_rendered"] is True, "Missing successful effect/control checks.")
    requests = verification["requests"]
    require(requests["sql-control"]["response"]["json_array_count"] == 0 and
            requests["sql-false"]["response"]["json_array_count"] == 0 and
            requests["sql-true"]["response"]["json_array_count"] > 0, "SQL boolean controls did not hold.")
    for key in ("api-products", "api-detail", "web-root", "web-forgot", "web-css", "web-env"):
        response = requests[key]["response"]
        require(response["status"] == 200 and response["headers"]["x-content-type-options"] is None,
                "Recorded hardening conditions changed; re-review the decisions.")
    for key in ("web-root", "web-forgot"):
        require(requests[key]["response"]["headers"]["content-security-policy"] is None and
                requests[key]["response"]["headers"]["x-frame-options"] is None,
                "Recorded framing/CSP conditions changed.")
    require(checks["react_numeric_constant"]["found"] is True and
            "lanes & 2080374784" in checks["react_numeric_constant"]["context"],
            "No source context confirming the bitmask.")
    all_groups = [(si, gi, site, group) for si, site in enumerate(raw["site"])
                  for gi, group in enumerate(site["alerts"])]
    require(len(all_groups) == 15, "The source group inventory changed.")
    by_source = {(si, gi): number for number, (si, gi, _, _) in enumerate(all_groups, 1)}
    mapping = {}
    for row in provenance["mapping"]:
        match = re.fullmatch(r"/site/(\d+)/alerts/(\d+)/instances/(\d+)", row["source_pointer"])
        require(match is not None, "Invalid original instance pointer.")
        si, gi, ii = map(int, match.groups())
        require(ii < len(raw["site"][si]["alerts"][gi]["instances"]), "Instance no longer exists.")
        require(row["alert_id"] not in mapping, "Duplicate provenance ID.")
        mapping[row["alert_id"]] = by_source[(si, gi)]
    require(mapping.keys() == alerts.keys(), "Mapping does not cover the locked input.")
    rules = {row["group"]: row for row in decisions["groups"]}
    require(len(rules) == len(decisions["groups"]) == 15 and set(rules) == set(range(1, 16)),
            "Every source group needs exactly one review decision.")
    for number, rule in rules.items():
        require(rule["status"] in {"true", "false", "unknown", "excluded"} and
                rule["is_real"] is {"true": True, "false": False, "unknown": None, "excluded": None}[rule["status"]],
                "Decision status/value mismatch.")
        require(rule["priority"] in ("P1", "P2", "P3", "P4") if rule["status"] in ("true", "false")
                else rule["priority"] is None, "Invalid priority.")
        require(bool(rule["reason"]) and bool(rule["evidence"]), "Missing reasoning/evidence.")
        require((number not in set(mapping.values())) == (rule["status"] == "excluded"),
                "External findings must be excluded, not labeled negative.")
    labels = []
    for item_id, alert in alerts.items():
        number = mapping[item_id]
        rule = rules[number]
        references = []
        for ref in rule["evidence"]:
            if ref == "scope":
                references.append("data/h1-20261014/provenance.json")
            elif ref == "source-export":
                references.append("alert/2026-10-14-ZAP-Report-.json (original source group " + str(number) + ")")
            elif ref.endswith(".png"):
                references.append("evidence/main-13f4d88/" + ref)
            else:
                section, key = ref.split("/", 1)
                require(section in ("requests", "checkpoints") and key in verification[section],
                        "Evidence reference no longer exists.")
                references.append("evidence/main-13f4d88/verification.json#/" + ref)
        labels.append({"alert_id": item_id, "phat_group": number, "risk": alert["risk"],
                       "is_real": rule["is_real"], "priority": rule["priority"], "reason": rule["reason"],
                       "evidence_ref": "; ".join(references), "review_method": "ai_assisted_after_peer_reference",
                       "independent_human_review": False, "human_approved": False, "human_elapsed_seconds": None})
    groups = []
    for number, (_, _, site, raw_group) in enumerate(all_groups, 1):
        rule = rules[number]
        state = "excluded" if rule["status"] == "excluded" else "pending_joint_verification" if (
            rule["is_real"] is None or peer[number]["is_real"] is None) else (
                "same_provisional_classification" if rule["is_real"] == peer[number]["is_real"] else "different")
        groups.append({**rule, "name": raw_group["name"], "site": site["@name"],
                       "source_instance_count": len(raw_group["instances"]),
                       "alert_ids": [item_id for item_id, group_id in mapping.items() if group_id == number],
                       "phat": peer[number], "comparison_status": state})
    return {
        "schema_version": "nhu-ai-assisted-review-v1",
        "_meta": {**dataset["_meta"], "student_name": "Th\u1ea1ch Nh\u01b0", "student_id": "23120312",
                  "author": "Codex AI assistant, at student's request", "reference_to_phat_read": True,
                  "independent_human_review": False, "human_approved": False,
                  "is_ground_truth": False, "is_benchmark_result": False,
                  "human_started_at_utc": None, "human_finished_at_utc": None, "human_total_seconds": None,
                  "verification_sut_commit": verification["sut_commit"],
                  "notice": "AI-assisted proposals after reading peer labels. Not two independent human reviews. "
                            "True includes reproduced hardening conditions under a proposed rubric, "
                            "not proof of exploitability. Never feed this artifact to N3 as adjudicated truth."},
        "summary": {"instances": dict(Counter("unknown" if row["is_real"] is None else
                                              str(row["is_real"]).lower() for row in labels)),
                    "groups": dict(Counter(row["status"] for row in groups)),
                    "comparison": dict(Counter(row["comparison_status"] for row in groups))},
        "groups": groups, "labels": labels,
    }


def write_review(output):
    output = Path(output)
    require(not output.exists(), "Use a new output directory; keep the original assisted review.")
    pack = HERE / "data/h1-20261014"
    source = ROOT / "alert/2026-10-14-ZAP-Report-.json"
    peer_path = ROOT / "Phat/P2_nhan_alert/alert-labeling-template.md"
    evidence = HERE / "evidence/main-13f4d88/verification.json"
    dataset, provenance = read_json(pack / "dataset.json"), read_json(pack / "provenance.json")
    require(file_digest(pack / "a1-input.json") == dataset["_meta"]["source_sha256"] and
            digest(read_json(source)) == provenance["raw_zap_content_sha256"], "Locked source/input changed.")
    report = make_review(dataset, provenance, read_json(source), read_json(HERE / "review_decisions.json"),
                         read_json(evidence), peer_rows(peer_path.read_text(encoding="utf-8-sig")))
    report["_meta"].update({"verification_sha256": file_digest(evidence),
                            "peer_text_sha256": text_file_digest(peer_path),
                            "decisions_text_sha256": text_file_digest(HERE / "review_decisions.json")})
    write_json(output / "nhu-review.json", report)
    with (output / "nhu-review.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(report["labels"])
    lines = ["# N2 - Th\u1ea1ch Nh\u01b0 (23120312): review c\u00f3 AI h\u1ed7 tr\u1ee3", "",
             "**Kh\u00f4ng ph\u1ea3i nh\u00e3n ng\u01b0\u1eddi \u0111\u1ed9c l\u1eadp / Ground Truth \u0111\u00e3 ch\u1ed1t.**", "",
             "C\u00f9ng 15 nh\u00f3m g\u1ed1c v\u1edbi Ph\u00e1t; 2 nh\u00f3m ngo\u00e0i scope b\u1ecb lo\u1ea1i, c\u00f2n 13 nh\u00f3m / 29 instance.", "",
             "| # Phat | Alert | Nhu (de xuat) | Priority | Phat | Doi chieu | Can cu / gioi han |",
             "|---|---|---|---|---|---|---|"]
    for group in report["groups"]:
        clean = lambda value: str(value).replace("|", "\\|").replace("\n", " ")
        lines.append("| " + " | ".join(map(clean, (group["group"], group["name"], group["status"],
            group["priority"] or "-", group["phat"]["label_text"], group["comparison_status"], group["reason"]))) + " |")
    evidence_link = lambda name: os.path.relpath(evidence.parent / name, output).replace("\\", "/")
    lines.extend(["", "Summary (not accuracy): `" + str(report["summary"]) + "`.", "",
                  "Evidence: [HTTP/browser log](" + evidence_link("verification.json") + "), "
                  "[XSS](" + evidence_link("xss-executed.png") + "), "
                  "[frame](" + evidence_link("frame-rendered.png") + ").", "",
                  "Human timing is unmeasured. Automated request milliseconds are not human labeling time.",
                  "P4 on non-vulnerabilities means low review priority, not an exploitable bug.",
                  "Groups 4, 8, 13 remain pending joint verification; do not auto-adjudicate."])
    with (output / "doi-chieu-phat.md").open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = write_review(args.output_dir)
    except (OSError, ValueError, TypeError, KeyError, IndexError):
        print("Review export failed; check source hashes, same groups, verification and a new output folder.")
        return 1
    print(report["summary"])
    print("AI-assisted only. Human confirmation pending; no independent lock, truth or benchmark created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
