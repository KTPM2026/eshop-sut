"""Recompute descriptive live-run statistics; never infer ground truth or cost."""

import argparse
from collections import Counter
import json
from pathlib import Path

from ai.A1_ai_triage.live import save


def usage(calls):
    return {"api_calls": len(calls), "successful_calls": sum(c["status"] == "success" for c in calls),
        "failed_calls": sum(c["status"] != "success" for c in calls),
        "reported_tokens": {key: sum((c.get("usage") or {}).get(key, 0) for c in calls)
            for key in ("prompt_tokens", "completion_tokens", "total_tokens")},
        "usage_missing_calls": sum(c.get("usage") is None for c in calls),
        "cost": None}


def summarize(triage_paths, benchmark_path):
    triage = []
    for path in triage_paths:
        report = json.loads(path.read_text(encoding="utf-8"))
        calls = [c for a in report["attempts"] for c in a["api_calls"]]
        triage.append({"source": path.as_posix(), "status": report["_meta"]["status"],
            "run_id": report["_meta"]["run_id"], "records": len(report["results"]),
            "priority_counts": dict(Counter(r["priority"] for r in report["results"])),
            "is_real_counts": dict(Counter(str(r["is_real"]) for r in report["results"])),
            **usage(calls)})
    benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
    branches = {}
    for row in benchmark["rows"]:
        branches.setdefault(row["branch"], []).append(row)
    return {"triage_runs": triage, "triage_quality_metrics": None,
        "human_review_status": "pending_independent_labels_and_N3",
        "manual_time_savings": None,
        "benchmark": {"source": benchmark_path.as_posix(), "status": benchmark["status"],
            "branches": {name: {"runs": len(rows), "successful_runs": sum(r["bypass"] for r in rows),
                "success_rate_per_run": sum(r["bypass"] for r in rows) / len(rows),
                "attack_requests": sum(r["attack_requests"] for r in rows),
                "auxiliary_requests": sum(r["auxiliary_requests"] for r in rows),
                "request_to_first_success": [r["request_to_first_success"] for r in rows],
                "stop_reasons": [r["stop_reason"] for r in rows]}
                for name, rows in branches.items()}, **usage(benchmark.get("api_calls", []))},
        "notice": "Descriptive lab measurements only; API latency is not manual time saved. Missing usage/cost remains unknown."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--triage", type=Path, nargs="+", required=True)
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    save(args.output, summarize(args.triage, args.benchmark))
    print(f"summary={args.output}")


if __name__ == "__main__":
    main()
