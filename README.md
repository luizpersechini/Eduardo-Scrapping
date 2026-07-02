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
- **Three data routes**:
  - **New scrape** — the classic per-CNPJ ANBIMA quota scrape
    (date × CNPJ pivot output).
  - **FIDC** — scrapes all subclasses of each FIDC CNPJ with the full
    6-column periodic table (PL, cota, aplicações, resgates, cotistas),
    long/tidy output, optional per-CNPJ subclass filter.
  - **CVM** — no scraping at all: downloads the official
    `inf_diario_fi` monthly CSV from
    [dados.cvm.gov.br](https://dados.cvm.gov.br) and filters it to the
    uploaded CNPJs. Immune to anti-bot blocks; cached per month in
    `cvm_cache/`.
- **Live progress** during a run: SVG ring, six KPI tiles, thin emerald
  progress bar, shimmering "Fetching…" row in the activity feed,
  per-CNPJ success/failed history.
- **Stop button + incremental save** — a `_partial.xlsx` is written to
  `results/` after every CNPJ, so even a killed process keeps everything
  scraped so far.
- **Circuit breaker** — if the driver dies permanently mid-run, the run
  aborts cleanly with partial results instead of grinding through the
  recovery loop for every remaining CNPJ.
- **History route** — lists every saved Excel in `results/`
  (regular, FIDC and CVM runs, partial runs tagged) for re-download,
  plus per-run session logs.
- **Excel output formatting** — dates are real `dd/mm/yyyy` Excel date
  cells (no "Text to Columns" needed) and quota values are plain
  numbers (no `R$ ` prefix). See `DataProcessor.write_excel`.
- **Optional upstream proxy** (Settings → proxy field) for IP rotation
  on large batches.
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

### Local — Windows (end-user package)

Three batch files, made for a non-technical user:

- [`1-INSTALAR.bat`](./1-INSTALAR.bat) — one-time install (finds Python
  - Chrome, creates `venv\`, installs deps).
- [`2-ABRIR-COTA.bat`](./2-ABRIR-COTA.bat) — starts the app (no login
  locally via `COTA_NO_LOGIN=1`).
- [`3-ATUALIZAR.bat`](./3-ATUALIZAR.bat) — one-click update: downloads
  the latest `main` zip from GitHub and copies the code over, never
  touching `venv\`, `instance/`, `results/` or credentials.

Full instructions in [`WINDOWS_SETUP.md`](./WINDOWS_SETUP.md).
A GitHub Actions **Windows smoke test**
([`.github/workflows/windows-smoke.yml`](./.github/workflows/windows-smoke.yml))
installs and boots the app on `windows-latest` on every push to `main`.

### CLI (no Streamlit)

```bash
python main.py            # serial ANBIMA scrape
python main_parallel.py   # parallel scrape (higher detection risk)
python main_cvm.py input.xlsx             # CVM open-data quotas (no browser)
python main_cvm.py input.xlsx --month 202605
```

---

## Project layout

```
streamlit_app.py        Streamlit UI entry point (routes: scrape/FIDC/CVM/history/settings)
cota_theme.py           Cota design system (CSS + HTML helpers)
stealth_scraper.py      Primary scraper (undetected-chromedriver + fallbacks, FIDC methods)
anbima_scraper.py       Standard-Selenium scraper (used when stealth is off)
data_processor.py       Cleans scraper output; write_excel (dd/mm/yyyy dates, numeric quotas)
cvm_downloader.py       Downloads + caches CVM inf_diario_fi monthly zips
cvm_processor.py        Filters the CVM CSV to the requested CNPJs
config.py               URLs, selectors, timeouts, CVM settings
main.py                 CLI orchestrator (serial ANBIMA scrape)
main_parallel.py        CLI orchestrator (N workers)
main_cvm.py             CLI for the CVM open-data path (no browser)
monitor_progress.py     Tail a running scrape
monitor_and_verify.py   Verify scraped data integrity
verify_results.py       Standalone post-run verification
1-INSTALAR.bat          Windows one-time installer (PT, end-user)
2-ABRIR-COTA.bat        Windows launcher (PT, end-user)
3-ATUALIZAR.bat         Windows one-click updater (PT, end-user)
run_windows.bat         Windows local launcher (developer)
tests/                  smoke_test, cvm_ingest_test, cvm_route_test (run in CI)
.github/workflows/      windows-smoke.yml — install + boot on windows-latest
.streamlit/             Streamlit config + Cota palette
packages.txt            Apt deps for Streamlit Cloud (chromium, chromium-driver)
requirements.txt        Python deps (requirements.lock = uv hash-pinned)
results/                Saved run Excels (gitignored)
cvm_cache/              Cached CVM monthly zips/CSVs (gitignored)
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
