"""
drbench_kit: a Docker-free way to load DRBench tasks, generate a report with a
plain LLM, and score it with DRBench's own insights_recall judge.

No enterprise container, no MCP, no Nextcloud/Mattermost/mail. Just the task
text (question + documents), the gold answers, and the scoring logic.
"""

from drbench_kit.task import Task, load_task, list_tasks
from drbench_kit.agent import generate_report
from drbench_kit.score import (
    break_report_to_insights,
    insights_recall,
    distractor_recall,
    report_quality,
    score_all,
)

__all__ = [
    "Task",
    "load_task",
    "list_tasks",
    "generate_report",
    "break_report_to_insights",
    "insights_recall",
    "distractor_recall",
    "report_quality",
    "score_all",
]
