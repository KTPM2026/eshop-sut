"""Plot a completed three-strategy live log without treating failures as speedups."""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Refusing to overwrite an existing chart")
    report = json.loads(args.source.read_text(encoding="utf-8"))
    if (report.get("status") != "completed" or not report.get("snapshot_consistent")
            or not report.get("sources_unchanged")):
        parser.error("Expected a completed, consistent live benchmark")
    names = ("wordlist_static", "llm_static", "llm_feedback")
    groups = [[r for r in report["rows"] if r["branch"] == name] for name in names]
    if len(report["rows"]) != 9 or any(sorted(r["run_no"] for r in rs) != [1, 2, 3] for rs in groups):
        parser.error("Expected exactly three runs per strategy")
    if any(r["attack_requests"] != len(r["attempts"]) for rs in groups for r in rs):
        parser.error("Attack counts do not match attempts")
    labels = ("Wordlist", "LLM static", "LLM feedback")
    colors = ("#426a9b", "#ac743a", "#34816c")
    success = [sum(r["bypass"] for r in rs) for rs in groups]
    attacks = [sum(r["attack_requests"] for r in rs) / len(rs) for rs in groups]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8))
    for ax, values, title in zip(axes, (success, attacks),
            ("Successful runs (out of 3)", "Attack requests sent per run (mean)")):
        bars = ax.bar(labels, values, color=colors)
        ax.set_title(title)
        ax.set_ylim(0, max(3, max(values)) + 1.5)
        ax.spines[["top", "right"]].set_visible(False)
        ax.bar_label(bars, labels=[f"{value:g}" for value in values], padding=4)
    fig.suptitle("A2 live — independent rerun, 2026-10-25")
    fig.text(0.5, 0.04,
        "Static: no verified success. Feedback succeeded on its first request in each run.\n"
        "Request count excludes setup and AI calls; it does not measure elapsed time.",
        ha="center", fontsize=9)
    fig.tight_layout(rect=(0, 0.13, 1, 0.93))
    with args.output.open("xb") as stream:
        fig.savefig(stream, format=args.output.suffix.lstrip("."), metadata={"Creator": "A2 benchmark plot"})
    plt.close(fig)


if __name__ == "__main__":
    main()
