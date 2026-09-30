# Final checklist (tick every box before pressing Submit; the form cannot be edited afterwards)

- [ ] Today is on or before 30 September 2026 (late submissions are not considered)
- [ ] Logged into the form with the **college email** (personal emails are rejected)
- [ ] Old Groq keys revoked at console.groq.com, and `.env` untracked in the old `AGNTIC_AI` repo (`git rm --cached .env digital_safety_agent/.env`)
- [ ] The Groq key in this project's `.env` is a fresh one, and no key appears in the repo, report or screenshots (`git log -p | grep -i gsk_` prints nothing)
- [ ] GitHub repo is **Public**, and the link opens in a private/incognito window
- [ ] Hosted app opens in an incognito window; a grounded question is answered and an unanswerable one is refused
- [ ] Drive folder link opens in an incognito window and shows Viewer access
- [ ] `docs/VeriDoc_Project_Report.pdf` and `.docx` open; the Live app and Drive links on the cover and in Section 14 are filled in (run `python docs/build_report.py` after editing `docs/links.json`)
- [ ] The DOCX and PDF match (both come from the same build)
- [ ] Every field in `docs/FORM_ANSWERS.md` copied into the form and double-checked
- [ ] Open the hosted app a few minutes before submitting (free apps sleep; the first load is slow)
