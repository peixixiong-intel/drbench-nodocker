"""DRBench's three original report metrics, reproduced faithfully, no Docker.

  1. insights_recall   - fraction of GOLD insights the report covers      (higher better)
  2. distractor_recall - fraction of planted DISTRACTORS the report covers (lower better)
  3. report_quality    - LLM judge, 5 criteria averaged, 0..1             (higher better)

Metrics 1 and 2 are the same judge (QASimilarityV2 in DRBench) run over different
gold lists. Metric 3 is DRBench's ReportQuality judge. The judge prompts in
`prompts/` are copied verbatim from DRBench.
"""
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

from drbench_kit import llm

PROMPTS = Path(__file__).resolve().parent / "prompts"


def _judge_model(model: Optional[str]) -> str:
    return model or os.environ.get("JUDGE_MODEL", "openai/gpt-4o")


def _load_prompt(name: str) -> str:
    return (PROMPTS / name).read_text(encoding="utf-8")


def _extract_json(text: str):
    m = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    return json.loads(text.strip())


# ---------------------------------------------------------------- report -> claims

def break_report_to_insights(report_text: str, model: Optional[str] = None,
                             max_retries: int = 3) -> List[dict]:
    """Split a report into atomic {claim, citations} items (DRBench's own prompt)."""
    model = _judge_model(model)
    prompt = _load_prompt("break_report_to_insights.txt").replace("{report_text}", report_text)
    for _ in range(max_retries):
        try:
            resp = llm.chat(prompt, model=model, temperature=0, max_tokens=4096).strip()
            s, e = resp.find("["), resp.rfind("]")
            if s != -1 and e != -1 and e > s:
                arr = json.loads(resp[s:e + 1])
                out = []
                for it in arr:
                    if isinstance(it, dict) and "claim" in it:
                        claim = (it.get("claim") or "").strip()
                        cites = it.get("citations") if isinstance(it.get("citations"), list) else []
                        if len(claim) >= 10:
                            out.append({"claim": claim, "citations": cites})
                return out
        except Exception:
            continue
    return []


def _claims_text(insights: List[dict]) -> str:
    if not insights:
        return "No claims found in the report."
    return "\n".join(f"Insight {i}: {ins['claim']}" for i, ins in enumerate(insights, 1)).strip()


# ---------------------------------------------------------------- recall (shared judge)

def _coverage_recall(gold_list: List[str], claims_text: str, model: str,
                     verbose: bool = True) -> dict:
    """For each gold item, ask the judge if the report covers it (yes/no).
    Score = fraction covered. This is DRBench's QASimilarityV2 core."""
    template = _load_prompt("insight_scoring.txt")
    per = []
    for gold in gold_list:
        prompt = template.replace("{claims_text}", claims_text).replace("{gold_insight}", gold)
        answer, justification, selected = "no", "", None
        for _ in range(3):
            try:
                js = _extract_json(llm.chat(prompt, model=model, temperature=0, max_tokens=1024))
                answer = str(js.get("answer", "no")).strip().lower()
                justification = js.get("justification", "")
                selected = js.get("selected_insight")
                break
            except Exception:
                continue
        score = 1.0 if answer == "yes" else 0.0
        per.append({"gold": gold, "answer": answer, "score": score,
                    "selected_insight": selected, "justification": justification})
        if verbose:
            print(f"    [{'HIT' if score else '   '}] {gold[:88]}")
    total = len(per)
    covered = int(sum(p["score"] for p in per))
    return {"score": covered / total if total else 0.0, "covered": covered,
            "total": total, "per_item": per}


def insights_recall(report_text: str, task, model: Optional[str] = None,
                    report_insights: Optional[List[dict]] = None, verbose: bool = True) -> dict:
    """Fraction of the task's GOLD insights covered by the report (higher = better)."""
    model = _judge_model(model)
    insights = report_insights if report_insights is not None else break_report_to_insights(report_text, model)
    if verbose:
        print(f"  insights_recall  ({len(task.gold_insights)} gold insights):")
    res = _coverage_recall(task.gold_insights, _claims_text(insights), model, verbose)
    res["num_report_insights"] = len(insights)
    return res


