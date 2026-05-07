# Cota — ANBIMA Fund Data Scraper

Streamlit web app that scrapes historical fund data from
[ANBIMA's Consultas](https://data.anbima.com.br/consultas) for a list of
CNPJs and exports the result as Excel.

The UI was redesigned to a modern fintech aesthetic ("Cota") in
[`cota_theme.py`](./cota_theme.py).
The scraper itself uses
[`undetected-chromedriver`](https://github.com/ultrafunkamsterdam/undetected-chromedriver)
with a plain-Selenium fallback.

---

## Features

- **Login → Upload → Review → Scrape → Download** stepper flow.
- **Live progress** during a run: SVG ring, six KPI tiles, thin emerald
  progress bar, shimmering "Fetching…" row in the activity feed,
  per-CNPJ success/failed history.
- **Stop button** — interrupting a run still saves the partial results
  for download.
- **History route** — lists every past `session_logs/scraping_session_*.log`
  with parsed run stats and a per-run log download.
- **Settings route** — Chromium / chromedriver version detection,
  `/dev/shm` and memory diagnostics, "Re-run diagnostics" and
  "Kill orphan Chrome" buttons, workspace defaults (stealth, headless,
  polite delay).
- **WebDriver init has a retry + fallback chain**:
  undetected-chromedriver → undetected-chromedriver retry →
  plain Selenium + selenium-stealth.

---

## Run it

### Streamlit Cloud

The repo is wired for Streamlit Community Cloud (see
[`packages.txt`](./packages.txt) for `chromium` / `chromium-driver`,
[`requirements.txt`](./requirements.txt) for Python deps,
[`.streamlit/config.toml`](./.streamlit/config.toml) for the Cota theme).

Push a change to `main` → Streamlit Cloud auto-redeploys.

### Local — macOS

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Requires Google Chrome (the scraper drives a real browser). On macOS,
**uncheck Headless mode** in the Review panel — a visible Chrome window is
much less likely to trip ANBIMA's anti-bot detection.

### Local — Windows

Double-click [`run_windows.bat`](./run_windows.bat) and follow the
prompts. Full instructions in [`WINDOWS_SETUP.md`](./WINDOWS_SETUP.md).

### CLI (no Streamlit)

```bash
python main.py            # serial scrape
python main_parallel.py   # parallel scrape (higher detection risk)
```

---

## Project layout

```
streamlit_app.py        Streamlit UI entry point
cota_theme.py           Cota design system (CSS + HTML helpers)
stealth_scraper.py      Primary scraper (undetected-chromedriver + fallbacks)
anbima_scraper.py       Standard-Selenium scraper (used when stealth is off)
data_processor.py       Cleans / pivots scraper output for Excel export
config.py               URLs, selectors, timeouts
main.py                 CLI orchestrator (serial)
main_parallel.py        CLI orchestrator (N workers)
monitor_progress.py     Tail a running scrape
monitor_and_verify.py   Verify scraped data integrity
verify_results.py       Standalone post-run verification
run_windows.bat         Windows local launcher
.streamlit/             Streamlit config + Cota palette
packages.txt            Apt deps for Streamlit Cloud (chromium, chromium-driver)
requirements.txt        Python deps
docs/archive/           Historical project docs
archive/                Old logs / outputs / test scripts
```

---

## Documentation

- [`ARCHITECTURE.md`](./ARCHITECTURE.md) — how the pieces fit together.
- [`ANTI_BOT_GUIDE.md`](./ANTI_BOT_GUIDE.md) — anti-detection design
  (read this before changing `stealth_scraper.py`).
- [`DEPLOYMENT.md`](./DEPLOYMENT.md) — Streamlit Cloud + Windows.
- [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md) — known failure modes
  and how to recover.
- [`CHANGELOG.md`](./CHANGELOG.md) — versioned change log.
- [`SECURITY.md`](./SECURITY.md), [`CONTRIBUTING.md`](./CONTRIBUTING.md),
  [`LICENSE.md`](./LICENSE.md).

For the design source files (Cota prototype HTML/CSS/JS, chat
transcripts), see the original handoff bundle from
[claude.ai/design](https://claude.ai/design).

---

## Stack

Python · Streamlit · Selenium · undetected-chromedriver ·
selenium-stealth · pandas · openpyxl
