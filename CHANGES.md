# CapCheck fixes – what changed and why

## Bugs fixed
1. **API dropped `checks_unavailable`** – `ReportResponse` had no such field, so the "could not run" list never reached the UI.
2. **Image detectors almost never fired** – ELA splicing needed a block range > 28 and the FFT test a spike ratio > 4.2; real images measured ~2. Only metadata tags could ever trigger a result.
   - ELA now re-saves at the JPEG quality read from the file's own quantization tables (exact on tests), compares blocks robustly, and is skipped for PNG/screenshots instead of guessing.
   - FFT test now removes the natural spectrum falloff and measures peaks in robust std-devs (photos ≈ 3, injected upsampling lattice ≈ 10; threshold 7).
3. **False "AI-generated" from captions** – any PNG text containing "steps"/"seed"/"prompt" scored 96. Now only real generator chunk names / generator names count; binary blobs are ignored.
4. **Video false "manipulated"** – frames sampled 1.5 s apart made ordinary motion look like flicker; temporal score is now capped below the "suspicious" level. Per-frame ELA on app-written JPEGs removed.
5. **UI claimed a skipped ELA "passed"** – now shows "Not applicable".
6. C2PA-style marker detection unchanged; Wikipedia/reference hits still never count as proof.

## Report card (new)
- Backend: `VerdictEngine.build_report_card()` → grade A–F, overall %, per-check % (fact-checkers, reference knowledge, live news, AI tests, editing test, provenance, audio/video tests), "how it was worked out", caveats. Stored in new `reports.report_card` column (auto-migrated).
- Frontend: `components/ReportCard.tsx`, shown on the results page. Old reports get a fallback card.
- PDF export includes the card.
- A check that could not judge shows **"no result"**, never an invented number. Media % is capped at 88%.

## Tests added
`tests/unit/test_report_card.py`, `tests/image/test_detector_calibration.py` (synthetic images with known ground truth).

## Rebuild the frontend
`frontend/dist` is stale – run `npm install && npm run build` (or just use the dev server via start_all.py).

## Fix: "sqlite3.OperationalError: unable to open database file" (backend exits at startup)
- Cause: the project lives in a OneDrive-synced folder; OneDrive locks/virtualises the .db and its journal file, so SQLite can't open it.
- `config.py` now test-opens the database. If the folder is OneDrive/Dropbox-synced or not writable, it uses `%LOCALAPPDATA%\CapCheck\capcheck.db` instead (existing DB is copied over once).
- `start_all.py` no longer prints "RUNNING SUCCESSFULLY" when the backend crashed (only HTTP 200 counts as up, dead process = failure).
- `run_backend.bat` now shows database init errors instead of hiding them.
- SQLite connections wait up to 30s for locks.

## New: Gemini AI check for text claims
- `backend/app/engines/news/gemini_client.py` sends the claim to Google Gemini and gets back a verdict, a 0-100 "chance it is true", a confidence value, key points and a 4-row evaluation table (Factual accuracy, Evidence strength, Context completeness, Wording). It tries Google Search grounding first and falls back to plain mode / other models automatically.
- The Gemini percentage is the overall % on the Report Card; its table rows appear as individual percentage bars. Fact-checker/news results are still shown for comparison, and the sites Gemini consulted are listed as sources.
- If Gemini is unreachable or the key is wrong, the old evidence-only pipeline runs and the card lists "Gemini AI check (reason)" under checks that could not run.
- Settings in `.env`: `GEMINI_API_KEY`, `GEMINI_MODEL` (default gemini-2.5-flash), `GEMINI_GROUNDING` (true/false).

## Fix: History page not loading
- `api/history.py`: one unreadable/damaged record is now skipped (and logged) instead of failing the whole list with HTTP 500.
- `api/reports.py`: report building tolerates empty/invalid JSON columns and missing values from older records.
- `HistoryPage.tsx`: shows the real error with a "Try again" button instead of silently showing an empty list; no longer crashes on records with missing title/summary/date.
- `App.tsx`: an error boundary shows a readable message instead of a blank white page if any screen crashes.

## Fix: History page froze the whole app (could not navigate away)
- Root cause: `HistoryPage` called `reportApi.getPdfDownloadUrl()`, which does not exist. As soon as the list contained a report, React crashed and the whole app went blank, so no link worked.
- The PDF button now downloads through the signed-in API (`getPdfBlob`), like the results page does, and is a button instead of a link nested inside a link.
- The error boundary now resets when you open another page, so navigation always works even if a page crashes.