def distractor_recall(report_text: str, task, model: Optional[str] = None,
                      report_insights: Optional[List[dict]] = None, verbose: bool = True) -> dict:
    """Fraction of planted DISTRACTORS wrongly included by the report (lower = better).
    report_avoidance = 1 - distractor_recall."""
    model = _judge_model(model)
    insights = report_insights if report_insights is not None else break_report_to_insights(report_text, model)
    if verbose:
        print(f"  distractor_recall  ({len(task.gold_distractors)} planted distractors):")
    res = _coverage_recall(task.gold_distractors, _claims_text(insights), model, verbose)
    res["num_report_insights"] = len(insights)
    return res


# ---------------------------------------------------------------- report_quality

_RQ_KEYS = ["depth_quality", "relevance_to_question", "persona_consistency",
            "coherence_conciseness", "contradictions"]


def _parse_report_quality(response: str) -> dict:
    def extract_block(tag):
        pat = (rf"<{tag}>\s*<score>\s*(.*?)\s*</score>\s*<justification>\s*(.*?)"
               rf"\s*</justification>\s*</{tag}>")
        m = re.search(pat, response, re.DOTALL | re.IGNORECASE)
        if m:
            try:
                score = int(float(m.group(1).strip()))
                score = max(1, min(10, score))
                return {"score": score / 10.0, "justification": m.group(2).strip()}
            except (ValueError, AttributeError):
                pass
        m = re.search(rf"<{tag}>.*?<score>\s*(.*?)\s*</score>.*?</{tag}>", response, re.DOTALL | re.IGNORECASE)
        if m:
            try:
                score = max(1, min(10, int(float(m.group(1).strip()))))
                return {"score": score / 10.0, "justification": "No justification provided"}
            except (ValueError, AttributeError):
                pass
        return {"score": 0.0, "justification": f"No valid response found for {tag}"}

    detail = {k: extract_block(k) for k in _RQ_KEYS}
    valid = sum(1 for k in _RQ_KEYS
                if detail[k]["score"] > 0 or "No valid response" not in detail[k]["justification"])
    avg = sum(detail[k]["score"] for k in _RQ_KEYS) / len(_RQ_KEYS)
    return {"score": avg, "detail": detail, "valid_criteria": valid}


def report_quality(report_text: str, task, model: Optional[str] = None,
                   verbose: bool = True, max_retries: int = 3) -> dict:
    """DRBench ReportQuality: judge 5 criteria (1-10 each), average / 10 -> 0..1."""
    model = _judge_model(model)
    prompt = (_load_prompt("report_quality.txt")
              .replace("{persona}", json.dumps(task.persona, indent=2))
              .replace("{dr_question}", task.question)
              .replace("{report}", report_text))
    result = None
    for _ in range(max_retries):
        try:
            parsed = _parse_report_quality(llm.chat(prompt, model=model, temperature=0, max_tokens=2048))
            if parsed["valid_criteria"] >= len(_RQ_KEYS):
                result = parsed
                break
            result = parsed  # keep best effort
        except Exception:
            continue
    if result is None:
        result = {"score": 0.5, "detail": {k: {"score": 0.5, "justification": "eval failed"} for k in _RQ_KEYS},
                  "valid_criteria": 0}
    if verbose:
        print(f"  report_quality = {result['score']:.3f}  "
              + "  ".join(f"{k.split('_')[0]}={result['detail'][k]['score']:.1f}" for k in _RQ_KEYS))
    return result


# ---------------------------------------------------------------- all three at once

def score_all(report_text: str, task, judge_model: Optional[str] = None, verbose: bool = True) -> dict:
    """Compute DRBench's three original metrics. Breaks the report into insights once
    and reuses it for both recall metrics."""
    model = _judge_model(judge_model)
    insights = break_report_to_insights(report_text, model=model)
    ir = insights_recall(report_text, task, model=model, report_insights=insights, verbose=verbose)
    dr = distractor_recall(report_text, task, model=model, report_insights=insights, verbose=verbose)
    rq = report_quality(report_text, task, model=model, verbose=verbose)
    return {
        "task_id": task.task_id,
        "insights_recall": ir["score"],
        "distractor_recall": dr["score"],
        "report_quality": rq["score"],
        "detail": {"insights_recall": ir, "distractor_recall": dr, "report_quality": rq},
    }
