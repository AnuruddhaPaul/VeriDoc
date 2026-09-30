"""VeriDoc - chat with PDFs and see whether each answer is actually backed by the document."""

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from veridoc import VeriDoc
from veridoc.grounding import LLMVerifier, NLIVerifier
from veridoc.llm import GroqLLM, MissingAPIKey
from veridoc.render import badge, escape_dollars, highlight_html

ROOT = Path(__file__).parent
SAMPLE_PDF = ROOT / "sample_docs" / "northwind_handbook.pdf"
load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / ".env")

st.set_page_config(page_title="VeriDoc", page_icon="🛡️", layout="wide")


@st.cache_resource(show_spinner="Loading embedding model...")
def get_embedder():
    from veridoc.embeddings import SentenceTransformerEmbedder

    embedder = SentenceTransformerEmbedder()
    embedder.encode(["warm-up"])
    return embedder


@st.cache_resource(show_spinner="Loading NLI model...")
def get_nli_verifier():
    return NLIVerifier()


def secret_key() -> str:
    try:
        return st.secrets.get("GROQ_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
    except Exception:  # no secrets file
        return os.getenv("GROQ_API_KEY", "")


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.title("🛡️ VeriDoc")
    st.caption("PDF Q&A that checks its own answers.")

    api_key = secret_key() or st.text_input("Groq API key", type="password", help="Free key from console.groq.com")
    mode = st.radio(
        "Grounding check",
        ["LLM verifier", "NLI verifier", "Off (baseline RAG)"],
        help="LLM: a second model call must quote evidence for every claim. "
        "NLI: a local entailment model scores each sentence. Off: plain RAG, for comparison.",
    )
    top_k = st.slider("Chunks retrieved (top-k)", 1, 8, 4)
    min_sim = st.slider("Off-topic cutoff (min similarity)", 0.0, 0.6, 0.15, 0.01,
                        help="If even the best chunk is less similar than this, VeriDoc abstains without calling the LLM.")

    st.divider()
    uploads = st.file_uploader("Upload PDF(s)", type="pdf", accept_multiple_files=True)
    use_sample = st.button("Load sample handbook", disabled=not SAMPLE_PDF.exists())
    if st.button("Clear conversation"):
        st.session_state.messages = []

# ------------------------------------------------------------------ indexing
if use_sample:
    st.session_state.sample = True
files = [(u.name, u.getvalue()) for u in uploads]
if st.session_state.get("sample") and not files:
    files = [(SAMPLE_PDF.name, SAMPLE_PDF.read_bytes())]

if not api_key:
    st.info("Enter a Groq API key in the sidebar (or set GROQ_API_KEY) to start.")
    st.stop()

try:
    llm = GroqLLM(api_key)
except MissingAPIKey as exc:
    st.error(str(exc))
    st.stop()

signature = tuple((name, len(data)) for name, data in files)
if files and st.session_state.get("signature") != signature:
    app = VeriDoc(llm, None, get_embedder())
    with st.spinner("Reading, chunking and embedding..."):
        for name, data in files:
            app.ingest_pdf(data, name)
    st.session_state.app, st.session_state.signature, st.session_state.messages = app, signature, []

app: VeriDoc | None = st.session_state.get("app")
if app is not None and files:  # settings can change without re-indexing
    app.llm, app.top_k, app.min_similarity = llm, top_k, min_sim
    app.verifier = {
        "LLM verifier": lambda: LLMVerifier(llm),
        "NLI verifier": get_nli_verifier,
        "Off (baseline RAG)": lambda: None,
    }[mode]()
    with st.sidebar:
        st.success(" \n".join(f"{n}: {c} chunks" for n, c in app.documents.items()))

st.session_state.setdefault("messages", [])

# ------------------------------------------------------------------ rendering
def render_result(result):
    level, label = badge(result)
    getattr(st, level)(label)
    st.markdown(escape_dollars(result.answer))

    if result.report:
        st.markdown("**Claim-by-claim check** (" + result.report.method.upper() + ")")
        for v in result.report.verdicts:
            icon = "✅" if v.supported else "❌"
            detail = ""
            if v.supported:
                page = result.sources[v.source_rank - 1].chunk.page
                score = f" · entailment {v.score:.2f}" if v.score is not None else ""
                detail = f" — source [{v.source_rank}], page {page}{score}"
            elif v.reason:
                detail = f" — _{v.reason}_"
            st.markdown(escape_dollars(f"{icon} {v.claim}{detail}"))

    if result.status == "ungrounded" and result.draft:
        with st.expander("Show the unverified draft (not backed by the document)"):
            st.markdown(escape_dollars(result.draft))

    if result.sources:
        quotes = {}
        if result.report:
            for v in result.report.verdicts:
                if v.supported and v.source_rank:
                    quotes.setdefault(v.source_rank, []).append(v.quote)
        with st.expander(f"Retrieved sources ({len(result.sources)})"):
            for rank, r in enumerate(result.sources, start=1):
                st.markdown(f"**[{rank}] {r.chunk.source} · page {r.chunk.page}** · similarity {r.score:.2f}")
                st.markdown(
                    f"<div style='font-size:0.9em;padding:0.4em 0.7em;border-left:3px solid #999'>"
                    f"{highlight_html(r.chunk.text, quotes.get(rank, []))}</div>",
                    unsafe_allow_html=True,
                )
    if result.timings:
        st.caption(" · ".join(f"{k} {v:.2f}s" for k, v in result.timings.items()))


st.header("Ask your document")
if app is None or not files:
    st.write("Upload a PDF (or load the sample handbook) to begin. Try asking something the document "
             "does **not** cover and watch VeriDoc refuse to guess.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.write(message["content"])
        else:
            render_result(message["result"])

if question := st.chat_input("Ask a question about your document...", disabled=app is None or not files):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        with st.spinner("Retrieving, answering, verifying..."):
            try:
                result = app.ask(question)
            except Exception as exc:  # network / rate-limit errors from the LLM
                st.error(f"Request failed: {exc}")
                st.stop()
        render_result(result)
    st.session_state.messages.append({"role": "assistant", "result": result})
