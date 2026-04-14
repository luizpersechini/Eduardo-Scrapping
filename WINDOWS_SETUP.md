# Running the ANBIMA Scraper on Windows

A simple local launcher (`run_windows.bat`) is included. It creates a
virtual environment the first time you run it, installs all dependencies,
and starts the Streamlit app in your browser.

## Prerequisites (one-time installs)

1. **Python 3.11 or newer** — https://www.python.org/downloads/windows/
   - **IMPORTANT:** During the installer, tick **"Add python.exe to PATH"**.
2. **Google Chrome** — https://www.google.com/chrome/
   - The scraper drives a real Chrome browser, so Chrome must be installed.
3. (Optional but recommended) Git — https://git-scm.com/download/win
   - Only needed if you want to pull updates with `git pull`.

## How to get the code

Either:
- Click **Code → Download ZIP** on GitHub and extract it, **or**
- Run `git clone https://github.com/luizpersechini/Eduardo-Scrapping.git`

## First run

1. Open the project folder in Windows Explorer.
2. Double-click `run_windows.bat`.
3. A terminal window opens. On the first run it will:
   - Create a `venv\` folder next to the scripts.
   - Install all Python dependencies (a few minutes).
4. When setup finishes, the Streamlit UI opens automatically in your default
   browser at `http://localhost:8501`.

## Subsequent runs

Just double-click `run_windows.bat` again. It will reuse the existing `venv\`
and launch the app in a few seconds.

## Stopping the app

Close the terminal window, or press `Ctrl+C` in it.

## Updating

- If you cloned the repo: `git pull` inside the folder, then re-run the launcher.
- If you downloaded a ZIP: download the new ZIP and replace files (keep your
  `venv\` folder to avoid reinstalling dependencies, or delete it to force
  a clean reinstall on the next run).

## Notes on headless mode

On your local Windows machine you should **uncheck "Headless Mode"** in the
app's sidebar. A visible Chrome window is much less likely to trigger
ANBIMA's anti-bot defenses than a headless one.

## Troubleshooting

- **"Python is not installed or not in PATH"** — reinstall Python and make sure
  you tick "Add python.exe to PATH", then open a new terminal / re-run the bat.
- **Dependency install fails** — delete the `venv\` folder and re-run
  `run_windows.bat` to start over.
- **ChromeDriver errors** — update Chrome to the latest version; the scraper
  matches the installed Chrome version automatically.
