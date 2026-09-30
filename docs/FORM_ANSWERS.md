# Submission form: answers to copy in

Form: https://forms.gle/rEvS7iFV3g6EPzX5A
**Log in with your college email only. The form cannot be edited after you submit.**

## Student information
| Field | Answer |
|---|---|
| Name | Anuruddha Paul |
| Roll number | 2328072 |
| Batch | GENAI 2026 |
| Trainer / faculty | Mr Sachin |
| College email | (you: the same address you are logged in with) |

## Project information
| Field | Answer |
|---|---|
| Project title | VeriDoc: a PDF question-answering system that verifies its own answers |
| One-line description | A PDF chatbot that checks every claim in its answer against the document and says "Not found in the document" instead of guessing. |
| Longer description | VeriDoc is a retrieval-augmented chatbot for PDFs (PyMuPDF, MiniLM embeddings, ChromaDB, a Groq-hosted LLM, Streamlit). Before an answer is shown, a grounding layer splits it into claims and verifies each against the retrieved text, either with a second LLM call whose quotes are string-matched against the source, or with a local NLI model. It shows a badge, a per-claim check with page numbers and highlighted evidence, and refuses when the document has no answer. Evaluated on 22 development and 20 held-out questions. |
| Technologies | Python, Streamlit, PyMuPDF, sentence-transformers (all-MiniLM-L6-v2), ChromaDB, Groq (openai/gpt-oss-120b), DeBERTa NLI cross-encoder, pytest, Playwright |

## Links (fill the last two in once they exist)
| Field | Answer |
|---|---|
| GitHub repository (must be PUBLIC) | https://github.com/AnuruddhaPaul/VeriDoc |
| Hosted project link | https://veridoc-bgemx43smyhzo9wqhnaibd.streamlit.app |
| Google Drive folder (Anyone with the link, Viewer) | (Drive URL) |

## What goes in the Drive folder
1. `VeriDoc_source.zip` (the repo without `.venv/` and without `.env`; run `git archive --format=zip -o VeriDoc_source.zip HEAD` from the repo root; this cannot include `.env` because it is not tracked)
2. `VeriDoc_Project_Report.docx`
3. `VeriDoc_Project_Report.pdf`
4. `figures/` (from `docs/figures/`: diagrams and screenshots)
5. `eval_results/` (from `eval/results/`)
6. `northwind_handbook.pdf` (from `sample_docs/`)
7. `LINKS.txt` (GitHub and hosted URLs, one per line)

Sharing: **Share, General access, Anyone with the link, role Viewer.** Then open the link in a private window to test.
