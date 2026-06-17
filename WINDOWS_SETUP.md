# Running on Windows (end-user package)

This repo ships a **foolproof two-click Windows setup** aimed at a
non-technical user (Eduardo). Everything is in Portuguese for him; this file
is the English/developer reference.

## The two scripts (repo root)

| File               | When      | What it does                                                                                                                                            |
| ------------------ | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `1-INSTALAR.bat`   | once      | Checks for Python 3.11+ and Chrome (opens the download page with plain-language instructions if missing), creates `venv\`, installs `requirements.txt`. |
| `2-ABRIR-COTA.bat` | every use | Activates `venv\`, sets `COTA_NO_LOGIN=1`, starts Streamlit on port 8501, and opens the browser automatically. Closing the black window stops the app.  |

`LEIA-ME.txt` is the Portuguese quick-start the user reads first.

## Handing it to the end user

1. GitHub → **Code → Download ZIP**, or `git clone`.
2. Send the folder (ZIP/USB/Drive). It contains everything tracked — no
   secrets (`.env`, credentials, scraped data are gitignored).
3. Tell them: **read `LEIA-ME.txt`, double-click `1-INSTALAR` once, then
   `2-ABRIR-COTA` to use.**

The scripts use `%~dp0` (their own folder), so the extracted folder can have
any name and live anywhere.

## No login on the local copy

`2-ABRIR-COTA.bat` sets the env var `COTA_NO_LOGIN=1`, which makes
`streamlit_app.py` skip the login screen (single-user local app). **Streamlit
Cloud never sets this var**, so the public deployment keeps its login intact.

## Headless

The scraper's "Headless browser" toggle defaults **OFF** off-cloud (Windows
included) — a visible Chrome window is the reliable mode. The
`--server.headless=true` flag in `2-ABRIR-COTA.bat` is the _Streamlit server_
flag (stops the email prompt / double browser tab) and is unrelated.

## Prerequisites the user installs once

1. **Python 3.11+** — https://www.python.org/downloads/windows/ — must tick
   **"Add python.exe to PATH"** (the installer guides them; `1-INSTALAR`
   re-opens this page if Python is missing).
2. **Google Chrome** — https://www.google.com/chrome/

## Updating their copy

Send a fresh ZIP and have them replace the files (they can keep their `venv\`
to skip reinstalling, or delete it to force a clean reinstall via `1-INSTALAR`).

## Troubleshooting

- **"Python não foi encontrado"** — install Python with the PATH checkbox, re-run `1-INSTALAR`.
- **Install fails** — check internet; delete `venv\` and re-run `1-INSTALAR`.
- **"Failed to initialize web driver"** — close the black window, re-open via
  `2-ABRIR-COTA`. undetected-chromedriver auto-fetches a driver matching the
  installed Chrome; the plain-Selenium fallback covers UC failures.
- **Slow / stuck run** — close the black window and reopen; partial results
  are saved and downloadable from the **History** tab.
