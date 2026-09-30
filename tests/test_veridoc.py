"""Offline tests: a scripted LLM and the hashing embedder stand in for Groq and MiniLM."""

import json
from pathlib import Path

import pytest

from veridoc.embeddings import HashingEmbedder
from veridoc.grounding import (
    LLMVerifier,
    NLIVerifier,
    VerificationError,
    parse_json_object,
    quote_in_text,
    split_claims,
    strip_citations,
)
from veridoc.ingest import approx_tokens, chunk_pages, chunk_text, extract_pages
from veridoc.pipeline import (
    GROUNDED, NOT_FOUND, PARTIAL, UNCHECKED, UNGROUNDED, UNVERIFIED, VeriDoc,
)
from veridoc.rag import is_not_found

SAMPLE = Path(__file__).resolve().parent.parent / "sample_docs" / "northwind_handbook.pdf"
LEAVE = "All full-time employees receive 25 days of paid annual leave per calendar year."


class ScriptedLLM:
    """Returns canned generator / verifier outputs and records the calls made."""

    def __init__(self, answer="", verdict=None):
        self.answer, self.verdict, self.calls = answer, verdict, []

    def complete(self, system, user, *, json_mode=False, max_tokens=1024):
        self.calls.append("verify" if json_mode else "generate")
        if json_mode:
            return self.verdict if isinstance(self.verdict, str) else json.dumps(self.verdict)
        return self.answer


def make_app(llm, verifier="llm", **kw):
    v = LLMVerifier(llm) if verifier == "llm" else verifier
    app = VeriDoc(llm, v, HashingEmbedder(), min_similarity=kw.pop("min_similarity", 0.05), **kw)
    app.ingest_pdf(SAMPLE.read_bytes(), "handbook.pdf")
    return app


def claim(text, supported, source=None, quote=""):
    return {"claim": text, "supported": supported, "source": source, "quote": quote, "reason": ""}


# ---------------------------------------------------------------- ingestion
def test_extract_pages_and_page_numbers():
    pages = extract_pages(SAMPLE.read_bytes())
    assert [p for p, _ in pages] == [1, 2, 3, 4, 5]
    assert "25 days of paid annual leave" in pages[0][1]
    chunks = chunk_pages(pages, "h")
    assert {c.page for c in chunks} == {1, 2, 3, 4, 5}
    assert len({c.id for c in chunks}) == len(chunks)


def test_chunking_respects_size_and_overlaps():
    text = " ".join(f"Sentence number {i} talks about topic {i}." for i in range(200))
    chunks = chunk_text(text, max_tokens=100, overlap_tokens=25)
    assert len(chunks) > 3
    assert all(approx_tokens(c) <= 100 + 15 for c in chunks)
    # the tail of each chunk is repeated at the start of the next
    assert chunks[0].split(". ")[-1].split()[0] in chunks[1]
    # nothing is lost
    for i in range(200):
        assert f"Sentence number {i} " in " ".join(chunks)


def test_chunking_splits_a_giant_unpunctuated_run():
    chunks = chunk_text("word " * 2000, max_tokens=100, overlap_tokens=10)
    assert len(chunks) > 10 and all(approx_tokens(c) <= 115 for c in chunks)


# ---------------------------------------------------------------- grounding helpers
def test_helpers():
    assert strip_citations("Employees get 25 days [1]. Also 5 carry [2, 3].") == "Employees get 25 days. Also 5 carry."
    assert split_claims("Yes. It is 25 days [1]. Carry over is 5 days [2].") == ["It is 25 days.", "Carry over is 5 days."]
    assert quote_in_text("25 days of paid annual leave", LEAVE)
    assert quote_in_text("All full-time ... per calendar year", LEAVE)
    assert not quote_in_text("30 days of paid annual leave", LEAVE)
    assert not quote_in_text("", LEAVE)
    assert is_not_found("NOT_FOUND") and is_not_found(" not found. ") and not is_not_found("Not found in 2019")


