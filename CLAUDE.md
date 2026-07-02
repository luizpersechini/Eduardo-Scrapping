# Eduardo Scrapping — ANBIMA fund data scraper

## Stack

Python · Selenium · undetected-chromedriver · selenium-stealth · Pandas · openpyxl · Streamlit

## Run

```
streamlit run streamlit_app.py       # the app (routes: scrape/FIDC/CVM/history/settings)
python main.py                       # CLI serial ANBIMA scrape
python main_parallel.py              # parallel scraping (faster, higher risk of detection)
python main_cvm.py input.xlsx        # CVM open-data quotas (no browser, no anti-bot)
```

Windows end user: `1-INSTALAR.bat` (once) → `2-ABRIR-COTA.bat` (use) → `3-ATUALIZAR.bat` (update from main).

## Test / verify

```
python tests/smoke_test.py       # FIDC processor + subclass matcher
python tests/cvm_ingest_test.py  # CVM downloader/processor
python tests/cvm_route_test.py   # CVM Streamlit route (AppTest, no network)
python monitor_and_verify.py     # verify scraped data integrity
python monitor_progress.py       # check run progress
```

CI: `.github/workflows/windows-smoke.yml` runs all three test files + a headless app boot on windows-latest for every push to main.

## Structure

- `streamlit_app.py` — UI entry point (scrape / FIDC / CVM / history / settings routes)
- `cota_theme.py` — Cota design system (CSS + HTML helpers)
- `stealth_scraper.py` — anti-bot evasion layer (+ FIDC methods, proxy support)
- `anbima_scraper.py` — plain-Selenium scraper (stealth off)
- `data_processor.py` — clean/transform scraped data; `write_excel` = the single Excel writer (dd/mm/yyyy dates, numeric quotas)
- `cvm_downloader.py` / `cvm_processor.py` — CVM open-data ingest (cached in `cvm_cache/`)
- `main.py` / `main_parallel.py` / `main_cvm.py` — CLI entry points
- `config.py` — site URLs, selectors, timeouts, CVM\_\* settings

## Dangerous — propose plan before touching

- `stealth_scraper.py` — anti-bot config; wrong changes get IP banned
- `main_parallel.py` — parallel mode stresses rate limits hard
- Credentials in `EDUARDO_CREDENTIALS.txt` — never log, print, or commit

## Don't touch

- `EDUARDO_CREDENTIALS.txt` — real login credentials
- Raw output files while a scrape is running

## Docs

- See ARCHITECTURE.md for scraper pipeline overview
- See ANTI_BOT_GUIDE.md before modifying stealth settings
- See DEPLOYMENT.md for production run instructions
