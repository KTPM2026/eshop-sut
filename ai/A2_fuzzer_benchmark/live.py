"""Compare wordlist, cloud-generated static candidates and cloud feedback in H3."""

import argparse
import json
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from pydantic import Field

from ai.A1_ai_triage.live import save
from ai.A3a_ai_config import AIClient
from ai.A3a_ai_config.client import PAYLOAD_SYSTEM
from ai.A3a_ai_config.contracts import StrictContract, PayloadSuggestion
from ai.A3a_ai_config.environment import load_environment
from . import offline


class CandidateList(StrictContract):
    payloads: list[str] = Field(min_length=7, max_length=7)


LAB_CONTEXT = {
    "scope": "Disposable, seeded EShop SQLite SQLi lab; read-only product search only",
    "query": "SELECT * FROM products WHERE name LIKE '%" + "{search}" + "%'",
    "method": "GET", "parameter": "search",
    "oracle": "Observed product IDs equal vulnerable query and differ from parameterized query",
    "feedback": "403 blocked_keyword reports the matching literal substring; WAF stays enabled",
}


def benchmark(output, base, runs=3, budget=50, max_ai_calls=10, client=None):
    if output.exists():
        raise FileExistsError("Refusing to overwrite benchmark")
    offline.BASE = base
    sources = [Path(__file__), Path(offline.__file__),
        offline.ROOT / "ai/A3a_ai_config/client.py", offline.ROOT / "ai/A3a_ai_config/contracts.py",
        *[offline.ROOT / "backend" / n for n in ("server_fuzzer_lab.js", "waf_middleware.js", "database.js")]]
    hashes = {p.relative_to(offline.ROOT).as_posix(): offline.digest(p.read_bytes()) for p in sources}
    report = {"run_id": str(uuid.uuid4()), "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "config": client.config.model_dump(), "target": base, "budget": budget,
        "max_feedback_ai_calls_per_run": max_ai_calls, "is_replay": False,
        "oracle": "proposed_sqlite_differential_v1", "oracle_review": "pending_group_review",
        "sut_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_hashes": hashes, "prompt": PAYLOAD_SYSTEM, "lab_context": LAB_CONTEXT,
        "status": "incomplete", "rows": [], "model_inference_performed": False}
    save(output, report)
    before = len(client.calls)
    try:
        static = client._request(PAYLOAD_SYSTEM,
            {**LAB_CONTEXT, "instruction": "Generate exactly seven diverse, non-destructive SQLi search inputs. No WAF feedback is available."},
            CandidateList).payloads
        if any(not p.strip() or len(p) > 1024 for p in static):
            raise ValueError("Invalid candidate")
    except Exception as error:
        report.update(error_type=type(error).__name__, generation_calls=client.calls[before:])
        save(output, report)
        return report
    report.update(model_inference_performed=True, static_generation={"payloads": static,
        "api_calls": client.calls[before:], "reused_across_runs": True})
    names = ("wordlist_static", "llm_static", "llm_feedback")
    for number in range(runs):
        order = names[number % 3:] + names[:number % 3]
        for name in order:
            start = len(client.calls)
            suggestions = []

            def propose(attempts, remaining):
                if len(client.calls) - start >= max_ai_calls:
                    return {"payload": "", "reason": "AI call ceiling", "should_stop": True}
                answer = client._request(PAYLOAD_SYSTEM, {**LAB_CONTEXT,
                    "target_url": base + "/api/products", "previous_attempts": attempts,
                    "remaining_requests": remaining}, PayloadSuggestion).model_dump()
                if not answer["should_stop"] and not answer["payload"].strip():
                    raise ValueError("Empty payload")
                raw_payload = answer["payload"].strip().strip('"`')
                if raw_payload.lower().startswith("search="):
                    raw_payload = raw_payload[7:].strip()
                answer["payload"] = raw_payload
                suggestions.append(answer)
                return answer

            def checkpoint(row):
                report["partial_row"] = {**row, "branch": name, "run_no": number + 1,
                    "api_calls": client.calls[start:], "suggestions": suggestions}
                save(output, report)

            internal = "wordlist_static" if name == "wordlist_static" else "fixed_candidates" if name == "llm_static" else "heuristic_feedback"
            row = offline.run_branch(internal, budget, candidates=static if name == "llm_static" else None,
                proposer=propose if name == "llm_feedback" else None, on_update=checkpoint)
            row.update(branch=name, run_no=number + 1,
                mode="offline" if name == "wordlist_static" else "live_generated_static" if name == "llm_static" else "live",
                api_calls=client.calls[start:], suggestions=suggestions,
                ai_api_requests=len(client.calls) - start)
            for attempt in row["attempts"]:
                attempt["mode"] = row["mode"]
            if name == "llm_feedback" and row["stop_reason"] == "model_stopped" and len(client.calls) - start >= max_ai_calls:
                row["stop_reason"] = "ai_budget_exhausted"
            report.pop("partial_row", None)
            report["rows"].append(row)
            save(output, report)
            if row["stop_reason"] in ("ai_error", "transport_error", "precondition_failed"):
                report["api_calls"] = client.calls
                save(output, report)
                return report
    report["snapshot_consistent"] = len({r.get("snapshot_sha256") for r in report["rows"]}) == 1
    report["sources_unchanged"] = hashes == {p.relative_to(offline.ROOT).as_posix(): offline.digest(p.read_bytes()) for p in sources}
    report["status"] = "completed" if report["snapshot_consistent"] and report["sources_unchanged"] else "incomplete"
    report["api_calls"] = client.calls
    save(output, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--budget", type=int, default=50)
    parser.add_argument("--max-ai-calls", type=int, default=10)
    parser.add_argument("--env-file", type=Path, default=Path("ai/.env"))
    args = parser.parse_args()
    url = offline.urllib.parse.urlsplit(args.base_url)
    if url.scheme != "http" or url.hostname not in {"localhost", "127.0.0.1", "::1"} or url.username or url.password or url.path not in ("", "/") or url.query or url.fragment:
        parser.error("Expected local HTTP origin")
    if min(args.runs, args.budget, args.max_ai_calls) <= 0:
        parser.error("Budgets must be positive")
    load_environment(args.env_file)
    with AIClient(mode="live", min_interval_seconds=20) as client:
        report = benchmark(args.output, args.base_url.rstrip("/"), args.runs, args.budget, args.max_ai_calls, client)
    print(f"status={report['status']}; rows={len(report['rows'])}; output={args.output}")
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
