"""Builds deploy/veridoc_hf_space/ and deploy/veridoc_hf_space.zip: the files a Hugging Face Space needs.

Why: Groq answered HTTP 403 ("Access denied. Please check your network settings.") to requests coming
from Streamlit Community Cloud, while the same key worked from a laptop. Spaces run on different servers.
"""

import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "deploy" / "veridoc_hf_space"

README = """---
title: VeriDoc
emoji: 🛡️
colorFrom: blue
colorTo: indigo
sdk: streamlit
app_file: app.py
pinned: false
short_description: PDF Q&A that verifies its own answers
---

# VeriDoc

A PDF question-answering chatbot that checks every claim in its answer against the document and says
"Not found in the document" instead of guessing. Source code and report:
https://github.com/AnuruddhaPaul/VeriDoc

Set the `GROQ_API_KEY` secret in the Space settings before using it.
"""

if OUT.exists():
    shutil.rmtree(OUT)
(OUT / "sample_docs").mkdir(parents=True)
shutil.copy(ROOT / "app.py", OUT / "app.py")
shutil.copy(ROOT / "requirements.txt", OUT / "requirements.txt")
shutil.copytree(ROOT / "veridoc", OUT / "veridoc", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
shutil.copy(ROOT / "sample_docs" / "northwind_handbook.pdf", OUT / "sample_docs" / "northwind_handbook.pdf")
(OUT / "README.md").write_text(README, encoding="utf-8")

zip_path = ROOT / "deploy" / "veridoc_hf_space.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(OUT.rglob("*")):
        if f.is_file():
            z.write(f, f.relative_to(OUT))
print("wrote", zip_path, [str(f.relative_to(OUT)) for f in OUT.rglob("*") if f.is_file()])
