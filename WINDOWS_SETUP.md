# Running on Windows (end-user package)

This repo ships a **foolproof two-click Windows setup** aimed at a
non-technical user (Eduardo). Everything is in Portuguese for him; this file
is the English/developer reference.

## The three scripts (repo root)

| File               | When      | What it does                                                                                                                                                                                            |
| ------------------ | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `1-INSTALAR.bat`   | once      | Checks for Python 3.11+ and Chrome (opens the download page with plain-language instructions if missing), creates `venv\`, installs `requirements.txt`.                                                 |
| `2-ABRIR-COTA.bat` | every use | Activates `venv\`, sets `COTA_NO_LOGIN=1`, starts Streamlit on port 8501, and opens the browser automatically. Closing the black window stops the app.                                                  |
| `3-ATUALIZAR.bat`  | to update | Downloads the latest `main` as a zip from GitHub and copies the code over the install with `robocopy`, excluding `venv\`, `instance\`, `results\` and `EDUARDO_CREDENTIALS.txt`; re-runs `pip install`. |

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

They double-click **`3-ATUALIZAR.bat`** — it fetches the latest `main`
zip and overwrites only the code (their `venv\`, database, results and
credentials are untouched), then they open `2-ABRIR-COTA` as usual.

If their copy predates the updater, bootstrap it once from a cmd window
opened _in the project folder_ (File Explorer address bar → type `cmd`
→ Enter):

```
powershell -Command "iwr 'https://raw.githubusercontent.com/luizpersechini/Eduardo-Scrapping/main/3-ATUALIZAR.bat' -OutFile 3-ATUALIZAR.bat"
```

## Troubleshooting

- **"Python não foi encontrado"** — install Python with the PATH checkbox,
  re-run `1-INSTALAR`. The installer also probes `py -3` and the default
  install folders directly, so a stale PATH right after installing
  usually resolves itself; a reboot always does.
- **`python` opens the Microsoft Store** — Windows ships a Store stub
  that hijacks the bare `python` command. Use the `py` launcher instead
  (`py -m venv venv`), which the installer already prefers.
- **Commands "can't find requirements.txt"** — they're running cmd in
  `C:\Users\<name>` instead of the project folder. Open File Explorer in
  the project folder, click the address bar, type `cmd`, Enter — the
  window opens in the right place.
- **Install fails** — check internet; delete `venv\` and re-run `1-INSTALAR`.
- **"Failed to initialize web driver" / driver-version mismatch** —
  close the black window, re-open via `2-ABRIR-COTA`. Chrome's version
  is read from the registry on Windows (since v2.2.0), so
  driver/browser mismatches (e.g. driver 150 vs Chrome 149) shouldn't
  recur; if one does, delete `%APPDATA%\undetected_chromedriver` and
  relaunch.
- **`type object 'DataProcessor' has no attribute ...` right after an
  update** — the update ran while the app was open, so the running
  Python kept old modules in memory. Close the black window and reopen
  `2-ABRIR-COTA`. The updater now refuses to run while the app is open
  (checks port 8501) so this shouldn't recur.
- **Garbage like `'" (' não é reconhecido...` at the end of an update** —
  the updater overwrote _itself_ mid-run (cmd reads batch files by byte
  offset, so a changed `3-ATUALIZAR.bat` derails after the copy step).
  The files DID update; the run only derailed after the copy. Since
  v2.4.x the updater relaunches itself from `%TEMP%` so it never
  overwrites a running copy; updating _from_ an older updater can show
  this error one last time — ignore it, or re-bootstrap the bat with
  the `iwr` one-liner above.
- **Slow / stuck run** — close the black window and reopen; partial results
  are saved and downloadable from the **History** tab.
