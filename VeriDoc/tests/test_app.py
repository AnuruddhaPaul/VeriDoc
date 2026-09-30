"""Drives the real Streamlit script headlessly with the LLM and embedder faked."""

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import veridoc.embeddings
import veridoc.llm
from veridoc.embeddings import HashingEmbedder
from veridoc.render import badge, escape_dollars, highlight_html

APP = str(Path(__file__).resolve().parent.parent / "app.py")


class FakeGroq:
    def __init__(self, api_key=None, **_):
        pass

    def complete(self, system, user, *, json_mode=False, max_tokens=1024):
        if json_mode:
            return json.dumps({"claims": [
                {"claim": "Employees get 25 days of annual leave.", "supported": True, "source": 1,
                 "quote": "25 days of paid annual leave", "reason": ""},
                {"claim": "Employees get 40 sick days.", "supported": False, "source": None, "quote": "", "reason": "not in sources"},
            ]})
        return "Employees get 25 days of annual leave [1] and 40 sick days [1]."


@pytest.fixture
def at(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "fake-key")
    monkeypatch.setattr(veridoc.llm, "GroqLLM", FakeGroq)
    monkeypatch.setattr(veridoc.embeddings, "SentenceTransformerEmbedder", HashingEmbedder)
    return AppTest.from_file(APP, default_timeout=60).run()


def test_app_loads_without_exceptions(at):
    assert not at.exception
    assert any("Upload a PDF" in m.value for m in at.markdown)


def test_full_flow_with_sample_document(at):
    next(b for b in at.sidebar.button if b.label == "Load sample handbook").click().run()
    assert not at.exception
    assert any("chunks" in s.value for s in at.sidebar.success)

    at.chat_input[0].set_value("How many days of annual leave do employees get?").run()
    assert not at.exception
    assert any("Partially grounded" in w.value and "1/2" in w.value for w in at.warning)
    text = " ".join(m.value for m in at.markdown)
    assert "✅ Employees get 25 days of annual leave." in text and "❌ Employees get 40 sick days." in text


def test_render_helpers():
    assert escape_dollars("$60 or $70") == "\\$60 or \\$70"
    out = highlight_html("Meals <b>up to</b> 60 USD per day.", ["up to 60 usd"])
    assert "&lt;b&gt;" in out and "<mark>" not in out  # tags in the text are escaped, non-contiguous quote skipped
    out = highlight_html("Pay 25 days of  paid\nleave.", ["25 days of paid leave"])
    assert out == "Pay <mark>25 days of  paid\nleave</mark>."
