# Attribution

This kit is derived from **DRBench** by ServiceNow:
<https://github.com/ServiceNow/drbench>, licensed under the Apache License 2.0
(see `LICENSE`).

Reused from DRBench:

- **Task data** under `data/tasks/` — the questions, textualized documents, and gold
  answers. (PDFs/DOCX/PPTX originals and the Docker enterprise harness are not
  redistributed here; get them from the upstream repo.)
- **Judge prompts** under `drbench_kit/prompts/` (`insight_scoring.txt`,
  `break_report_to_insights.txt`, `report_quality.txt`) — copied verbatim.
- **Metric logic** in `drbench_kit/score.py` — a faithful reimplementation of
  DRBench's `QASimilarityV2` (insights_recall / distractor_recall) and `ReportQuality`.

New in this kit: the Docker-free task loader, the baseline agent, the OpenRouter
client, and the runnable command-line scripts.
