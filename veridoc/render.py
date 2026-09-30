"""Pure helpers for presenting a Result (kept out of app.py so they can be unit-tested)."""

from __future__ import annotations

import html
import re

from .pipeline import (
    GROUNDED, NOT_FOUND, PARTIAL, UNCHECKED, UNGROUNDED, UNVERIFIED, Result,
)


def badge(result: Result) -> tuple[str, str]:
    """(streamlit_level, label) for the answer's grounding indicator."""
    report = result.report
    counts = f"{report.supported_count}/{len(report.verdicts)} claims supported" if report else ""
    return {
        GROUNDED: ("success", f"Grounded - {counts}"),
        PARTIAL: ("warning", f"Partially grounded - {counts}. Check the flagged claims."),
        UNGROUNDED: ("error", "Not grounded - no claim could be verified against the document."),
        NOT_FOUND: ("info", "Not found in the document."),
        UNVERIFIED: ("warning", "Could not run the grounding check - treat this answer as unverified."),
        UNCHECKED: ("info", "Grounding check is off (baseline mode) - this answer is unverified."),
    }[result.status]


def escape_dollars(text: str) -> str:
    """Stop Streamlit's markdown from treating '$60 ... $70' as LaTeX."""
    return text.replace("$", "\\$")


def highlight_html(text: str, quotes: list[str]) -> str:
    """HTML-escape `text` and wrap each verifier quote found in it with <mark>."""
    spans: list[tuple[int, int]] = []
    for quote in quotes:
        words = re.findall(r"[A-Za-z0-9]+", quote)
        if not words:
            continue
        match = re.search(r"\W+".join(re.escape(w) for w in words), text, flags=re.IGNORECASE)
        if match:
            spans.append(match.span())
    spans.sort()
    out, pos = [], 0
    for start, end in spans:
        if start < pos:  # overlapping quotes: keep the first
            continue
        out.append(html.escape(text[pos:start]))
        out.append(f"<mark>{html.escape(text[start:end])}</mark>")
        pos = end
    out.append(html.escape(text[pos:]))
    return "".join(out)
