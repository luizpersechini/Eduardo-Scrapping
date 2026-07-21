# Architecture

How the pieces of Cota / the ANBIMA scraper fit together.

---

## Top-level diagram

```
                      Streamlit UI (streamlit_app.py)
                                  │
       ┌──────────────────────────┼──────────────────────────┐
       │                          │                          │
   cota_theme.py            session state             route dispatch
   (CSS + HTML helpers)     (auth, phase, settings,    (scrape/fidc/cvm/
                            cnpjs, results,             history/settings)
                            activity_events)
       │                          │
       └──────────────────────────┴──────────────────────────┐
                                                             │
                   stealth_scraper.StealthANBIMAScraper       │
                                  │                          │
            try undetected-chromedriver                       │
            └→ retry once after 2 s                           │
                 └→ plain Selenium + selenium-stealth ────────┤
                                  │                          │
                          scrape_fund_data(cnpj) ──→ result   │
                                  │                          │
                          DataProcessor (data_processor.py)   │
                                  │                          │
                              pandas DataFrame                │
                                  │                          │
                              Excel via openpyxl ─────────────┘
```

---

## Modules

### `streamlit_app.py`

Streamlit UI entry point. Owns:

- **Auth** (`USERNAME` / SHA-256 `PASSWORD_HASH`).
- **Session state** keys: `phase`, `route`, `settings`, `cnpjs`,
  `scraping_in_progress`, `stop_scraping`, `progress`, `success_count`,
  `failed_count`, `status_messages`, `activity_events`, `start_time`,
  `results`, `uploaded_filename`, `_last_diag`, etc.
- **Routes**: `scrape` (default), `fidc`, `cvm`, `history`, `settings`.
  The topbar HTML is rendered by `cota_theme.topbar`; the actual route
  switch is the small button row right under it.
- **Phases**: `upload → review → scrape → done` in the scrape route;
  the `fidc` and `cvm` routes mirror the same phase pattern with their
  own session-state keys (`fidc_*`, `cvm_*`).
  Each phase is a self-contained block; transitions set
  `st.session_state.phase` then `st.rerun()`.
- **Resilience during a run**:
  - _Incremental save_ — after every CNPJ the collected results are
    written to `results/<kind>_results_<ts>_partial.xlsx`, so a killed
    process (or Stop) keeps everything scraped so far. On success the
    partial is replaced by the final file.
  - _Circuit breaker_ — if the driver is permanently dead (recovery
    exhausted), the run aborts immediately with the partial results
    instead of burning the recovery loop on every remaining CNPJ.

The scrape phase pre-creates four `st.empty()` slots
(`hero_slot`, `bar_slot`, `activity_slot`, `status_slot`) and rewrites
them via `_render_live(...)` after every CNPJ. This is what gives the
appearance of a live-updating UI without any JS — Streamlit's slot
diffing patches each region in place.

### `cota_theme.py`

The Cota design system. Two halves:

1. `COTA_CSS` — one big CSS string injected once via `inject_css()`.
   Styles native Streamlit widgets (buttons, inputs, file uploader,
   bordered containers) to the Cota palette and adds custom classes for
   the topbar, stepper, KPI tiles, activity feed, success circle,
   result tables, history rows, env rows.
2. HTML helpers that build self-contained blocks the app composes via
   `st.markdown(..., unsafe_allow_html=True)`:
   `brand_mark`, `topbar`, `page_head`, `footer`, `login_bg`,
   `stepper`, `cnpj_table`, `run_summary`, `setting_text`,
   `progress_hero`, `progress_bar_html`, `activity_panel`,
   `success_circle`, `kpi_row`, `result_table`, `history_row`,
   `env_row`.

All helpers emit single-line HTML to avoid Streamlit's CommonMark
parser treating indented lines as code blocks.

### `stealth_scraper.py`

Primary scraper. The interesting bit is `setup_driver()`, which has a
**retry + fallback chain** for cloud reliability:

```
attempt 1: undetected-chromedriver
attempt 2: undetected-chromedriver again (sleep 2s in between)
attempt 3: plain Selenium + selenium-stealth, system chromedriver, no patching
```

Each attempt's exception is collected; if all three fail, the last
traceback is surfaced in `last_init_error` / `last_init_traceback` and
shown verbatim in the UI.

`uc.Chrome` kwargs are **branched by host**:

- **Linux (Streamlit Cloud)** — copy the system chromedriver to a
  per-session `/tmp/chromedriver_<uuid>` (UC needs to patch it,
  `/usr/bin/chromedriver` is read-only), pass
  `version_main=chrome_version`, `use_subprocess=True`.
- **macOS / Windows** — `version_main=chrome_version` (so UC doesn't
  auto-download a chromedriver one major ahead of installed Chrome),
  `use_subprocess=False` (the subprocess launch path causes the
  headless window to die on first navigation on Mac).

On Windows, `chrome.exe --version` prints nothing, so the Chrome major
is read from the registry (`BLBeacon\version`) — without it UC guesses
the newest driver and mismatches the installed browser.

Anti-detection on top of UC:

- A small set of safe Chrome args (no
  `--disable-features=VizDisplayCompositor` — that one crashes
  Chromium 120+ in containers).
- CDP `Network.setUserAgentOverride` to a stable Chrome 120 UA string.
- `Object.defineProperty(navigator, 'webdriver', {get: () => undefined})`
  on every page load.

The recovery loop you see in logs ("attempting recovery (attempt 1/3)")
is a _separate_ mechanism that fires when the driver becomes
unresponsive _during_ a scrape (window closed, connection refused). It
calls `close()` and then `setup_driver()` again.

