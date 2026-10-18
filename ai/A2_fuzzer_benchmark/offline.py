"""Reproducible SQLi-only local benchmark; no cloud calls or L2 cache writes."""

import argparse
import hashlib
import json
import sqlite3
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from demo.ai_fuzzer.ai_fuzzer import heuristic_adaptation
from demo.ai_fuzzer.benchmark_fuzzer import WORDLIST_PAYLOADS, AI_PREGENERATED_PAYLOADS


ROOT = Path(__file__).resolve().parents[2]
BASE = "http://localhost:3001"
BRANCHES = ("wordlist_static", "fixed_candidates", "heuristic_feedback")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode(data):
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def http(method, path):
    request = urllib.request.Request(BASE + path, method=method,
                                     data=b"{}" if method == "POST" else None,
                                     headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8", errors="replace")
    except OSError:
        return 0, "transport_error"


def rows(status, body):
    if status != 200:
        return None
    try:
        value = json.loads(body)
        if not isinstance(value, list):
            return None
        if any(not isinstance(row, dict) or type(row.get("id")) is not int
               or not isinstance(row.get("name"), str) for row in value):
            return None
        if len({row["id"] for row in value}) != len(value):
            return None
        return [{"id": row["id"], "name": row["name"]} for row in value]
    except (ValueError, TypeError):
        return None


def checkpoint(snapshot, payload, status, body):
    """Compare observed IDs to vulnerable and parameterized SQLite queries.

    This is a proposed lab oracle for the exact H3 name LIKE query, not XSS
    or a general SQLi detector. Only id/name are retained, never full products.
    """
    observed = rows(status, body)
    if observed is None:
        return {"bypass": None if status == 0 else False, "reason": "no_valid_result"}
    with closing(sqlite3.connect(":memory:")) as db:
        db.execute("CREATE TABLE products (id INTEGER, name TEXT)")
        db.executemany("INSERT INTO products VALUES (?, ?)",
                       [(row["id"], row["name"]) for row in snapshot])
        safe = sorted(row[0] for row in db.execute(
            "SELECT id FROM products WHERE name LIKE ?", ("%" + payload + "%",)))
        try:
            vulnerable = sorted(row[0] for row in db.execute(
                "SELECT id FROM products WHERE name LIKE '%" + payload + "%'"))
        except sqlite3.Error:
            return {"bypass": False, "reason": "unsupported_or_invalid_query"}
    actual = sorted(row["id"] for row in observed)
    names_match = all(row in snapshot for row in observed)
    passed = bool(actual) and names_match and actual == vulnerable and actual != safe
    return {"bypass": passed, "reason": "sql_effect_verified" if passed else "no_sql_effect",
            "observed_ids": actual, "parameterized_ids": safe, "vulnerable_ids": vulnerable}


def run_branch(branch, budget=50, request=http):
    if branch not in BRANCHES or type(budget) is not int or budget <= 0:
        raise ValueError("Invalid branch/budget")
    result = {"branch": branch, "mode": "offline", "budget": budget,
              "attempts": [], "auxiliary_requests": 0, "attack_requests": 0,
              "ai_api_requests": 0, "stop_reason": "precondition_failed",
              "total_sut_requests": 0,
              "request_to_first_success": None, "bypass": False}

    def auxiliary(method, path):
        result["auxiliary_requests"] += 1
        result["total_sut_requests"] += 1
        return request(method, path)

    reset_status, _ = auxiliary("POST", "/api/waf/reset")
    if reset_status != 200:
        return result
    status, body = auxiliary("GET", "/api/waf/status")
    try:
        config = json.loads(body)
    except ValueError:
        return result
    result["waf"] = config
    if status != 200 or config.get("waf_enabled") is not True or config.get("waf_level") != 1:
        return result
    status, body = auxiliary("GET", "/api/products")
    snapshot = rows(status, body)
    if not snapshot:
        return result
    result["snapshot"] = snapshot
    result["snapshot_sha256"] = digest(encode(snapshot))
    marker = "__no_product_" + uuid.uuid4().hex
    status, body = auxiliary("GET", "/api/products?search=" + marker)
    if rows(status, body) != []:
        return result
    result["baseline"] = {"payload": marker, "status": status, "result": []}
    static = WORDLIST_PAYLOADS if branch == "wordlist_static" else AI_PREGENERATED_PAYLOADS
    payload = "' OR '1'='1"
    for index in range(budget):
        if branch != "heuristic_feedback":
            if index >= len(static):
                result["stop_reason"] = "source_exhausted"
                break
            payload = static[index]
        started = time.perf_counter()
        status, body = request("GET", "/api/products?search=" + urllib.parse.quote(payload, safe=""))
        effect = checkpoint(snapshot, payload, status, body)
        result["attempts"].append({"attempt_no": index + 1, "payload": payload,
            "response_code": status, "checkpoint": effect, "bypass": effect["bypass"],
            "latency_ms": round((time.perf_counter() - started) * 1000, 3),
            "response_sha256": digest(body.encode("utf-8")), "mode": "offline"})
        if status == 0:
            result["stop_reason"] = "transport_error"
            break
        if effect["bypass"]:
            result.update(bypass=True, request_to_first_success=index + 1, stop_reason="success")
            break
        if branch == "heuristic_feedback":
            try:
                reason = json.loads(body).get("blocked_keyword", "")
            except (ValueError, AttributeError):
                reason = ""
            payload = heuristic_adaptation(str(reason), payload)
    else:
        result["stop_reason"] = "budget_exhausted"
    result["attack_requests"] = len(result["attempts"])
    result["total_sut_requests"] = result["attack_requests"] + result["auxiliary_requests"]
    return result


def main():
    global BASE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--budget", type=int, default=50)
    parser.add_argument("--base-url", default=BASE)
    args = parser.parse_args()
    parsed = urllib.parse.urlsplit(args.base_url)
    if (parsed.scheme != "http" or parsed.hostname not in ("localhost", "127.0.0.1", "::1")
            or parsed.username or parsed.password or parsed.path not in ("", "/")
            or parsed.query or parsed.fragment):
        parser.error("base-url must be a local HTTP origin")
    BASE = args.base_url.rstrip("/")
    if args.runs <= 0 or args.budget <= 0:
        parser.error("runs/budget must be positive")
    if args.output.exists():
        parser.error("Refusing to overwrite an existing artifact")
    sources = [Path(__file__), ROOT / "demo/ai_fuzzer/ai_fuzzer.py",
               ROOT / "demo/ai_fuzzer/benchmark_fuzzer.py", ROOT / "backend/waf_middleware.js",
               ROOT / "backend/server_fuzzer_lab.js", ROOT / "backend/database.js"]
    before = {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in sources}
    output = {"run_id": str(uuid.uuid4()), "created_at_utc": datetime.now(timezone.utc).isoformat(),
              "target": BASE, "oracle": "proposed_sqlite_differential_v1", "oracle_review": "pending_group_review",
              "model_inference_performed": False, "is_replay": False,
              "source_hashes": before,
              "sut_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "payload_sources": {"wordlist_static": WORDLIST_PAYLOADS,
                                  "fixed_candidates": AI_PREGENERATED_PAYLOADS,
                                  "notice": "Fixed list has no verified AI-generation provenance"},
              "rows": []}
    for number in range(args.runs):
        order = BRANCHES[number % 3:] + BRANCHES[:number % 3]
        for branch in order:
            row = run_branch(branch, args.budget)
            row["run_no"] = number + 1
            output["rows"].append(row)
    output["status"] = "completed" if all(r["stop_reason"] not in
        ("precondition_failed", "transport_error") for r in output["rows"]) else "incomplete"
    output["snapshot_consistent"] = len({r.get("snapshot_sha256") for r in output["rows"]}) == 1
    if not output["snapshot_consistent"]:
        output["status"] = "incomplete"
    output["sources_unchanged"] = before == {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in sources}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(encode(output))
    print(f"status={output['status']}; rows={len(output['rows'])}; output={args.output}")
    return 0 if output["status"] == "completed" and output["sources_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
