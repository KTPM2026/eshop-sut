"""Run existing H3 code with a disposable SQLite database, never the SUT DB."""

import argparse
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request


ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--budget", type=int, default=50)
    args = parser.parse_args()
    if args.output.exists() or args.runs <= 0 or args.budget <= 0:
        parser.error("output must be new and runs/budget must be positive")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    with tempfile.TemporaryDirectory(prefix="eshop-h3-") as directory:
        lab = Path(directory)
        for name in ("database.js", "server_fuzzer_lab.js", "waf_middleware.js"):
            shutil.copyfile(ROOT / "backend" / name, lab / name)
        environment = {**os.environ, "PORT": str(port), "WAF_ENABLED": "true", "WAF_LEVEL": "1",
                       "NODE_PATH": str(ROOT / "backend/node_modules"), "PYTHONDONTWRITEBYTECODE": "1"}
        with (lab / "server.log").open("w", encoding="utf-8") as log:
            process = subprocess.Popen(["node", str(lab / "server_fuzzer_lab.js")],
                cwd=lab, env=environment, stdout=log, stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            try:
                base = f"http://127.0.0.1:{port}"
                for _ in range(50):
                    if process.poll() is not None:
                        raise RuntimeError("Isolated H3 exited; check Node dependencies")
                    try:
                        with urllib.request.urlopen(base + "/api/products", timeout=1) as response:
                            if response.status == 200:
                                break
                    except OSError:
                        pass
                    time.sleep(0.1)
                else:
                    raise RuntimeError("Isolated lab did not become ready")
                return subprocess.run([sys.executable, "-X", "utf8", "-m",
                    "ai.A2_fuzzer_benchmark.offline", "--base-url", base,
                    "--runs", str(args.runs), "--budget", str(args.budget),
                    "--output", str(args.output.resolve())], cwd=ROOT, env=environment).returncode
            finally:
                if process.poll() is None:
                    process.terminate()
                process.wait(timeout=10)


if __name__ == "__main__":
    raise SystemExit(main())
