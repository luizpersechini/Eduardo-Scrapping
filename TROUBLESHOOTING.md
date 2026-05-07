# Troubleshooting

Known failure modes and how to recover. The Settings route in the app
contains live diagnostics for most of these — open it before guessing.

---

## "Failed to initialize web driver"

The full underlying exception is shown in the UI under
**🔧 Technical details**. Open that expander first; the message tells
you which of the three init strategies failed and why.

Common patterns:

### `SessionNotCreatedException: This version of ChromeDriver only supports Chrome version N. Current browser version is N-1`

UC auto-downloaded a chromedriver one major version ahead of the Chrome
binary on the host. Fixed in v2.0.0 by always passing
`version_main=<detected Chrome>` to UC. If you still hit this, your
`get_chrome_version()` returned `None` — verify Chrome is on PATH or in
one of the standard locations checked in `stealth_scraper.py`.

### `SessionNotCreatedException: cannot connect to chrome at 127.0.0.1:NNNNN from chrome not reachable`

Chrome started but immediately died. On macOS this is almost always
**headless mode** + Chrome 147+:

1. In the Review screen, toggle **Headless browser** off.
2. Re-run.

A visible Chrome window is reliable; the headless-window-dies-on-first-
navigation issue only affects UC's headless launch path on Mac.

### `Text file busy: '/tmp/chromedriver'`

A previous Chrome process is still holding the binary. Fixed in v2.0.0
by using a unique `/tmp/chromedriver_<uuid>` path per session. If you
still see this somehow, click **Kill orphan Chrome** in Settings and
retry.

### `Permission denied: '/usr/bin/chromedriver'`

UC can't patch the read-only system chromedriver. Fixed in v2.0.0 by
copying it to `/tmp/chromedriver_<uuid>` first. If you still hit this,
verify `/tmp` is writable.

---

## "Argh. This app has gone over its resource limits"

(Streamlit Community Cloud only.) The container exceeded its ~1 GB RAM
ceiling. Cause: zombie Chrome processes from a previous run weren't
cleaned up.

Recovery:

1. From the Streamlit Cloud dashboard, **Reboot app**.
2. Once it's back, in the app open **Settings → Kill orphan Chrome**.
3. Try Start scraping again.

The app already runs `kill_orphan_chrome()` on session init and before
every Start, so this should be rare.

---

## App is sleeping when you visit

Streamlit Community Cloud puts apps to sleep after **12 hours without
traffic**. The visitor sees a "Yes, get this app back up!" button.
Click it, wait ~30 s for the cold start, then log in normally.

This is documented Streamlit behaviour and not a bug. To prevent it
without a paid Streamlit plan, visit the app once a day, or move to a
host without idle hibernation (Render, Fly.io, Railway).

---

## Scrape is much slower than expected (~3 min per CNPJ)

You're probably seeing the recovery loop — open the terminal where
Streamlit is running and look for:

```
Driver not alive for <CNPJ>, attempting recovery (attempt N/3)
```

The driver died mid-scrape and the scraper is recreating it three
times before falling through. Most common trigger is **headless on
macOS with Chrome 147+** — uncheck Headless mode in Review.

---

## "no such window: target window already closed"

Same root cause as the slowness above. Toggle Headless off on macOS;
on Streamlit Cloud, click "Re-run diagnostics" in Settings to see the
real Chrome stderr.

---

## Excel download fails / wrong format

`openpyxl` version mismatch with `pandas`. `requirements.txt` pins
`openpyxl>=3.1.5`. If a stale environment cached an older version,
`pip install -r requirements.txt --upgrade` fixes it.

---

## CNPJ list parses but Review shows zero rows

The Excel file must have a column literally named `CNPJ` (case-sensitive).
Other column names are ignored.

---

## Settings page diagnostics

Click **Re-run diagnostics** to see:

- Detected platform / OS.
- Chromium binary path + version.
- ChromeDriver binary path + version.
- Result of a real headless launch against `about:blank`, including
  Chromium's stderr (this is what tells you *why* Chrome is crashing
  when it does).
- `/dev/shm` total + free (Linux only).
- `/proc/meminfo` (Linux only).

If the launch exits with non-zero and the stderr blames a missing
shared library, your `packages.txt` is incomplete — add the missing
apt package.
