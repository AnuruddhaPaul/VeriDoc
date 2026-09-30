# VeriDoc: hand-off brief for Claude Code (paste everything below the line)

How to use: `git clone https://github.com/AnuruddhaPaul/veridoc`, `cd veridoc`, start Claude Code in the repo root, and paste the whole brief below the line as your first message. (This private repo holds only the project, on `main`, at the repo root.)

---

You are taking over a student's final GenAI capstone project. It is due on the deadline below, so work in the order given, verify everything before claiming it works, and keep me informed in short messages. I am the student. Ask me for anything you cannot find in the repo, especially personal details for the report cover page.

## 0. Ground rules (read first)

1. **Never fabricate.** Every metric, test result, screenshot and log in the report must come from a real run you performed on this machine. If something fails, report the failure and put it in the report's test table. Do not smooth over it.
2. **Never print, log or commit my Groq API key.** I will put it in `.env` (repo root) myself (`GROQ_API_KEY=...`). Do not echo it, and do not include it in screenshots, the report or Drive files.
3. **Security clean-up (do this early):** my older repo `AnuruddhaPaul/AGNTIC_AI` has tracked `.env` files (root and `digital_safety_agent/`) containing Groq keys, so those keys are exposed. Tell me to revoke them at console.groq.com and create a new one, and to run `git rm --cached` on those files in that old repo. This new repo has no `.env`; check that `.env` stays in `.gitignore`. Do not paste any old key anywhere.
4. **Academic honesty:** the report must describe my own project and my own results, in clear plain English. Write the draft for me, but do not copy text from the sample report, and do not reuse its numbers. Its data is illustrative only.
5. **Git:** this repo (`AnuruddhaPaul/veridoc`, private) starts with one commit on `main`. Work on a feature branch, commit in small steps with clear messages, and ask me before pushing to `main`. The project was originally developed in `AnuruddhaPaul/AGNTIC_AI` (branch `claude/final-project-submission-uiz8m1`, draft PR #2); that copy is now just a backup.
6. **Date check:** the submission deadline is **30 September 2026**. Late submissions are not considered. Check today's date at the start. If the deadline has passed, tell me immediately and ask whether an extension exists before doing anything else.

## 1. The assignment

The course is a Generative AI / Agentic AI capstone. The instructor's submission form (https://forms.gle/rEvS7iFV3g6EPzX5A) asks for:

1. **Project details:** student information and project information.
2. **Working project upload:** project files in a Google Drive folder, shared with **Viewer access for everyone with the link**.
3. **GitHub repository link:** the project code, in a public repository.
4. **Hosted project link:** the live app (Streamlit Community Cloud or similar). Note that Vercel and Netlify cannot host a Streamlit/Python server, so use Streamlit Community Cloud, or Hugging Face Spaces as a fallback (see section 5).

Form rules:
- Submit with my **college email ID only**. Personal emails are rejected.
- **No edits after submitting**, so cross-check every link first.
- Verify all links are correct and accessible.
- I must supply the personal details myself: name, roll number, batch (GENAI 2026), trainer/faculty name.

Reference material (read before writing anything):
- The course guideline documents `Capstone_Project_Guidelines.docx` and `Agentic AI Project Guidance .docx` are NOT in this repo (they live in my older repo `AnuruddhaPaul/AGNTIC_AI`). Ask me to copy them into `docs/reference/`, read both, and follow them wherever they are stricter than this brief.
- If `GenAI_Sample_Project_Report.pdf` is in the repo (search under `docs/` or ask me for it), it is the format reference: a 16-page sample report called "TripMate", built as a 14-section structure. If it is missing, use the section list in section 7 below.

## 2. The project: VeriDoc

**One line:** a PDF question-answering chatbot that checks its own answers. Every claim in an answer is verified against the retrieved document text before display. If the document does not back the claim, VeriDoc flags it or says "Not found in the document" instead of guessing.

**Why it matters (use in the report's problem statement):** ordinary RAG chatbots answer confidently even when retrieval missed, and users cannot tell a grounded answer from an invented one. The grounding layer is the differentiator. It applies the hallucination-detection idea from vision-language work to text RAG.

**Pipeline:** PDF → PyMuPDF text extraction (per page) → sentence-aware chunks of about 350 tokens with about 60 tokens of overlap (chunks never cross pages, so every citation has an exact page) → `all-MiniLM-L6-v2` embeddings (sentence-transformers) → ChromaDB (cosine) → retrieve top-k (default 4) → similarity gate → Groq `llama-3.3-70b-versatile` answers using only the chunks, citing `[n]` → grounding check → decision → Streamlit UI.

**Decision logic (`veridoc/pipeline.py`):**
- best chunk similarity below `MIN_SIMILARITY` (0.15) → `not_found`, **no LLM call**
- model replies `NOT_FOUND` → `not_found`
- verification off → `unchecked` (baseline mode for comparison)
- verifier crashes or returns bad JSON → `unverified`, fail closed and never labelled grounded
- all claims supported → `grounded`; some → `partial` (weak claims flagged); none → `ungrounded` (answer withheld, draft kept behind an expander)

**Two verifiers (`veridoc/grounding.py`), which form the ablation study:**
- **LLM verifier:** a second Groq call, in JSON mode, splits the answer into atomic claims. Each supported claim must cite a source number and a **verbatim quote**, and the code then string-matches that quote against the cited chunk. An invented quote demotes the claim to unsupported.
- **NLI verifier:** a local entailment cross-encoder (`cross-encoder/nli-deberta-v3-small`) scores sliding 3-sentence windows of the chunks against each answer sentence. A claim is supported if the entailment probability is at least 0.5.

**Repo layout (repo root):**
```
app.py                  Streamlit UI (badge, claim-by-claim ✅/❌, highlighted evidence, baseline toggle)
veridoc/ingest.py       PDF -> pages -> chunks
veridoc/embeddings.py   MiniLM embedder (+ offline HashingEmbedder used only by tests)
veridoc/store.py        ChromaDB wrapper
veridoc/rag.py          grounded-answer prompt, NOT_FOUND handling
veridoc/grounding.py    LLMVerifier + NLIVerifier + quote check
veridoc/pipeline.py     orchestration and status decision
veridoc/render.py       badge text + quote highlighting
veridoc/llm.py          GroqLLM client (retry/backoff)
veridoc/config.py       all tunables via env vars
eval/questions.json     12 answerable + 10 unanswerable (8 in-domain-but-absent, 2 off-topic)
eval/run_eval.py        runs baseline / LLM / NLI, writes eval/results/results.{md,json}
sample_docs/            fictional "Northwind Robotics Employee Handbook" PDF + generator script
tests/                  21 offline pytest tests (scripted LLM + hashing embedder)
README.md, requirements*.txt, .env.example, .gitignore
```

## 3. Status: what is done and what is not

**Done and verified (in a sandbox with no internet to Groq/HF):**
- All code above is committed in this repo.
- 21/21 offline tests pass, including a headless run of the Streamlit script with a faked LLM/embedder. The tests already caught one real bug (`NOT_FOUND` was not recognised), which is fixed.
- The Streamlit server boots (`/_stcore/health` returned ok).

**NOT done and NOT verified. This is your job:**
- No live Groq call has ever been made. The prompts, JSON mode and the verifier's JSON shape are untested against the real model.
- MiniLM and the NLI model have never been downloaded or run. `load_nli_predictor` (label mapping through `id2label`) is untested against the real model.
- `eval/run_eval.py` has never run. The README results table is intentionally empty.
- Thresholds (`MIN_SIMILARITY=0.15`, `NLI_THRESHOLD=0.5`, `top_k=4`) are untuned guesses.
- No real screenshots, no report, no diagrams, no hosted deployment, no Drive folder, no dedicated submission repo.
- Known possible weak spots to look for: the free-tier Groq rate limit during the eval (about 90 calls; the client retries, so watch for failures); Streamlit Cloud's roughly 1 GB RAM with torch plus two models; chunk boundaries splitting facts across pages; the NLI verifier being too strict on paraphrase and numbers.

**Backend decision:** no separate backend and no Supabase. Streamlit is both the UI and the server, and ChromaDB runs in memory in the app. Only add Supabase (chat history or stored PDFs) if I explicitly ask, and only after everything else is submitted.

## 4. Work plan (do in this order; tell me when each step is done)

**Step 1: Environment**
1. `python -m venv .venv`, activate it, then `pip install -r requirements-dev.txt`.
2. Confirm I have created `.env` from `.env.example` with a fresh key. Never read the key back to me.
3. Run `pytest -q`. Expect 21 passing. Fix anything environment-specific.

**Step 2: Live smoke test.** In a short script or the REPL, do one real `GroqLLM.complete` call, one real embedding, and one full `VeriDoc.ask` on `sample_docs/northwind_handbook.pdf` with the LLM verifier. Check that the JSON parses, the quote check works, and the statuses come out as expected. Fix prompt or parsing bugs found here. Keep the offline tests green, and add a test for every bug you fix.

**Step 3: NLI verifier live.** Run it once. Confirm `id2label` maps to an "entailment" index, that probabilities look sane (an obviously supported claim should be well above 0.5, an unsupported one well below), and roughly how long it takes on this CPU.

**Step 4: Run the demo script by hand in the real app** (`streamlit run app.py`): 2 grounded questions, 3 unanswerable ones, 1 off-topic one, then the same unanswerable ones with grounding switched **Off** to show the baseline hallucinating. Note what the baseline actually did. That contrast is the strongest evidence in the report.

**Step 5: Run the eval** (`python eval/run_eval.py`). Save `eval/results/results.md` and `results.json`, and paste the table into `README.md`.
- If results are bad (many correct answers refused, or hallucinations slipping through), diagnose with the per-question rows in `results.json`. Tune `MIN_SIMILARITY`, `top_k` and `NLI_THRESHOLD`, or improve prompts, then re-run.
- Keep every run's numbers. Report the final run as the headline and mention what you tuned and why. **Do not tune on the questions and then present that as unbiased.** If you tune, say so, and preferably add a small held-out set of extra questions for the final number.
- Report failures honestly, including any answerable question that was refused and any hallucination that slipped through.

**Step 6: Real screenshots.** Use Playwright with Chromium (or take them manually) at a consistent window size (about 1400×900), on the real running app with real answers. Capture at least: (a) app home with sample doc loaded; (b) a ✅ grounded answer with the claim list and highlighted source; (c) a ⚠️ partial answer if one occurs naturally; (d) "Not found in the document"; (e) the off-topic cutoff refusal; (f) the same unanswerable question with grounding Off, side by side with the verified refusal; (g) the retrieved-sources panel with a highlighted quote. Crop cleanly and hide any API key field. Save as PNG in `docs/figures/`.

**Step 7: Diagrams** (specifications in section 6). Produce them as SVG and PNG at 300 dpi in `docs/figures/`.

**Step 8: Deploy.** Follow section 5.

**Step 9: Write the report.** Follow the specifications in section 7. Deliver **both `.docx` and `.pdf`**, built from the same content. Use the docx and pdf skills if they are available, or python-docx plus LibreOffice (`soffice --headless --convert-to pdf`). Render the PDF to images and inspect every page for layout problems before delivering.

**Step 10: Submission package.** Follow section 8.

Commit and push after each step. Update the README status honestly at the end.

## 5. Hosting (Streamlit Community Cloud, with fallback)

1. Ask me to merge PR #2, or deploy from the branch. I do the GitHub and Streamlit login steps myself; give me exact click-by-click instructions.
2. share.streamlit.io → New app → repository, branch, main file `app.py`. Under Advanced settings → Secrets add `GROQ_API_KEY = "..."` (I paste it myself).
3. Watch the build logs. If the app runs out of memory (about 1 GB on the free tier, and torch plus MiniLM plus the NLI model is tight):
   - first try a smaller hosted build: default the hosted app to the LLM verifier, load the NLI model lazily, and pin CPU-only torch in `requirements.txt`;
   - if that still fails, deploy to **Hugging Face Spaces** (Streamlit SDK, free 16 GB CPU): add the Spaces README metadata, set `GROQ_API_KEY` as a Space secret, and use that URL as the hosted link.
4. Test the hosted URL in a private/incognito window with the sample document: one grounded question and one unanswerable question. Save a screenshot of the hosted app with its URL visible. Confirm the app does not expose or log the key.
5. Keep the app awake around the submission. Free apps sleep, so open it shortly before I submit and mention the wake-up delay in the README.

## 6. Diagram specifications (block-diagram reference)

Make every figure with a consistent style: white background, sans-serif font at least 12 pt when printed at page width, rounded rectangles for processes, diamonds for decisions, cylinders for storage, arrows with short labels, and a small legend. Use one colour language everywhere:
- **Blue** = data and storage (PDF, chunks, ChromaDB)
- **Green** = LLM calls (Groq generator, LLM verifier)
- **Orange** = verification and checks
- **Grey** = UI and user
- **Red** = abstain or refuse exits
Draw with matplotlib, graphviz, Mermaid-CLI or draw.io, whichever you can render reliably. Number figures by section (Figure 6.1, 6.2, …), give each a caption, and always explain each figure in a short paragraph next to it.

**Figure 6.1: System architecture (block diagram), left to right, two lanes.**
- *Ingestion lane (top):* `PDF upload` → `PyMuPDF parser (page text)` → `Sentence chunker (~350 tok, overlap, page kept)` → `MiniLM embedder (all-MiniLM-L6-v2)` → `ChromaDB (cosine)`.
- *Query lane (bottom):* `User question` → `Embed question` → `Retrieve top-k chunks` (arrow from ChromaDB) → **diamond** `Similarity ≥ cutoff?` (No → red `Not found, no LLM call`) → `Generator: Groq Llama-3.3-70B, sources only, cites [n]` → **diamond** `Model said NOT_FOUND?` (Yes → red `Not found`) → `Grounding verifier (LLM or NLI)` → `Decision` → `Streamlit UI`.
- The Decision block fans out to four labelled outcomes: `Grounded`, `Partial (flag weak claims)`, `Ungrounded (withhold answer)`, `Unverified (verifier failed)`.

**Figure 6.2: Decision state diagram.** Inputs (similarity, NOT_FOUND, verifier result) on the left; the six statuses (`not_found`, `unchecked`, `unverified`, `grounded`, `partial`, `ungrounded`) on the right, with the condition on each arrow.

**Figure 7.1: LLM verifier sequence.** Answer + numbered sources → verifier splits into claims → each claim returns `supported, source, quote` → **code checks the quote is verbatim in the cited chunk** (highlight this step, because it is the safeguard) → verdict kept or demoted to unsupported.

**Figure 9.1: Results chart.** Grouped bars for baseline vs LLM verifier vs NLI verifier showing answer rate and hallucination rate, with the percentage on each bar. Read the dataviz skill first if available. Use only real numbers from `results.json`.

**Figure 10.x: Screenshots** as listed in Step 6, each captioned with what it demonstrates.

## 7. Report specification (produce `.docx` AND `.pdf`)

**File names:** `docs/VeriDoc_Project_Report.docx` and `docs/VeriDoc_Project_Report.pdf`.

**Layout (mirror the sample report):** A4, clean professional style, 1-inch margins, body about 11 pt, numbered headings ("1. Problem Statement"). Running header `VeriDoc | Project Report` and footer `Page N`. Length about 14–20 pages. Do not include the sample's yellow "STUDENT TIP" boxes, because those are instructions. Use the same visual language as the figures (section 6) for callouts and tables.

**Cover page fields:** the title **VeriDoc: a PDF question-answering system that verifies its own answers**, then `NAME`, `ROLL NUMBER`, `BATCH: GENAI 2026`, `SUBMITTED TO`, `DATE`. Ask me for all of these. Do not invent them.

**The 14 sections. Follow this structure and its rules:**
1. **Problem Statement:** who has the problem (people who rely on PDF chatbots for handbooks, policies, contracts), what exactly goes wrong (confident hallucination, no way to tell grounded from invented), and at least one number you can test later. Include the domain, users and success criteria.
2. **Objectives and Scope:** 3 to 6 *measurable* objectives (for example, "abstain on at least X% of unanswerable questions", "answer at least Y% of answerable questions correctly"). Set the targets honestly, then report against them. Include explicit in-scope and out-of-scope lists (out of scope: scanned/OCR PDFs, multi-turn memory, truth verification beyond the document).
3. **Solution and Features:** what the user can do (upload, ask, see a badge, see per-claim ✅/❌, see highlighted evidence, toggle baseline), not a list of technologies.
4. **Tech Stack:** a table with columns *Technology | Purpose in this project | Why it was chosen*: PyMuPDF, sentence-transformers MiniLM, ChromaDB, Groq Llama-3.3-70B, DeBERTa NLI cross-encoder, Streamlit, pytest, Playwright (screenshots), Streamlit Cloud/HF Spaces. Every row needs a real reason (free, local, no server, fast, and so on), not "popular".
5. **Knowledge Base and Data:** the fictional Northwind handbook (5 pages, all invented facts, so anything outside it must come from model imagination), how it was generated, chunking parameters, how many chunks, top-k, why chunks do not cross pages. Also describe the question set: 12 answerable, 10 unanswerable.
6. **System Architecture:** Figure 6.1 and 6.2 plus a walk-through of one request end to end.
7. **Implementation Highlights:** 2 or 3 key pieces with *short* excerpts (under 15 lines each): the quote-verification safeguard, the fail-closed decision logic, the similarity gate. Do not paste hundreds of lines. Include Figure 7.1.
8. **Testing and Results:** a table of test cases with *Input | Expected | Actual | Status*, covering both passes **and failures**. Include the unit-test summary (21 tests plus whatever you added) and the live demo script results, and mention the bug the tests caught.
9. **Evaluation and Metrics:** the eval table and Figure 9.1, and the method (question set, how correctness was decided, single LLM, temperature 0). Discuss baseline vs LLM verifier vs NLI verifier as a mini ablation. Explain the cost/latency differences (extra API call vs local model). State clearly any tuning done and its limits, including the small sample size.
10. **Screenshots:** captioned real screenshots (Step 6).
11. **Challenges and Learnings:** real problems actually hit (for example the `NOT_FOUND` underscore bug, PDFs that emit one block per line, bare "1." splitting sentences, sandbox/network limits, rate limits, memory on hosting) and exactly how each was solved. Add anything you hit during the live runs.
12. **Future Improvements:** 2 to 5 realistic next steps (NLI fine-tuning on domain data, OCR support, multi-turn memory, cross-page chunking, claim-level confidence calibration, Supabase for saved sessions).
13. **Conclusion:** what was built, results against the objectives from section 2, what was learned. Do not repeat the introduction.
14. **References and Links:** GitHub repo URL, hosted app URL, Drive folder URL, libraries and papers actually used (MiniLM, DeBERTa NLI, ChromaDB, Groq docs, RAG paper). No private or missing links.

**Common mistakes to avoid (from the sample's guidance):** vague goals, technologies listed with no reason, diagrams with no explanation, pasting whole files of code, showing only passing tests, numbers with no method behind them, blurry or unlabelled screenshots, claiming there were no challenges, an unrealistic wish-list, a private or missing repo link.

**Quality gate before delivering:** the PDF and DOCX have identical content; every figure is referenced in the text and captioned; fonts and tables render properly in the PDF; I have inspected every page as an image; every number in the report matches `eval/results/results.json` and the test output; and no key or personal detail is exposed.

## 8. Submission package (finish with this)

1. **Public GitHub repo:** the form needs a repository link that reviewers can open. This repo (`AnuruddhaPaul/veridoc`) is currently **private**. When everything is finished, run a secret scan first (`git log -p | grep -i gsk_`, and check no `.env` was ever committed), then ask me to switch it to public in Settings → Danger Zone → Change visibility (or confirm with the instructor that private-with-access is acceptable). Never make it public while any key is in its history. The final README must include: what it is, the architecture diagram, setup, demo script, the real eval table, the hosted link, and limitations.
2. **Google Drive folder** (I create it; give me the exact list): project source zip, `VeriDoc_Project_Report.docx`, `VeriDoc_Project_Report.pdf`, `docs/figures/` (screenshots and diagrams), `eval/results/`, sample PDF, and a `LINKS.txt` with the GitHub and hosted URLs. Sharing must be **Anyone with the link → Viewer**. Test by opening it in a private window.
3. **Hosted link:** verified in an incognito window (section 5).
4. **Final checklist, printed for me to tick before I submit:** deadline not passed; college email logged in; the GitHub link opens while logged out; the hosted app answers a grounded question and refuses an unanswerable one; the Drive link opens while logged out and shows Viewer access; the report PDF and DOCX open and match; there is no key in the repo, report or screenshots; all form fields prepared in a text file (`docs/FORM_ANSWERS.md`) so I can copy them in. Remind me that the form cannot be edited after submission.

## 9. How to work with me

- Keep messages short. After each step give: what you did, what passed, what failed, and what you need from me.
- If a step is blocked (missing key, no internet, Streamlit account), say exactly what I must do, then move to the next unblocked step.
- Prefer real verification over reassurance. Run the code, look at the outputs, and open the images and PDF pages you produce.
- If something I asked for conflicts with the course guidelines or the deadline, tell me plainly and propose the safest option.

Begin with sections 0 and 1. Check the date, read the two guideline documents, fix the `.env` exposure, and then start Step 1.
