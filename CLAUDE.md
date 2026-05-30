# Eduardo Scrapping — ANBIMA fund data scraper

## Stack
Python · Selenium · undetected-chromedriver · selenium-stealth · Pandas · openpyxl · Streamlit

## Run
```
python main.py           # full scrape pipeline
python main_parallel.py  # parallel scraping (faster, higher risk of detection)
streamlit run main.py    # if Streamlit UI mode is configured
```

## Test / verify
```
python monitor_and_verify.py  # verify scraped data integrity
python monitor_progress.py    # check run progress
```

## Structure
- `main.py` — orchestrator entry point
- `anbima_scraper.py` — core scraper logic
- `stealth_scraper.py` — anti-bot evasion layer
- `data_processor.py` — clean/transform scraped data
- `config.py` — site URLs, selectors, timeouts
- `parse_bot_*.py` — alternative bot-based parsing

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