`close()` does a graceful `driver.quit()` and on Linux follows it with
`pkill -9 -f chromedriver|chrome|chromium` to make sure no zombie
process stays around to eat into the Streamlit Cloud RAM ceiling.

FIDC support lives in three additional methods on the same class:

- `search_fidc_subclasses(cnpj)` — like `search_fund` up to the results
  page, but collects **all** result anchors instead of clicking the
  first one (a FIDC CNPJ can map to several subclasses).
- `extract_fidc_periodic_data()` — generalised table reader that
  keyword-matches all 6 FIDC columns (competência, PL, cota,
  aplicações, resgates, cotistas).
- `scrape_fidc_data(cnpj)` — orchestrates the two above per subclass
  and returns `{CNPJ, Status, subclasses: [...]}`.

An optional **upstream proxy** (`proxy` ctor arg, Settings field in the
UI) is passed to Chrome as `--proxy-server` for IP rotation on large
batches. Use an IP-whitelisted gateway — Chrome's flag carries no
credentials.

### `anbima_scraper.py`

Plain-Selenium version of the same scraper. Used when "Stealth mode"
is toggled off in the UI. Same scrape interface (`scrape_fund_data`).

### `data_processor.py`

Takes the per-CNPJ scraper output and:

- Pivots the regular-scrape periodic data into a date × CNPJ pivot
  with a two-row header (fund name / "Valor cota").
- Flattens FIDC results into a long/tidy frame
  (`process_fidc_data`): one row per subclasse × competência date.
- Cleans values for Excel: `to_date()` turns `dd/mm/yyyy` strings into
  real datetimes, `brl_to_number()` strips `R$ ` and Brazilian
  thousand/decimal separators into plain floats.
- `write_excel(df, target)` is the **single Excel writer** used by
  every output path (regular, FIDC, CVM; UI and CLI). It forces
  `DD/MM/YYYY` display on every date cell — including the
  regular pivot's mixed-type date column, which pandas'
  `datetime_format` option alone would skip.

### `cvm_downloader.py` / `cvm_processor.py` / `main_cvm.py`

The ANBIMA-independent quota source. CVM publishes every fund's daily
quotas as a monthly CSV (`inf_diario_fi_YYYYMM.zip`) on
dados.cvm.gov.br — no scraping, no anti-bot risk.

- `cvm_downloader` — lists available months, resolves the target month
  (default: latest published — CVM appends to it daily), downloads the
  zip (write-then-rename, cached in `cvm_cache/`; current and previous
  months are re-downloaded once per day, older months cached forever),
  extracts the CSV (overwriting a stale extract).
- `cvm_processor.load_quotas(csv, cnpjs)` — reads only the needed
  columns, filters to the requested CNPJs, keeps `ID_SUBCLASSE` as a
  disambiguator, coerces dates/numbers, and returns the same tidy
  column shape as the FIDC output.
- `main_cvm.py` — CLI wrapper: `python main_cvm.py input.xlsx
[--month YYYYMM]`.

The `cvm` route in the UI is the same upload → review → run → done
flow, minus the browser.

### `config.py`

Page URLs, CSS/XPath selectors, timeouts, and the `CVM_*` settings
(base URL, filename pattern, cache dir, column map). Change here when
ANBIMA's DOM or CVM's schema shifts.

### `main.py` / `main_parallel.py`

CLI orchestrators that don't need Streamlit. `main.py` serial, the
parallel one runs N worker processes. Useful for headless automated
runs or when you want to scrape from a server with no UI.

---

## Data flow for one scrape (Streamlit path)

1. User uploads `.xlsx` with a `CNPJ` column on the **Upload** phase.
2. `pandas.read_excel` parses; CNPJs land in `st.session_state.cnpjs`.
   Phase advances to **Review**.
3. User adjusts `settings` (stealth / headless / workers / delay) and
   clicks Start. `kill_orphan_chrome()` runs first.
4. Phase advances to **Scrape**. The scrape phase block instantiates
   `StealthANBIMAScraper(headless=...)` and calls `setup_driver()`.
5. For each CNPJ: render shimmering "Fetching…" row → call
   `scrape_fund_data(cnpj)` → append `{cnpj, name, status, points, ms}`
   to `activity_events` → re-render the live regions.
6. After the loop (or after Stop is clicked) the `finally:` block
   closes the driver, runs `DataProcessor` over collected results,
   stashes the DataFrame in `st.session_state.results`, advances phase
   to **Done**, and reruns.
7. **Done** phase shows the summary card + KPI row + result table
   sourced from `activity_events`; the Download Excel button serves
   the DataFrame from session state.

---

## Streamlit Cloud-specific behaviour

The cloud environment (Debian 11, ~1 GB RAM, 12-hour idle hibernation)
needs special care:

- `packages.txt` installs `chromium` and `chromium-driver` via apt.
- `kill_orphan_chrome()` runs once on session init, before every
  Start, and via the Settings "Kill orphan Chrome" button. Lingering
  Chrome is the #1 cause of "Argh. This app has gone over its resource
  limits".
- The chromedriver binary is read-only at `/usr/bin/chromedriver`, so
  `setup_driver()` copies it to `/tmp/chromedriver_<uuid>` per session
  before passing the path to UC (UC patches the binary at startup).
- `--disable-dev-shm-usage` is essential — `/dev/shm` is too small in
  the container for Chrome's default shared-memory IPC.
- 12-hour hibernation is policy. The fixes above prevent the
  _unscheduled_ container kills caused by RAM exhaustion; the daily
  hibernation is unavoidable on the free tier.

See [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md) for the failure modes
this design defends against.
