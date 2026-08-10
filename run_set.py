#!/usr/bin/env python3
"""Run the baseline agent + score all 3 metrics over a whole task set, no Docker.
Writes one JSON line per task and prints the dataset means. Resumable (skips
tasks already in the output file).

    python run_set.py --set core                 # curated 20
    python run_set.py --set all --out out/all.jsonl
    python run_set.py --set core --limit 3       # quick smoke
"""
import argparse
import json
import os

from dotenv import load_dotenv

load_dotenv()

from drbench_kit import list_tasks, load_task, generate_report
from drbench_kit.score import score_all


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", dest="which", default="core", help="'all', 'core', or a path to a .txt list")
    ap.add_argument("--out", default="out/results.jsonl", help="output JSONL path")
    ap.add_argument("--agent-model", default=None)
    ap.add_argument("--judge-model", default=None)
    ap.add_argument("--limit", type=int, default=None, help="only run the first N tasks")
    args = ap.parse_args()

    ids = list_tasks(args.which)
    if args.limit:
        ids = ids[:args.limit]

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    done = set()
    if os.path.exists(args.out):
        with open(args.out, encoding="utf-8") as f:
            for line in f:
                try:
                    done.add(json.loads(line)["task_id"])
                except Exception:  # noqa: BLE001
                    pass

    rows = []
    with open(args.out, "a", encoding="utf-8") as f:
        for t in ids:
            if t in done:
                print(f"skip {t} (already scored)")
                continue
            print(f"\n===== {t} =====")
            task = load_task(t)
            report = generate_report(task, model=args.agent_model)
            res = score_all(report, task, judge_model=args.judge_model, verbose=False)
            row = {
                "task_id": t,
                "insights_recall": res["insights_recall"],
                "distractor_recall": res["distractor_recall"],
                "report_quality": res["report_quality"],
            }
            f.write(json.dumps(row) + "\n")
            f.flush()
            rows.append(row)
            print(f"  insights_recall={row['insights_recall']:.3f}  "
                  f"distractor_recall={row['distractor_recall']:.3f}  "
                  f"report_quality={row['report_quality']:.3f}")

    # aggregate over everything in the out file (including prior runs)
    allrows = []
    with open(args.out, encoding="utf-8") as f:
        for line in f:
            try:
                allrows.append(json.loads(line))
            except Exception:  # noqa: BLE001
                pass
    if allrows:
        n = len(allrows)
        def mean(k):
            return sum(r[k] for r in allrows) / n
        print("\n================ DATASET MEANS ================")
        print(f"  tasks              = {n}")
        print(f"  insights_recall    = {mean('insights_recall'):.3f}   (higher better)")
        print(f"  distractor_recall  = {mean('distractor_recall'):.3f}   (lower better)")
        print(f"  report_quality     = {mean('report_quality'):.3f}   (higher better)")
        print("==============================================")


if __name__ == "__main__":
    main()
