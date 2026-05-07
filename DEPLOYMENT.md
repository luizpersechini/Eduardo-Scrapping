# Deployment

How to deploy / run Cota in each supported environment.

---

## Streamlit Community Cloud (production)

1. Push to `main` on GitHub. Streamlit Cloud is wired to auto-redeploy
   from this branch.
2. The cloud build:
   - installs apt packages from `packages.txt`
     (`chromium`, `chromium-driver`),
   - installs Python deps from `requirements.txt`,
   - reads theme tokens from `.streamlit/config.toml`.
3. The first visitor after a redeploy may see a sleeping/cold-start
   page — Streamlit Cloud hibernates apps after 12 h without traffic.
   Click "Yes, get this app back up!" and wait ~30 s.

### Cloud-specific runtime quirks (handled automatically)

- The system `chromedriver` is read-only at `/usr/bin/chromedriver`.
  `stealth_scraper.py` copies it to a per-session
  `/tmp/chromedriver_<uuid>` so undetected-chromedriver can patch it.
- `kill_orphan_chrome()` runs on session init and before every Start
  to keep the container under the ~1 GB RAM ceiling.
- `--disable-dev-shm-usage` is on by default; the cloud's `/dev/shm`
  is too small for Chrome's default IPC.

### Updating the deployment

```
git pull
# make changes
git add … && git commit -m "…" && git push origin main
```

Streamlit Cloud typically picks the new commit up within ~30 s. Watch
the deploy log from the dashboard if a build fails.

---

## Local — macOS

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Requires Google Chrome installed (the scraper drives a real browser).

**Tip:** uncheck **Headless mode** in the Review panel. On macOS with
Chrome 147+, headless mode causes the Chrome window to die on first
navigation and triggers the recovery loop (~3× slowdown). A visible
window is reliable.

---

## Local — Windows

Double-click `run_windows.bat`. The launcher:

- Verifies Python ≥ 3.11 is on PATH.
- Verifies Google Chrome is installed.
- Creates a `venv\` on first run and `pip install -r requirements.txt`.
- Starts Streamlit and opens the default browser to `http://localhost:8501`.

Full instructions are in `WINDOWS_SETUP.md`.

---

## CLI (no Streamlit)

For scripted runs from the command line:

```bash
python main.py            # serial scrape
python main_parallel.py   # parallel scrape (higher detection risk)

python verify_results.py    # post-run verification
python monitor_progress.py  # tail a running scrape
```

These read their inputs/outputs from disk; see each file's header
docstring for the expected paths.

---

## Other hosts (Render, Fly.io, Railway, custom Docker)

Streamlit Community Cloud has two limitations that may push you off it
eventually:

1. ~1 GB RAM ceiling — Chrome + Streamlit + pandas can hit this on
   bigger CNPJ batches.
2. 12-hour idle hibernation on the free tier.

If you outgrow Cloud, the cleanest move is a small Docker image with
your own Chrome version pinned. Render's free tier or a $5/mo Fly.io
machine handle this comfortably. Outline:

```dockerfile
FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
      chromium chromium-driver \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0"]
```

The Linux init path in `stealth_scraper.py` already handles
`/usr/bin/chromedriver` and `/usr/bin/chromium` cleanly, so this works
out of the box.
