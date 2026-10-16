"""Xuất hợp đồng JSON cho Long/Lân, không gọi API."""

import argparse
import json
from pathlib import Path

from .contracts import json_contracts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("contracts.json"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(json_contracts(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(args.output))


if __name__ == "__main__":
    main()