def test_parse_json_handles_fences_and_garbage():
    assert parse_json_object('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json_object('Sure! {"a": 1} hope that helps') == {"a": 1}
    with pytest.raises(VerificationError):
        parse_json_object("no json here")
    with pytest.raises(VerificationError):
        parse_json_object("{broken")


# ---------------------------------------------------------------- pipeline decisions
def test_grounded_answer_passes_through():
    llm = ScriptedLLM("Full-time employees get 25 days of annual leave [1].",
                      {"claims": [claim("Employees get 25 days.", True, 1, "25 days of paid annual leave")]})
    app = make_app(llm)
    # make sure the leave chunk is what rank 1 refers to
    r = app.ask("How many days of annual leave do employees get?")
    assert r.sources[0].chunk.page == 1
    assert r.status == GROUNDED and r.answer == llm.answer
    assert r.report.verdicts[0].source_rank == 1 and r.report.ratio == 1.0
    assert llm.calls == ["generate", "verify"]


def test_partial_when_some_claims_unsupported():
    llm = ScriptedLLM("Employees get 25 days of leave [1] and 40 days of sick leave [1].",
                      {"claims": [claim("25 days of leave", True, 1, "25 days of paid annual leave"),
                                  claim("40 days of sick leave", False)]})
    r = make_app(llm).ask("How many days of annual leave and sick leave do employees get?")
    assert r.status == PARTIAL and r.report.supported_count == 1 and len(r.report.verdicts) == 2
    assert r.answer == llm.answer  # answer is shown, but claim-level flags mark the weak part


def test_hallucination_is_blocked():
    llm = ScriptedLLM("Employees receive 40 days of leave [1].", {"claims": [claim("40 days of leave", False)]})
    r = make_app(llm).ask("How many days of annual leave do employees get?")
    assert r.status == UNGROUNDED and r.abstained
    assert "40 days" not in r.answer and r.draft == llm.answer  # draft kept for inspection only


def test_verifier_cannot_assert_support_without_a_real_quote():
    """Verifier says 'supported' but the quote is invented -> downgraded to unsupported."""
    llm = ScriptedLLM("Employees get 40 days [1].",
                      {"claims": [claim("Employees get 40 days.", True, 1, "employees get forty days of leave")]})
    r = make_app(llm).ask("How many days of annual leave do employees get?")
    assert r.status == UNGROUNDED
    assert "quote not found" in r.report.verdicts[0].reason


def test_wrong_source_number_is_not_support():
    llm = ScriptedLLM("Employees get 25 days [1].",
                      {"claims": [claim("Employees get 25 days.", True, 99, "25 days of paid annual leave")]})
    assert make_app(llm).ask("How many days of annual leave do employees get?").status == UNGROUNDED


def test_low_similarity_abstains_without_calling_llm():
    llm = ScriptedLLM("should never be used")
    app = make_app(llm, min_similarity=0.99)
    r = app.ask("What is the capital of France?")
    assert r.status == NOT_FOUND and r.answer == "Not found in the document." and llm.calls == []


def test_model_not_found_is_respected():
    llm = ScriptedLLM("NOT_FOUND")
    r = make_app(llm).ask("What is the bereavement leave policy for leave?")
    assert r.status == NOT_FOUND and llm.calls == ["generate"]


@pytest.mark.parametrize("bad", ["not json", {"claims": []}, {"nothing": 1}])
def test_verifier_failure_fails_closed(bad):
    llm = ScriptedLLM("Employees get 25 days of leave [1].", bad)
    r = make_app(llm).ask("How many days of annual leave do employees get?")
    assert r.status == UNVERIFIED and r.report is None  # shown with a warning, never labelled grounded


def test_baseline_mode_skips_verification():
    llm = ScriptedLLM("Employees get 25 days of leave [1].")
    r = make_app(llm, verifier=None).ask("How many days of annual leave do employees get?")
    assert r.status == UNCHECKED and llm.calls == ["generate"]


# ---------------------------------------------------------------- NLI verifier
def test_nli_verifier_with_fake_predictor():
    def predict(pairs):  # entails only when the claim's number appears in the premise
        return [0.95 if any(w.isdigit() and w in premise for w in hyp.split()) else 0.05 for premise, hyp in pairs]

    llm = ScriptedLLM("Employees get 25 days of leave [1]. They also get 99 days of sick leave [1].")
    app = make_app(llm, verifier=NLIVerifier(predict=predict))
    r = app.ask("How many days of annual leave and sick leave do employees get?")
    assert r.report.method == "nli"
    assert [v.supported for v in r.report.verdicts] == [True, False]
    assert r.report.verdicts[0].score == 0.95 and "25 days" in r.report.verdicts[0].quote
    assert r.status == PARTIAL


def test_nli_no_claims_raises():
    with pytest.raises(VerificationError):
        NLIVerifier(predict=lambda p: [0.0] * len(p)).verify("Ok.", [])


def test_nli_scores_single_sentence_premises():
    """Live finding: the NLI model entails a claim from one sentence but not from a 2-sentence window."""
    def predict(pairs):  # entails only when the premise holds the leave sentence WITHOUT its neighbour
        return [0.95 if "25 days" in premise and "Unused" not in premise else 0.02 for premise, hyp in pairs]

    llm = ScriptedLLM("Employees get 25 days of leave [1].")
    app = make_app(llm, verifier=NLIVerifier(predict=predict, window=3))
    r = app.ask("How many days of annual leave do employees get?")
    assert r.status == GROUNDED
