#!/usr/bin/env python3
"""End-to-end demo on ONE task, no Docker:
   load task -> write a report with the baseline agent -> score all 3 DRBench metrics.

    python run_demo.py --task DR0001
"""
import argparse

from dotenv import load_dotenv

load_dotenv()

from drbench_kit import load_task, generate_report
from drbench_kit.score import score_all


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", default="DR0001", help="task id, e.g. DR0001")
    ap.add_argument("--agent-model", default=None, help="override AGENT_MODEL (default openai/gpt-4o-mini)")
    ap.add_argument("--judge-model", default=None, help="override JUDGE_MODEL (default openai/gpt-4o)")
    args = ap.parse_args()

    task = load_task(args.task)
    print(task.summary())
    print("\n[1/2] Writing a report with the baseline agent (LLM over the task documents)...\n")
    report = generate_report(task, model=args.agent_model)
    print("===== REPORT =====")
    print(report)
    print("==================\n")

    print("[2/2] Scoring the three DRBench metrics with the judge...\n")
    result = score_all(report, task, judge_model=args.judge_model)

    print("\n================ SCORES ================")
    print(f"  insights_recall    = {result['insights_recall']:.3f}   (higher better)")
    print(f"  distractor_recall  = {result['distractor_recall']:.3f}   (lower better)")
    print(f"  report_quality     = {result['report_quality']:.3f}   (higher better)")
    print("=======================================")


if __name__ == "__main__":
    main()
