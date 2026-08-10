#!/usr/bin/env python3
"""List the tasks in a set (no API key needed).

    python list_tasks.py --set core          # the curated 20
    python list_tasks.py --set all           # all 100
    python list_tasks.py --set core --questions
"""
import argparse

from drbench_kit import list_tasks, load_task


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", dest="which", default="all",
                    help="'all' (100), 'core' (20), or a path to a .txt list of task ids")
    ap.add_argument("--questions", action="store_true", help="also print each task's question")
    args = ap.parse_args()

    ids = list_tasks(args.which)
    print(f"{len(ids)} tasks in set '{args.which}':\n")
    for t in ids:
        if args.questions:
            try:
                q = load_task(t).question
            except Exception as e:  # noqa: BLE001
                q = f"<error: {e}>"
            print(f"  {t}  {q}")
        else:
            print(f"  {t}")


if __name__ == "__main__":
    main()
