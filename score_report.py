#!/usr/bin/env python3
"""Score a report you already have against a task's gold, no Docker.

    python score_report.py --task DR0001 --report my_report.txt
    python score_report.py --task DR0001 --report my_report.md --out result.json
"""
import argparse
import json

from dotenv import load_dotenv

load_dotenv()

from drbench_kit import load_task
from drbench_kit.score import score_all


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", required=True, help="task id, e.g. DR0001")
    ap.add_argument("--report", required=True, help="path to a .txt/.md report file")
    ap.add_argument("--judge-model", default=None, help="override JUDGE_MODEL (default openai/gpt-4o)")
    ap.add_argument("--out", default=None, help="optional path to write the full JSON result")
    args = ap.parse_args()

    task = load_task(args.task)
    with open(args.report, encoding="utf-8") as f:
        report_text = f.read()

    print(task.summary(), "\n")
    result = score_all(report_text, task, judge_model=args.judge_model)

    print("\n================ SCORES ================")
    print(f"  insights_recall    = {result['insights_recall']:.3f}   (higher better)")
    print(f"  distractor_recall  = {result['distractor_recall']:.3f}   (lower better)")
    print(f"  report_quality     = {result['report_quality']:.3f}   (higher better)")
    print("=======================================")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nFull result written to {args.out}")


if __name__ == "__main__":
    main()
