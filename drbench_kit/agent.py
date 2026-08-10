"""A minimal, Docker-free baseline "agent".

The real DRBench benchmark makes an agent *navigate* a live enterprise
environment (Nextcloud, email, chat) over MCP to discover the documents. This
kit removes that: it hands the agent the task's textualized documents directly
(insight-bearing AND distractor files) and asks for a report. It measures report
writing / synthesis quality, not live retrieval. Swap this out for your own agent
if you want to study retrieval.
"""
import os
from typing import Optional

from drbench_kit import llm

_PROMPT = """You are an enterprise research analyst writing a deep-research report.

Answer the QUESTION using ONLY the INTERNAL DOCUMENTS provided below. Some of the
documents are distractors that are not relevant to the question; use judgement and
do not include irrelevant facts. Be specific: pull out concrete facts, numbers, dates,
and findings. After each claim, cite the source file in square brackets, e.g.
[IN0001/food-safety.md]. End with a "Citations" section listing the files you used.

QUESTION:
{question}

SUB-QUESTIONS TO COVER:
{subquestions}

INTERNAL DOCUMENTS:
{documents}

Write the report now."""


def generate_report(task, model: Optional[str] = None, max_doc_chars: int = 120_000) -> str:
    """Produce a report for `task` by giving an LLM the task's documents. No Docker."""
    model = model or os.environ.get("AGENT_MODEL", "openai/gpt-4o-mini")
    docs = task.documents_text()
    if len(docs) > max_doc_chars:
        docs = docs[:max_doc_chars] + "\n\n[... documents truncated for length ...]"
    subq = "\n".join(f"- {s}" for s in task.subquestions) or "- (none provided)"
    prompt = (_PROMPT
              .replace("{question}", task.question)
              .replace("{subquestions}", subq)
              .replace("{documents}", docs))
    return llm.chat(prompt, model=model, temperature=0.2, max_tokens=4096)
