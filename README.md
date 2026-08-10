# DRBench, no-Docker kit

A small, self-contained way to work with **[DRBench](https://github.com/ServiceNow/drbench)**
(ServiceNow's enterprise deep-research benchmark) **without Docker**: the task
corpus, the gold answers, runnable code to write a report and score it, and the
three original DRBench metrics reproduced faithfully.

If you just want to understand DRBench, read tasks, score reports, or try your own
agent on the task data, you do **not** need the enterprise container. This kit gives
you everything that isn't the live enterprise environment.

---

## Why there's no Docker here

The full DRBench harness spins up a fake enterprise (Nextcloud, Mattermost, email,
VNC) in Docker so that an **agent under test has to navigate those apps over MCP and
discover the right documents itself**, among distractors. That live retrieval is the
thing the full benchmark measures, and it is the only reason Docker exists in DRBench.

Everything else is plain text and plain Python:

- the **question** for each task,
- the **documents** (already textualized to `.md` / `.txt`),
- the **gold answers** (insights and planted distractors),
- the **scoring** (an LLM judge, no container).

So this kit hands the documents to a simple agent directly and scores the result. It
measures report writing and synthesis, not live retrieval. Swap in your own agent if
you want to study retrieval.

---

## What's inside

```
drbench-nodocker/
├── README.md
├── requirements.txt          # requests, python-dotenv  (that's all)
├── .env.example              # copy to .env, add your OpenRouter key
├── list_tasks.py             # browse the tasks               (no API key needed)
├── run_demo.py               # one task: agent writes a report, then scored
├── score_report.py           # score a report file you already have
├── run_set.py                # run over a whole set, print dataset means
├── examples/                 # two fake reports to score and compare
│   ├── good_report_DR0001.md
│   └── bad_report_DR0001.md
├── drbench_kit/
│   ├── llm.py                # tiny OpenRouter client (honors HTTP(S)_PROXY)
│   ├── task.py               # load a task: question, docs, persona, gold
│   ├── agent.py              # baseline no-Docker agent (LLM over the docs)
│   ├── score.py              # the 3 DRBench metrics, faithfully reproduced
│   └── prompts/              # judge prompts, copied verbatim from DRBench
└── data/
    ├── tasks/                # all 100 tasks (DR0001..DR0100), text only, no PDFs
    └── sets/
        ├── all.txt           # all 100 task ids
        └── core20.txt        # the curated core-20 subset
```

---

## Setup

Needs Python 3.9+.

```bash
# 1. create and activate a virtual environment
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

# 2. install (only two packages)
pip install -r requirements.txt

# 3. add your OpenRouter API key
copy .env.example .env         # macOS/Linux: cp .env.example .env
# then edit .env and set OPENROUTER_API_KEY=...   (get one at https://openrouter.ai/keys)
```

**On the office network:** a direct call to OpenRouter may time out because it's
blocked. Point the proxy env vars at the corporate proxy and `requests` will use them
automatically. Either add them to `.env`:

```
HTTPS_PROXY=http://proxy-dmz.intel.com:912
HTTP_PROXY=http://proxy-dmz.intel.com:912
```

or set them for the session in PowerShell before running:

```powershell
$env:HTTPS_PROXY = "http://proxy-dmz.intel.com:912"
$env:HTTP_PROXY  = "http://proxy-dmz.intel.com:912"
```

At home, leave them unset.

---

## Quick start

**1. Browse the tasks** (no key needed):

```bash
python list_tasks.py --set core --questions      # the curated 20, with questions
python list_tasks.py --set all                   # all 100 ids
```

**2. See the scorer work on the two example reports** (this is the best way to get it):

```bash
python score_report.py --task DR0001 --report examples/good_report_DR0001.md
python score_report.py --task DR0001 --report examples/bad_report_DR0001.md
```

Real output from this repo (gpt-4o judge):

| report                  | insights_recall | distractor_recall | report_quality |
|-------------------------|:---------------:|:-----------------:|:--------------:|
| `good_report_DR0001.md` | **0.833**       | **0.000**         | **0.880**      |
| `bad_report_DR0001.md`  | **0.000**       | **0.571**         | **0.420**      |

The good report covers the gold insights and avoids the planted distractors; the bad
one is vague, misses every gold insight, and repeats distractor facts. That contrast
is the whole point.

**3. Run the full loop on one task** (agent writes the report, then it's scored):

```bash
python run_demo.py --task DR0001
```

**4. Run over a whole set and get dataset means:**

```bash
python run_set.py --set core                 # the curated 20
python run_set.py --set all --out out/all.jsonl   # all 100 (slower, more API cost)
python run_set.py --set core --limit 3       # quick smoke test
```

`run_set.py` writes one JSON line per task to `--out` and is resumable (re-running
skips tasks already scored).

---

## Choosing which tasks: core vs all

Everything takes `--set`:

- `--set core` -> the curated 20 tasks (`data/sets/core20.txt`)
- `--set all`  -> all 100 tasks (`data/sets/all.txt`)
- `--set path/to/list.txt` -> your own list of task ids (one per line)

All 100 tasks are vendored either way; the set is just a filter.

---

## The three metrics (DRBench's originals)

All three are the LLM-judge metrics from DRBench, reproduced here from its own code
and prompts (`drbench_kit/prompts/` are copied verbatim). The judge defaults to
`openai/gpt-4o` (DRBench's judge); override with `JUDGE_MODEL`.

1. **`insights_recall`** — the report is split into atomic claims, then for each of the
   task's **gold insights** the judge decides (strictly) whether the report covers it.
   Score = fraction covered. **Higher is better.**

2. **`distractor_recall`** — the exact same judge, but run over the task's **planted
   distractor** facts. Score = fraction the report wrongly included. **Lower is
   better.** (Report avoidance = 1 - distractor_recall.)

3. **`report_quality`** — the judge rates the report 1-10 on five criteria (depth,
   relevance to the question, persona consistency, coherence/conciseness, and absence
   of contradictions), averaged and divided by 10 to give 0-1. **Higher is better.**

Each task's gold lives in `data/tasks/<id>/config/eval.json` (`dr_report_evaluation_qa`,
split by `qa_type` into `insight` vs `distractor`); the persona used by
`report_quality` is in `config/task.json`.

---

## How faithful is this to the real DRBench?

- **Scoring:** faithful. The judge prompts are copied verbatim and the metric logic
  (`insights_recall` = DRBench's `QASimilarityV2`, `distractor_recall` = the same over
  distractors, `report_quality` = DRBench's `ReportQuality`) matches its source.
- **What's different:** the *agent* here is a baseline that receives the documents
  directly instead of retrieving them from the live enterprise apps. Absolute scores
  are therefore not comparable to leaderboard runs that include live retrieval; use
  this to compare reports/agents against each other on the same task data.
- **Omitted:** DRBench's `factuality` metric (it needs the file corpus wired through
  the package's embedding search); the three metrics here are the report-level ones.

---

## Getting the original PDFs / the full corpus

This kit ships the **textualized** documents (`.md` / `.txt`) — the same text an agent
would read — but not the source PDFs/DOCX/PPTX, to keep it light. The full corpus,
including the originals and the Docker harness, is public:

```bash
git clone https://github.com/ServiceNow/drbench
```

---

## Attribution & license

The task data and the judge prompts are from **ServiceNow DRBench**
(<https://github.com/ServiceNow/drbench>), licensed under Apache 2.0. See
[`ATTRIBUTION.md`](ATTRIBUTION.md) and [`LICENSE`](LICENSE). This kit is a thin,
Docker-free wrapper around that work.
