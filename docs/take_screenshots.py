"""Drives the REAL running app with Playwright and saves screenshots to docs/figures/.

Usage:  python docs/take_screenshots.py [local | <public-url>]
Needs GROQ_API_KEY in .env (local mode). The key is loaded by the app itself and is never displayed:
the sidebar key box only appears when no key is configured.
"""

import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "figures"
PORT = 8599
W, H = 1400, 1000

GROUNDED_Q = "How many days of annual leave do full-time employees get?"
GROUNDED_Q2 = "What is the minimum password length?"
ABSENT_Q = "What is the bereavement leave policy?"
ABSENT_Q2 = "How many stock options do new hires receive?"
OFFTOPIC_Q = "What is the capital of France?"


def wait_for_server(url, timeout=90):
    end = time.time() + timeout
    while time.time() < end:
        try:
            urllib.request.urlopen(url + "/_stcore/health", timeout=2)
            return
        except Exception:
            time.sleep(1)
    raise RuntimeError("Streamlit did not start")


def settle(page, timeout=120_000):
    """Wait until Streamlit finishes running (no 'Running' status widget, no spinner)."""
    page.wait_for_timeout(800)
    page.wait_for_function(
        "() => !document.querySelector('[data-testid=\"stStatusWidget\"]') && "
        "!document.querySelector('[data-testid=\"stSpinner\"]')",
        timeout=timeout,
    )
    page.wait_for_timeout(600)


def clear(page):
    page.get_by_role("button", name="Clear conversation").click()
    settle(page)


def ask(page, question):
    box = page.locator('[data-testid="stChatInputTextArea"]')
    box.fill(question)
    box.press("Enter")
    page.wait_for_selector('[data-testid="stChatMessage"] >> nth=1', timeout=60_000)
    settle(page)


def expand_sources(page):
    for exp in page.get_by_text("Retrieved sources").all():
        exp.click()
    page.wait_for_timeout(500)


def shot(page, name):
    page.evaluate("window.scrollTo(0, 0)")
    page.screenshot(path=str(OUT / f"{name}.png"))
    print("saved", name)


def set_mode(page, label):
    page.locator('[data-testid="stSidebar"]').get_by_text(label, exact=True).click()
    settle(page)


def run_hosted(page):
    """Community Cloud wraps the app in an iframe and may show a 'wake up' button first."""
    wake = page.get_by_role("button", name="Yes, get this app back up!")
    try:
        wake.wait_for(timeout=8_000)
        wake.click()
        print("app was asleep; woke it")
    except Exception:
        pass
    page.wait_for_selector('iframe[title="streamlitApp"]', timeout=240_000)
    ui = page.frame_locator('iframe[title="streamlitApp"]').first
    frame = page.query_selector('iframe[title="streamlitApp"]').content_frame()
    frame.wait_for_selector('button:has-text("Load sample handbook")', timeout=240_000)
    frame.get_by_role("button", name="Load sample handbook").click()
    settle(frame)
    ask(frame, GROUNDED_Q)
    txt = frame.locator('body').inner_text()
    print("grounded question ->", "Grounded" in txt, "| '25 days' in answer:", "25 days" in txt)
    page.screenshot(path=str(OUT / "hosted_grounded.png"))
    clear(frame)
    ask(frame, ABSENT_Q)
    txt = frame.locator('body').inner_text()
    print("unanswerable question -> 'Not found' shown:", "Not found" in txt)
    page.screenshot(path=str(OUT / "hosted_not_found.png"))
    print("api key visible in page text:", "gsk_" in page.content() or "gsk_" in txt)


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "local"
    proc = None
    if target == "local":
        url = f"http://localhost:{PORT}"
        proc = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", str(PORT),
             "--server.headless", "true", "--browser.gatherUsageStats", "false"],
            cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        wait_for_server(url)
        prefix = "shot"
    else:
        url, prefix = target, "hosted"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": W, "height": H})
            page.goto(url, wait_until="domcontentloaded", timeout=120_000)
            if prefix == "hosted":
                run_hosted(page)
                browser.close()
                return
            page.wait_for_load_state("networkidle")
            page.get_by_role("button", name="Load sample handbook").click()
            settle(page)

            if len(sys.argv) > 2 and sys.argv[2] == "nli":  # retake only the NLI shot, in a taller window
                page.set_viewport_size({"width": W, "height": 1300})
                set_mode(page, "NLI verifier")
                ask(page, GROUNDED_Q2)
                expand_sources(page)
                shot(page, "shot_h_nli_grounded")
                browser.close()
                return

            shot(page, "shot_a_home")

            ask(page, GROUNDED_Q)
            expand_sources(page)
            shot(page, "shot_b_grounded")

            clear(page)
            ask(page, ABSENT_Q)
            shot(page, "shot_d_not_found")

            clear(page)
            ask(page, OFFTOPIC_Q)
            shot(page, "shot_e_offtopic")

            # NLI verifier on a grounded question (retaken separately with a taller window: `... local nli`)
            clear(page)
            set_mode(page, "NLI verifier")
            ask(page, GROUNDED_Q2)
            expand_sources(page)
            shot(page, "shot_h_nli_grounded")

            # baseline: grounding off + typical chatbot prompt
            clear(page)
            set_mode(page, "Off (baseline RAG)")
            page.get_by_text("Typical chatbot prompt (comparison)").click()
            settle(page)
            ask(page, ABSENT_Q)
            shot(page, "shot_f_baseline_bereavement")
            clear(page)
            ask(page, ABSENT_Q2)
            shot(page, "shot_f_baseline_stock")

            # same typical prompt WITH the LLM verifier (partial/ungrounded may occur naturally)
            clear(page)
            set_mode(page, "LLM verifier")
            ask(page, ABSENT_Q)
            expand_sources(page)
            shot(page, "shot_c_naive_plus_verifier")
            browser.close()
    finally:
        if proc:
            proc.terminate()


if __name__ == "__main__":
    main()
