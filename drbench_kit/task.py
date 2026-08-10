"""Load a DRBench task straight from the vendored text corpus. No Docker."""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
TASKS_DIR = DATA_DIR / "tasks"
SETS_DIR = DATA_DIR / "sets"

TEXT_EXTS = (".md", ".txt")


@dataclass
class Document:
    name: str      # file name, e.g. food-safety-compliance.md
    folder: str    # containing folder, e.g. IN001_pdf / DI0003
    kind: str      # "insight" (IN...), "distractor" (DI...), or "other"
    text: str


@dataclass
class Task:
    task_id: str
    question: str
    subquestions: List[str]
    persona: dict                 # intended audience, used by report_quality
    documents: List[Document]
    gold_insights: List[str]      # qa_type == "insight"  -> insights_recall
    gold_distractors: List[str]   # qa_type == "distractor" -> distractor_recall
    dir: Path

    def documents_text(self, include_kind_label: bool = False) -> str:
        parts = []
        for d in self.documents:
            header = f"### FILE: {d.folder}/{d.name}"
            if include_kind_label:
                header += f"  [{d.kind}]"
            parts.append(f"{header}\n{d.text}")
        return "\n\n".join(parts)

    def summary(self) -> str:
        n_in = sum(1 for d in self.documents if d.kind == "insight")
        n_di = sum(1 for d in self.documents if d.kind == "distractor")
        return (
            f"{self.task_id}: {self.question}\n"
            f"  documents: {len(self.documents)} text files "
            f"({n_in} in insight-bearing folders, {n_di} in distractor folders)\n"
            f"  gold insights: {len(self.gold_insights)}  |  gold distractors: {len(self.gold_distractors)}"
        )


def _folder_kind(folder_name: str) -> str:
    up = folder_name.upper()
    if up.startswith("IN"):
        return "insight"
    if up.startswith("DI"):
        return "distractor"
    return "other"


def load_task(task_id: str, tasks_dir: Path = TASKS_DIR) -> Task:
    d = Path(tasks_dir) / task_id
    if not d.is_dir():
        raise FileNotFoundError(f"Task {task_id} not found under {tasks_dir}")

    q = json.loads((d / "dr_question.json").read_text(encoding="utf-8"))
    question = q.get("dr_question", "")
    subq = q.get("question_source", {}).get("subquestions", []) or []

    task_cfg = json.loads((d / "config" / "task.json").read_text(encoding="utf-8"))
    persona = task_cfg.get("persona", {}) or {}
    question = question or task_cfg.get("dr_question", "")

    eval_cfg = json.loads((d / "config" / "eval.json").read_text(encoding="utf-8"))

    def _gold(qa_type):
        return [
            qa["answer"]
            for qa in eval_cfg.get("dr_report_evaluation_qa", [])
            if qa.get("qa_type") == qa_type
            and qa.get("answer")
            and qa.get("answer") != "Not answerable"
        ]

    gold_insights = _gold("insight")
    gold_distractors = _gold("distractor")

    documents: List[Document] = []
    files_root = d / "files"
    if files_root.is_dir():
        for folder in sorted(files_root.iterdir()):
            if not folder.is_dir():
                continue
            kind = _folder_kind(folder.name)
            for f in sorted(folder.iterdir()):
                if f.is_file() and f.suffix.lower() in TEXT_EXTS:
                    documents.append(
                        Document(
                            name=f.name,
                            folder=folder.name,
                            kind=kind,
                            text=f.read_text(encoding="utf-8", errors="replace"),
                        )
                    )

    return Task(
        task_id=task_id,
        question=question,
        subquestions=subq,
        persona=persona,
        documents=documents,
        gold_insights=gold_insights,
        gold_distractors=gold_distractors,
        dir=d,
    )


def read_set(which: str = "all", sets_dir: Path = SETS_DIR) -> List[str]:
    """Resolve a task set. `which` is 'all', 'core' (== core20), or a path to a .txt list."""
    alias = {"core": "core20", "core20": "core20", "all": "all"}
    p = Path(sets_dir) / f"{alias.get(which, which)}.txt"
    if not p.is_file():
        p = Path(which)  # allow an explicit path
    if not p.is_file():
        raise FileNotFoundError(f"Task set '{which}' not found (looked for {p})")
    return [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]


def list_tasks(which: str = "all", sets_dir: Path = SETS_DIR) -> List[str]:
    return read_set(which, sets_dir=sets_dir)
