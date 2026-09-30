"""Stress test: answerable vs. unanswerable questions, for each grounding configuration.

Usage (needs GROQ_API_KEY and internet for the model downloads):
    python eval/run_eval.py                       # baseline + LLM verifier + NLI verifier
    python eval/run_eval.py --configs none llm    # only some configurations

Metrics
    answer rate         answerable questions that got a correct answer shown       (higher is better)
    abstain rate        unanswerable questions where no answer was shown           (higher is better)
    hallucination rate  unanswerable questions where an answer WAS shown           (lower is better)
    grounded precision  of answers flagged fully 'grounded', share that are correct
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

from veridoc import VeriDoc  # noqa: E402
from veridoc.grounding import LLMVerifier, NLIVerifier  # noqa: E402
from veridoc.llm import GroqLLM  # noqa: E402
from veridoc.pipeline import GROUNDED  # noqa: E402
from veridoc.rag import NAIVE_SYSTEM  # noqa: E402

ANSWER_STATUSES = {"grounded", "partial", "unchecked", "unverified"}


_NUMBER_WORDS = {"two": "2", "three": "3", "four": "4", "five": "5", "fourteen": "14",
                 "sixteen": "16", "twenty-five": "25", "thirty": "30"}


def _norm(text: str) -> str:
    """Lower-case, unify Unicode spaces (the model emits U+202F) and spell small numbers as digits."""
    text = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text).lower())
    for word, digit in _NUMBER_WORDS.items():
        text = re.sub(rf"\b{word}\b", digit, text)
    return text


def is_correct(answer: str, expect: list[str]) -> bool:
    return all(_norm(token) in _norm(answer) for token in expect)


def build(config: str, llm, embedder):
    verifier = {"none": None, "llm": LLMVerifier(llm), "nli": NLIVerifier(),
                "naive": None, "naive_llm": LLMVerifier(llm)}[config]
    kwargs = {"generation_system": NAIVE_SYSTEM} if config.startswith("naive") else {}
    return VeriDoc(llm, verifier, embedder, **kwargs)


def run_config(config: str, spec: dict, llm, embedder) -> tuple[dict, list[dict]]:
    app = build(config, llm, embedder)
    app.ingest_pdf((ROOT / spec["document"]).read_bytes(), Path(spec["document"]).name)

    rows: list[dict] = []
    for item in spec["answerable"]:
        r = app.ask(item["q"])
        shown = r.status in ANSWER_STATUSES
        rows.append({"type": "answerable", "q": item["q"], "status": r.status, "answer": r.answer,
                     "correct": shown and is_correct(r.answer, item["expect"])})
    for item in spec["unanswerable"]:
        r = app.ask(item["q"])
        rows.append({"type": "unanswerable", "q": item["q"], "kind": item["kind"], "status": r.status,
                     "answer": r.answer, "hallucinated": r.status in ANSWER_STATUSES})

    ans = [x for x in rows if x["type"] == "answerable"]
    una = [x for x in rows if x["type"] == "unanswerable"]
    grounded = [x for x in ans if x["status"] == GROUNDED]
    summary = {
        "config": config,
        "answer_rate": sum(x["correct"] for x in ans) / len(ans),
        "abstain_rate": sum(not x["hallucinated"] for x in una) / len(una),
        "hallucination_rate": sum(x["hallucinated"] for x in una) / len(una),
        "grounded_precision": (sum(x["correct"] for x in grounded) / len(grounded)) if grounded else None,
        "n_answerable": len(ans),
        "n_unanswerable": len(una),
    }
    return summary, rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--configs", nargs="+", default=["none", "llm", "nli"], choices=["none", "llm", "nli", "naive", "naive_llm"])
    parser.add_argument("--questions", default=str(ROOT / "eval" / "questions.json"))
    parser.add_argument("--tag", default="", help="suffix for the output files, e.g. _heldout")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    spec = json.loads(Path(args.questions).read_text())
    llm = GroqLLM()
    from veridoc.embeddings import SentenceTransformerEmbedder

    embedder = SentenceTransformerEmbedder()  # shared so the model loads once

    summaries, detail = [], {}
    for config in args.configs:
        t0 = time.time()
        summary, rows = run_config(config, spec, llm, embedder)
        summary["seconds"] = round(time.time() - t0, 1)
        summaries.append(summary)
        detail[config] = rows

    out_dir = ROOT / "eval" / "results"
    out_dir.mkdir(exist_ok=True)
    (out_dir / f"results{args.tag}.json").write_text(json.dumps({"summary": summaries, "detail": detail}, indent=2))

    fmt = lambda v: "n/a" if v is None else f"{v:.0%}"  # noqa: E731
    lines = ["| Config | Answer rate | Abstain rate | Hallucination rate | Grounded precision | Time (s) |",
             "|---|---|---|---|---|---|"]
    names = {"none": "Baseline RAG (no check)", "llm": "LLM verifier", "nli": "NLI verifier",
             "naive": "Naive prompt, no check", "naive_llm": "Naive prompt + LLM verifier"}
    for s in summaries:
        lines.append(f"| {names[s['config']]} | {fmt(s['answer_rate'])} | {fmt(s['abstain_rate'])} | "
                     f"{fmt(s['hallucination_rate'])} | {fmt(s['grounded_precision'])} | {s['seconds']} |")
    table = "\n".join(lines)
    (out_dir / f"results{args.tag}.md").write_text(table + "\n")
    print(table)


if __name__ == "__main__":
    main()
