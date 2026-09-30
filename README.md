# 🛡️ VeriDoc

**A PDF chatbot that tells you when it isn't sure.**
Standard RAG (chunk → embed → retrieve → generate), plus a **grounding layer**: before an answer is
shown, every claim in it is checked against the retrieved text. Claims the document does not back are
flagged, and if nothing can be verified VeriDoc says *"Not found in the document"* instead of guessing.

## How it works

```
PDF ─► PyMuPDF ─► sentence-aware chunks (~350 tok, overlap, exact page) ─► MiniLM embeddings ─► ChromaDB
                                                                                                   │
question ─► embed ─► top-k chunks ──► similarity below cutoff? ──yes──► "Not found" (no LLM call)  │
                         │ no                                                                      │
                         ▼                                                                         │
              LLM answers from ONLY those chunks, citing [n]  ── says NOT_FOUND? ──► "Not found"   │
                         │                                                                         │
                         ▼                                                                         │
              GROUNDING CHECK (per claim)                                                          │
                ├─ LLM verifier: decompose into claims, each needs a verbatim quote,               │
                │                quote is then string-matched against the cited chunk              │
                └─ NLI verifier: local entailment model (DeBERTa) scores chunk-window ⊨ claim      │
                         ▼
   all claims supported ► ✅ Grounded    some ► ⚠️ Partial (weak claims flagged)
   none supported ► ⛔ Not grounded (answer withheld, draft kept behind an expander)
   verifier crashed / bad JSON ► "unverified" warning (fails closed, never shown as grounded)
```

The UI shows a coloured grounding badge, a ✅/❌ line per claim with the supporting page, and the
retrieved chunks with the supporting quote highlighted.

### Design decisions worth knowing
* **The verifier can't just say "yes".** In LLM mode a claim only counts as supported if the verifier
  supplies a source number *and* a quote that is actually found in that chunk. An invented quote demotes the
  claim to unsupported (`tests/test_veridoc.py::test_verifier_cannot_assert_support_without_a_real_quote`).
* **Fail closed.** If the verifier errors, the answer is labelled *unverified*, never *grounded*.
* **Cheap abstention.** Off-topic questions are caught by a similarity cutoff before any LLM call.
* **Chunks never span pages**, so every citation has an exact page number.
* **Baseline mode** (grounding off) is built in, so you can demo the same question with and without the check.

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env          # add your free Groq key from console.groq.com
streamlit run app.py
```
Click **Load sample handbook** in the sidebar (a fictional company handbook, all facts invented) or upload your own PDF.

### Try this demo script
| Ask | Expected |
|---|---|
| How many days of annual leave do employees get? | ✅ Grounded, page 1 |
| What is the daily meal reimbursement limit for domestic travel? | ✅ Grounded, page 3 |
| What is the bereavement leave policy? | Not found in the document |
| How many stock options do new hires receive? | Not found in the document |
| Who is the CEO of Northwind Robotics? | Not found in the document |
| What is the capital of France? | Not found (off-topic cutoff, zero LLM calls) |

Then switch the sidebar to **Off (baseline RAG)** and ask the unanswerable ones again to see what an unchecked RAG does.

## Evaluation (mini ablation)

`eval/questions.json` holds 12 answerable and 10 unanswerable questions (8 plausible-but-absent, 2 off-topic)
over the sample handbook. `eval/run_eval.py` runs them through **baseline RAG**, the **LLM verifier** and the
**NLI verifier** and reports:

* **Answer rate** – answerable questions answered correctly
* **Hallucination rate** – unanswerable questions where an answer was shown anyway (lower is better)
* **Abstain rate** – its complement
* **Grounded precision** – of answers badged fully *grounded*, how many are correct

```bash
python eval/run_eval.py            # writes eval/results/results.md and results.json
```

| Config | Answer rate | Abstain rate | Hallucination rate | Grounded precision |
|---|---|---|---|---|
| Baseline RAG (no check) | _run the eval_ | | | |
| LLM verifier | | | | |
| NLI verifier | | | | |

> The table is intentionally empty until you run the script with your own API key. Paste the output here.

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```
21 offline tests (scripted LLM + hashing embedder, so no key or model download is needed) cover parsing,
chunking, claim splitting, the quote check, every pipeline outcome (grounded / partial / ungrounded / not found /
unverified / baseline), the NLI verifier, and a headless run of the Streamlit UI.

## Project layout

```
app.py                 Streamlit UI
veridoc/ingest.py      PDF → pages → chunks
veridoc/embeddings.py  sentence-transformers (+ offline hashing embedder for tests)
veridoc/store.py       ChromaDB wrapper
veridoc/rag.py         grounded-answer prompt
veridoc/grounding.py   LLM verifier + NLI verifier
veridoc/pipeline.py    orchestration and the grounded / partial / ungrounded decision
veridoc/render.py      badge + quote highlighting helpers
eval/                  question set and ablation runner
sample_docs/           fictional handbook + the script that generates it
tests/                 pytest suite
```

## Deploy (Streamlit Community Cloud)
1. Push the repo to GitHub. 2. share.streamlit.io → New app → main file `app.py`.
3. Advanced settings → Secrets: `GROQ_API_KEY = "your_key"`.

## Limitations
* Grounding checks *support*, not truth: a document that is itself wrong yields a "grounded" wrong answer.
* Scanned PDFs need OCR first; tables and multi-column layouts are extracted as plain text.
* Facts split across pages can't be combined in one chunk (top-k retrieval can still pull both pages).
* The NLI verifier is strict on paraphrase and numeric reasoning; the LLM verifier is more flexible but costs a second API call.
* The similarity cutoff (default 0.15) and NLI threshold (0.5) are starting points; tune them with the eval script.
