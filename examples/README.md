# Example reports (fake inputs to play with)

Two hand-written reports for task **DR0001** so you can see the scorer work without
running the agent. One is good, one is bad. Score them and compare:

```bash
python score_report.py --task DR0001 --report examples/good_report_DR0001.md
python score_report.py --task DR0001 --report examples/bad_report_DR0001.md
```

What to expect (the point of the exercise):

| file                    | insights_recall | distractor_recall | report_quality | why |
|-------------------------|-----------------|-------------------|----------------|-----|
| `good_report_DR0001.md` | high (near 1.0) | ~0                | higher         | covers the 6 gold insights, avoids the distractor facts |
| `bad_report_DR0001.md`  | ~0              | high              | lower          | vague, misses every gold insight, and pulls in 4 planted distractor facts (turnover, training, renovation, energy) |

Reminder of what each metric means:
- **insights_recall** - fraction of the task's gold insights the report covers. Higher is better.
- **distractor_recall** - fraction of the *planted distractor* facts the report wrongly includes. Lower is better.
- **report_quality** - a judge's 0-1 rating (depth, relevance, persona fit, coherence, contradictions). Higher is better.

Now open `data/tasks/DR0001/` and read the actual documents the facts came from, then
write your own report and score it the same way.
