"""
ANBIMA Fund Data Scraper - Web UI
Simple web interface for scraping ANBIMA fund data
"""

import os
import re
import streamlit as st
import pandas as pd
import io
from datetime import datetime
import time
import logging
from pathlib import Path
import hashlib
import subprocess
import traceback
import sys

# Import existing scrapers
from stealth_scraper import StealthANBIMAScraper
from data_processor import DataProcessor
import config

# Setup logging to capture all events
LOG_DIR = Path("session_logs")
LOG_DIR.mkdir(exist_ok=True)

# Persisted scrape outputs — every completed (or interrupted) run writes its
# Excel here so it can be re-downloaded later from the History page.
# `_partial.xlsx` suffix marks runs that were interrupted before finishing
# all CNPJs.
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)


def setup_session_logger():
    """Setup a session-specific logger that writes to file"""
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"scraping_session_{session_id}.log"

    # Create logger
    logger = logging.getLogger(f"session_{session_id}")
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers
    if not logger.handlers:
        # File handler
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger, log_file


# Initialize session logger if not already done
if "session_logger" not in st.session_state:
    st.session_state.session_logger, st.session_state.log_file = setup_session_logger()
    st.session_state.session_logger.info("=" * 80)
    st.session_state.session_logger.info("NEW SCRAPING SESSION STARTED")
    st.session_state.session_logger.info(
        f"Version: {APP_VERSION if 'APP_VERSION' in dir() else 'Unknown'}"
    )
    st.session_state.session_logger.info(f"Timestamp: {datetime.now().isoformat()}")
    st.session_state.session_logger.info("=" * 80)


# Version info
def get_version_info():
    """Get version and git commit info"""
    try:
        # Read version from VERSION file
        version_file = Path(__file__).parent / "VERSION"
        version = (
            version_file.read_text().strip() if version_file.exists() else "Unknown"
        )

        # Try to get git commit hash
        try:
            commit = (
                subprocess.check_output(
                    ["git", "rev-parse", "--short", "HEAD"],
                    cwd=Path(__file__).parent,
                    stderr=subprocess.DEVNULL,
                )
                .decode("utf-8")
                .strip()
            )
        except:
            commit = "N/A"

        return version, commit
    except:
        return "Unknown", "N/A"


APP_VERSION, GIT_COMMIT = get_version_info()

# Configure page (Cota uses a topbar, not a sidebar)
st.set_page_config(
    page_title="Cota · ANBIMA Fund Data Scraper",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Cota theme: warm-neutral surface + emerald accent + Geist fonts.
# Must be injected after `set_page_config` so its overrides win the cascade.
import cota_theme

cota_theme.inject_css()

# Login credentials (hashed password)
USERNAME = "eduardo"
PASSWORD_HASH = "66d2bed9c29bd80dbbd578f6219a1b9003383e047955e0ba445498ac62e6a796"  # Secure random password


def check_password(password):
    """Check if password matches the stored hash"""
    return hashlib.sha256(password.encode()).hexdigest() == PASSWORD_HASH


def login_page():
    """Cota-styled login page.

    Layout: decorative grid + emerald glow background, centred card with the
    Cota brand mark, "Sign in" title, username + password fields, primary
    "Continue" button, and a footer with the security notice + version.
    """
    # Decorative background (grid + emerald glow)
    st.markdown(cota_theme.login_bg(), unsafe_allow_html=True)

    # Use 3 columns to centre the login card.
    # We rely on `st.container(border=True)` to render the card surface so we
    # don't have to open/close raw <div>s around live Streamlit widgets
    # (Streamlit emits each markdown call in its own DOM block, so unbalanced
    # wrapper divs leak into the page as visible text).
    left, mid, right = st.columns([1, 1.4, 1])
    with mid:
        with st.container(border=True):
            # Brand mark + tagline (one self-contained HTML block)
            st.markdown(cota_theme.brand_mark(size="lg"), unsafe_allow_html=True)

            # Title
            st.markdown(
                '<h1 class="cota-login-title">Sign in</h1>'
                '<p class="cota-login-sub">Use your workspace credentials to access the scraper.</p>',
                unsafe_allow_html=True,
            )

            # Form fields — Streamlit-native inputs, restyled by COTA_CSS
            username = st.text_input("Username", value="eduardo", key="login_username")
            password = st.text_input(
                "Password",
                type="password",
                key="login_password",
                placeholder="••••••••",
            )

            if st.button(
                "Continue →", type="primary", width="stretch", key="login_continue"
            ):
                if username == USERNAME and check_password(password):
                    st.session_state.authenticated = True
                    st.session_state.user = username
                    st.rerun()
                else:
                    st.error("Enter a valid username and password to continue.")

            # Footer (security note + version) — single-line HTML to avoid the
            # markdown parser treating indented lines as a code block.
            st.markdown(
                '<div class="cota-login-foot">'
                '<div class="cota-login-foot-row">🛡️ Secure session · SHA-256 hashed credentials</div>'
                f'<div class="cota-login-foot-row muted">v{APP_VERSION} · build {GIT_COMMIT}</div>'
                "</div>",
                unsafe_allow_html=True,
            )


# Check authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Show login page if not authenticated
if not st.session_state.authenticated:
    login_page()
    st.stop()

# Initialize session state
if "scraping_in_progress" not in st.session_state:
    st.session_state.scraping_in_progress = False
if "progress" not in st.session_state:
    st.session_state.progress = 0
if "results" not in st.session_state:
    st.session_state.results = None
if "cnpjs" not in st.session_state:
    st.session_state.cnpjs = []
if "status_messages" not in st.session_state:
    st.session_state.status_messages = []
# Structured activity feed — list of dicts {cnpj, name, status, points, ms}.
# Used to render the Cota live-activity panel.
if "activity_events" not in st.session_state:
    st.session_state.activity_events = []
if "success_count" not in st.session_state:
    st.session_state.success_count = 0
if "failed_count" not in st.session_state:
    st.session_state.failed_count = 0
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "stop_scraping" not in st.session_state:
    st.session_state.stop_scraping = False
# Cota workflow phase: upload → review → scrape → done.
if "phase" not in st.session_state:
    st.session_state.phase = "upload"
# Run settings (replaces the old sidebar widgets). Persisted in session state
# so they survive reruns and can be edited in the Review phase or Settings page.
#
# headless defaults OFF: on macOS + recent Chrome, a *headless* browser fails to
# render ANBIMA's periodic-data table (extraction returns nothing, then retries
# for minutes). A visible window is reliable. The Review/Settings toggles force
# headless ON only when running on Streamlit Cloud (no display available).
_is_cloud_boot = bool(
    os.environ.get("STREAMLIT_SHARING_MODE") or os.environ.get("IS_STREAMLIT_CLOUD")
)
if "settings" not in st.session_state:
    st.session_state.settings = dict(
        stealth=True,
        headless=_is_cloud_boot,  # False locally, True on cloud
        workers=1,
        delay=1.5,
    )

# ── FIDC workflow state (separate route, mirrors the regular-scrape keys) ──
if "fidc_phase" not in st.session_state:
    st.session_state.fidc_phase = "upload"
if "fidc_cnpjs" not in st.session_state:
    st.session_state.fidc_cnpjs = []
if "fidc_uploaded_filename" not in st.session_state:
    st.session_state.fidc_uploaded_filename = None
if "fidc_results" not in st.session_state:
    st.session_state.fidc_results = None
if "fidc_activity_events" not in st.session_state:
    st.session_state.fidc_activity_events = []
if "fidc_success_count" not in st.session_state:
    st.session_state.fidc_success_count = 0
if "fidc_failed_count" not in st.session_state:
    st.session_state.fidc_failed_count = 0
if "fidc_start_time" not in st.session_state:
    st.session_state.fidc_start_time = None
if "fidc_stop" not in st.session_state:
    st.session_state.fidc_stop = False
if "fidc_last_excel_path" not in st.session_state:
    st.session_state.fidc_last_excel_path = None


def kill_orphan_chrome():
    """Force-kill any lingering chrome/chromedriver processes.

    Orphan Chrome processes from a previous session are the #1 cause of
    Streamlit Cloud's "Argh. This app has gone over its resource limits"
    message — each instance holds ~500-700 MB of RAM and the container
    ceiling is ~1 GB. We run this on session init and before every new
    scraping run.
    """
    import platform

    if platform.system() != "Linux":
        return
    try:
        for proc_name in ("chromedriver", "chrome", "chromium"):
            subprocess.call(
                ["pkill", "-9", "-f", proc_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except Exception:
        pass


def collect_browser_environment() -> dict:
    """Probe Chromium / chromedriver / /dev/shm / memory and return a dict
    suitable for rendering on the Settings page."""
    import shutil as _shutil
    import platform

    info: dict = {
        "chromium_path": None,
        "chromium_version": None,
        "chromedriver_path": None,
        "chromedriver_version": None,
        "shm_total_mb": None,
        "shm_free_mb": None,
        "mem_total_kb": None,
        "mem_available_kb": None,
        "launch_ok": None,
        "launch_stderr_tail": None,
    }
    # Browser binary
    for path in (
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/google-chrome",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ):
        if os.path.exists(path):
            info["chromium_path"] = path
            try:
                info["chromium_version"] = (
                    subprocess.check_output(
                        [path, "--version"], stderr=subprocess.DEVNULL, timeout=5
                    )
                    .decode(errors="replace")
                    .strip()
                )
            except Exception:
                pass
            break
    # ChromeDriver binary
    for path in (
        "/usr/bin/chromedriver",
        "/usr/lib/chromium-browser/chromedriver",
        "/usr/lib/chromium/chromedriver",
    ):
        if os.path.exists(path):
            info["chromedriver_path"] = path
            try:
                info["chromedriver_version"] = (
                    subprocess.check_output(
                        [path, "--version"], stderr=subprocess.DEVNULL, timeout=5
                    )
                    .decode(errors="replace")
                    .strip()
                )
            except Exception:
                pass
            break
    # /dev/shm (only meaningful on Linux containers)
    if platform.system() == "Linux":
        try:
            shm = _shutil.disk_usage("/dev/shm")
            info["shm_total_mb"] = shm.total / 1024 / 1024
            info["shm_free_mb"] = shm.free / 1024 / 1024
        except Exception:
            pass
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        info["mem_total_kb"] = int(line.split()[1])
                    elif line.startswith("MemAvailable:"):
                        info["mem_available_kb"] = int(line.split()[1])
        except Exception:
            pass
    return info


def diagnose_chrome_launch() -> str:
    """Try to launch the system browser headless against about:blank to
    surface the real reason it fails (when applicable). Returns text output
    suitable for `st.code(...)`."""
    import platform

    info = collect_browser_environment()
    lines: list[str] = []
    lines.append(f"Platform: {platform.platform()}")
    if info["chromium_path"]:
        lines.append(
            f"Browser: {info['chromium_path']} → {info['chromium_version'] or '(version unknown)'}"
        )
    if info["chromedriver_path"]:
        lines.append(
            f"ChromeDriver: {info['chromedriver_path']} → {info['chromedriver_version'] or '(version unknown)'}"
        )
    if not info["chromium_path"]:
        lines.append("No Chromium / Chrome binary found on this host.")
        return "\n".join(lines)
    # Try a minimal headless launch and capture stderr
    try:
        proc = subprocess.run(
            [
                info["chromium_path"],
                "--headless=new",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--dump-dom",
                "about:blank",
            ],
            capture_output=True,
            timeout=15,
        )
        lines.append(f"Headless launch exit code: {proc.returncode}")
        if proc.stderr:
            tail = proc.stderr.decode(errors="replace")[-1500:]
            lines.append(f"\n— stderr (last 1500 chars) —\n{tail}")
    except Exception as e:
        lines.append(f"Headless launch FAILED: {e}")
    return "\n".join(lines)


# Clean up any orphan Chrome processes left over from a previous (possibly
# crashed) session. This runs once per new Streamlit session.
if "orphan_cleanup_done" not in st.session_state:
    kill_orphan_chrome()
    st.session_state.orphan_cleanup_done = True

# Route state — Cota has three top-level routes: scrape · history · settings.
# Phases 4 & 5 of the redesign add the actual History/Settings pages; for
# now everything but "scrape" is a stub.
if "route" not in st.session_state:
    st.session_state.route = "scrape"

# Cota topbar (renders a sticky header with brand, nav, status pill, user).
# The visual nav above is for *display*; the real route switcher is the
# row of small buttons immediately below it.
_user = st.session_state.get("user", USERNAME)
st.markdown(
    cota_theme.topbar(user=_user, route=st.session_state.route), unsafe_allow_html=True
)

# Functional nav row (sits under the topbar). We can't put real Streamlit
# buttons inside the HTML topbar, so we render this strip just below.
_nav_cols = st.columns([1, 1, 1, 1, 4, 1])
with _nav_cols[0]:
    if st.button(
        "New scrape",
        key="nav_scrape",
        type=("primary" if st.session_state.route == "scrape" else "secondary"),
    ):
        st.session_state.route = "scrape"
        st.rerun()
with _nav_cols[1]:
    if st.button(
        "FIDC",
        key="nav_fidc",
        type=("primary" if st.session_state.route == "fidc" else "secondary"),
    ):
        st.session_state.route = "fidc"
        st.rerun()
with _nav_cols[2]:
    if st.button(
        "History",
        key="nav_history",
        type=("primary" if st.session_state.route == "history" else "secondary"),
    ):
        st.session_state.route = "history"
        st.rerun()
with _nav_cols[3]:
    if st.button(
        "Settings",
        key="nav_settings",
        type=("primary" if st.session_state.route == "settings" else "secondary"),
    ):
        st.session_state.route = "settings"
        st.rerun()
with _nav_cols[5]:
    if st.button("Log out", key="nav_logout"):
        st.session_state.authenticated = False
        st.rerun()

# Run settings live in session_state.settings (configured on the Review phase).
# Read once here so the rest of the file can reuse the names it always used.
use_stealth = st.session_state.settings["stealth"]
headless = st.session_state.settings["headless"]
num_workers = st.session_state.settings["workers"]
is_cloud = bool(
    os.environ.get("STREAMLIT_SHARING_MODE") or os.environ.get("IS_STREAMLIT_CLOUD")
)

# Sidebar removed — Cota uses a topbar instead. All admin/diagnostic tools
# now live on the Settings route.

# ============================================================================
# Main content — Cota route dispatch
# ============================================================================

# ─── History route ─────────────────────────────────────────────────────────
if st.session_state.route == "history":
    st.markdown(
        cota_theme.page_head(
            title="History",
            sub="Re-download the Excel from any past scrape — including runs that were stopped mid-way.",
        ),
        unsafe_allow_html=True,
    )

    # Each row in the table is a saved Excel file in `results/`. Excels are
    # the primary artefact users come back for; the corresponding session
    # log is offered as a secondary download when one can be found.
    # Lists BOTH regular-scrape (anbima_results_*) and FIDC (fidc_results_*) runs.
    excel_files = (
        sorted(
            list(RESULTS_DIR.glob("anbima_results_*.xlsx"))
            + list(RESULTS_DIR.glob("fidc_results_*.xlsx")),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if RESULTS_DIR.exists()
        else []
    )

    log_files = (
        sorted(
            LOG_DIR.glob("scraping_session_*.log"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if LOG_DIR.exists()
        else []
    )

    def _parse_excel_filename(name: str) -> tuple[str, bool, str]:
        """Return (timestamp_str, was_partial, kind) from a results filename.

        Handles both `anbima_results_<ts>.xlsx` (kind="Regular") and
        `fidc_results_<ts>.xlsx` (kind="FIDC").
        """
        stem = name.removesuffix(".xlsx")
        if stem.startswith("fidc_results_"):
            kind = "FIDC"
            stem = stem.removeprefix("fidc_results_")
        else:
            kind = "Regular"
            stem = stem.removeprefix("anbima_results_")
        partial = stem.endswith("_partial")
        if partial:
            stem = stem[: -len("_partial")]
        return stem, partial, kind

    def _friendly_ts(stem: str) -> str:
        m = re.match(r"(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})", stem)
        if m:
            yyyy, mm, dd, hh, mi, _ss = m.groups()
            return f"{yyyy}-{mm}-{dd} {hh}:{mi}"
        return stem

    def _matching_log(stem: str) -> Path | None:
        """Find the closest session log written before/at the same time as this Excel."""
        if not log_files:
            return None
        m = re.match(r"(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})", stem)
        if not m:
            return None
        try:
            excel_dt = datetime.strptime(stem, "%Y%m%d_%H%M%S")
        except Exception:
            return None
        # Pick the log whose timestamp is the largest one <= excel_dt
        best = None
        best_dt = None
        for lp in log_files:
            lm = re.match(r"scraping_session_(\d{8}_\d{6})", lp.stem)
            if not lm:
                continue
            try:
                ldt = datetime.strptime(lm.group(1), "%Y%m%d_%H%M%S")
            except Exception:
                continue
            if ldt <= excel_dt and (best_dt is None or ldt > best_dt):
                best, best_dt = lp, ldt
        return best

    # ── Card 1: saved Excels ────────────────────────────────────────────
    with st.container(border=True):
        st.markdown(
            '<h2 class="cota-card-title">Saved scrape outputs</h2>'
            f'<p class="cota-card-sub">{len(excel_files)} Excel file(s) on disk under <code>results/</code>.</p>',
            unsafe_allow_html=True,
        )

        if not excel_files:
            st.markdown(
                '<div class="cota-empty">No outputs yet — start a scrape and finish (or stop) it to see one here.</div>',
                unsafe_allow_html=True,
            )
        else:
            # Header
            st.markdown(
                '<div class="cota-result-row cota-result-head" style="grid-template-columns:170px 1fr 110px 110px 100px;">'
                "<span>Run</span>"
                "<span>Status</span>"
                '<span style="text-align:right;">Size</span>'
                '<span style="text-align:right;">Excel</span>'
                '<span style="text-align:right;">Log</span>'
                "</div>",
                unsafe_allow_html=True,
            )

            for xpath in excel_files[:200]:
                stem, partial, kind = _parse_excel_filename(xpath.name)
                friendly = _friendly_ts(stem)
                size_kb = xpath.stat().st_size / 1024
                log_path = _matching_log(stem)

                kind_tag = (
                    '<span class="cota-tag cota-tag-ready" style="margin-left:6px;">FIDC</span>'
                    if kind == "FIDC"
                    else ""
                )
                tag = (
                    '<span class="cota-tag cota-tag-warn">⚠ Partial</span>'
                    if partial
                    else '<span class="cota-tag cota-tag-ok">✓ Complete</span>'
                ) + kind_tag

                # 5-column row: Run / Status / Size / Excel button / Log button
                c_run, c_status, c_size, c_excel, c_log = st.columns(
                    [170, 800, 110, 110, 100]
                )
                with c_run:
                    st.markdown(
                        f'<div style="font-family:Geist Mono,monospace;font-size:12.5px;padding-top:8px;">{stem}</div>'
                        f'<div class="cota-history-meta">{friendly}</div>',
                        unsafe_allow_html=True,
                    )
                with c_status:
                    st.markdown(
                        f'<div style="padding-top:10px;">{tag}</div>',
                        unsafe_allow_html=True,
                    )
                with c_size:
                    st.markdown(
                        f'<div style="text-align:right;font-family:Geist Mono,monospace;font-size:12.5px;padding-top:10px;color:var(--fg-mute);">{size_kb:.1f} KB</div>',
                        unsafe_allow_html=True,
                    )
                with c_excel:
                    try:
                        xbytes = xpath.read_bytes()
                    except Exception:
                        xbytes = b""
                    st.download_button(
                        "⬇ Excel",
                        data=xbytes,
                        file_name=xpath.name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        width="stretch",
                        key=f"hist_xlsx_{xpath.name}",
                    )
                with c_log:
                    if log_path:
                        try:
                            lbytes = log_path.read_bytes()
                        except Exception:
                            lbytes = b""
                        st.download_button(
                            "📋 Log",
                            data=lbytes,
                            file_name=log_path.name,
                            mime="text/plain",
                            width="stretch",
                            key=f"hist_log_{xpath.name}",
                        )
                    else:
                        st.markdown(
                            '<div style="text-align:right;color:var(--fg-mute);font-size:11.5px;padding-top:10px;">—</div>',
                            unsafe_allow_html=True,
                        )

    st.markdown(
        cota_theme.footer(version=f"v{APP_VERSION}", build=f"build {GIT_COMMIT}"),
        unsafe_allow_html=True,
    )
    st.stop()


# ─── Settings route ────────────────────────────────────────────────────────
if st.session_state.route == "settings":
    st.markdown(
        cota_theme.page_head(
            title="Settings",
            sub="Workspace defaults and environment health.",
        ),
        unsafe_allow_html=True,
    )

    env_col, defaults_col = st.columns([1, 1])

    # Browser environment card
    with env_col:
        with st.container(border=True):
            env = collect_browser_environment()
            healthy = bool(env["chromium_path"] and env["chromedriver_path"])
            health_tag = (
                '<span class="cota-tag cota-tag-ok">✓ Healthy</span>'
                if healthy
                else '<span class="cota-tag cota-tag-warn">⚠ Missing pieces</span>'
            )
            head_l, head_r = st.columns([3, 1])
            with head_l:
                st.markdown(
                    '<h2 class="cota-card-title">Browser environment</h2>'
                    '<p class="cota-card-sub">Chromium and chromedriver detection.</p>',
                    unsafe_allow_html=True,
                )
            with head_r:
                st.markdown(
                    f'<div style="text-align:right;padding-top:8px;">{health_tag}</div>',
                    unsafe_allow_html=True,
                )

            chromium_str = (
                f"{env['chromium_path']} · {env['chromium_version'] or 'unknown'}"
                if env["chromium_path"]
                else "not found"
            )
            chromedriver_str = (
                f"{env['chromedriver_path']} · {env['chromedriver_version'] or 'unknown'}"
                if env["chromedriver_path"]
                else "not found"
            )
            shm_str = (
                f"{env['shm_total_mb']:.1f} MB total · {env['shm_free_mb']:.1f} MB free"
                if env["shm_total_mb"] is not None
                else "n/a (non-Linux host)"
            )
            mem_str = (
                f"{env['mem_total_kb'] / 1024 / 1024:.1f} GB total · "
                f"{(env['mem_available_kb'] or 0) / 1024 / 1024:.1f} GB available"
                if env["mem_total_kb"] is not None
                else "n/a (non-Linux host)"
            )
            st.markdown(
                cota_theme.env_row("Chromium", chromium_str)
                + cota_theme.env_row("ChromeDriver", chromedriver_str)
                + cota_theme.env_row("/dev/shm", shm_str)
                + cota_theme.env_row("Memory", mem_str),
                unsafe_allow_html=True,
            )

            act_l, act_r = st.columns([1, 1])
            with act_l:
                if st.button(
                    "↻  Re-run diagnostics", width="stretch", key="settings_diag"
                ):
                    st.session_state._last_diag = diagnose_chrome_launch()
            with act_r:
                if st.button(
                    "🧹  Kill orphan Chrome", width="stretch", key="settings_kill"
                ):
                    kill_orphan_chrome()
                    st.success("Chrome processes cleaned up.")

            if st.session_state.get("_last_diag"):
                st.code(st.session_state._last_diag, language="text")

    # Defaults card
    with defaults_col:
        with st.container(border=True):
            st.markdown(
                '<h2 class="cota-card-title">Defaults</h2>'
                '<p class="cota-card-sub">Apply to every new scrape.</p>',
                unsafe_allow_html=True,
            )

            st.markdown(
                cota_theme.setting_text(
                    "Stealth mode",
                    "Use undetected ChromeDriver to evade bot detection.",
                ),
                unsafe_allow_html=True,
            )
            st.session_state.settings["stealth"] = st.toggle(
                "Stealth mode default",
                value=st.session_state.settings["stealth"],
                key="setting_stealth_default",
                label_visibility="collapsed",
            )

            st.markdown(
                cota_theme.setting_text(
                    "Headless browser",
                    "Faster, but more likely to trip detection. Required on Streamlit Cloud.",
                ),
                unsafe_allow_html=True,
            )
            st.session_state.settings["headless"] = st.toggle(
                "Headless default",
                value=(True if is_cloud else st.session_state.settings["headless"]),
                key="setting_headless_default",
                label_visibility="collapsed",
                disabled=is_cloud,
            )

            st.markdown(
                cota_theme.setting_text(
                    "Polite delay",
                    "Default randomised pause between requests, in seconds.",
                ),
                unsafe_allow_html=True,
            )
            st.session_state.settings["delay"] = st.slider(
                "Polite delay default",
                0.5,
                5.0,
                st.session_state.settings["delay"],
                0.5,
                key="setting_delay_default",
                label_visibility="collapsed",
            )

            # Build / version info at the bottom of the card
            st.markdown(
                f'<div class="cota-env-row" style="margin-top:8px">'
                f'<span class="cota-env-label">Version</span>'
                f'<span class="cota-env-value">v{APP_VERSION} · build {GIT_COMMIT}</span>'
                "</div>",
                unsafe_allow_html=True,
            )

    st.markdown(
        cota_theme.footer(version=f"v{APP_VERSION}", build=f"build {GIT_COMMIT}"),
        unsafe_allow_html=True,
    )
    st.stop()

# ─── FIDC route ─────────────────────────────────────────────────────────────
# A separate workflow for FIDC funds: one CNPJ can return multiple subclasses,
# each with its own 6-column DADOS PERIÓDICOS table. Mirrors the regular scrape
# route's upload → review → scrape → done phases but runs scrape_fidc_data() and
# produces a long/tidy Excel via DataProcessor.process_fidc_data().
if st.session_state.route == "fidc":
    st.markdown(
        cota_theme.page_head(
            title="FIDC extraction",
            sub="Upload CNPJs and pull every subclasse's full periodic table (PL, cota, volumes, cotistas).",
            right_html=cota_theme.stepper(st.session_state.fidc_phase),
        ),
        unsafe_allow_html=True,
    )

    # --- Phase: UPLOAD -------------------------------------------------------
    if st.session_state.fidc_phase == "upload":
        with st.container(border=True):
            st.markdown(
                '<h2 class="cota-card-title">Upload your CNPJ list</h2>'
                '<p class="cota-card-sub">Excel file (.xlsx or .xls) with a column named '
                "<code>CNPJ</code>. Each CNPJ may expand into several FIDC subclasses.</p>",
                unsafe_allow_html=True,
            )
            fidc_uploaded = st.file_uploader(
                "Drop file here, or browse",
                type=["xlsx", "xls"],
                label_visibility="collapsed",
                help="Upload Excel file with a 'CNPJ' column",
                key="fidc_upload_xlsx",
            )
            if fidc_uploaded:
                try:
                    df = pd.read_excel(fidc_uploaded)
                    if "CNPJ" in df.columns:
                        st.session_state.fidc_cnpjs = df["CNPJ"].astype(str).tolist()
                        st.session_state.fidc_uploaded_filename = fidc_uploaded.name
                        st.session_state.session_logger.info(
                            f"[FIDC] File uploaded: {fidc_uploaded.name} "
                            f"({len(st.session_state.fidc_cnpjs)} CNPJs)"
                        )
                        st.session_state.fidc_phase = "review"
                        st.rerun()
                    else:
                        st.error("Missing 'CNPJ' column in the uploaded file.")
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
                    st.session_state.session_logger.error(
                        f"[FIDC] Error reading file: {str(e)}"
                    )
                    st.session_state.session_logger.debug(traceback.format_exc())

    # --- Phase: REVIEW -------------------------------------------------------
    elif st.session_state.fidc_phase == "review":
        rev_l, rev_r = st.columns([1.4, 1])
        with rev_l:
            with st.container(border=True):
                top_l, top_r = st.columns([1, 1])
                with top_l:
                    st.markdown(
                        '<h2 class="cota-card-title">Review CNPJs</h2>'
                        f'<p class="cota-card-sub">{len(st.session_state.fidc_cnpjs)} entries loaded from '
                        f"<code>{st.session_state.get('fidc_uploaded_filename', 'input.xlsx')}</code></p>",
                        unsafe_allow_html=True,
                    )
                with top_r:
                    if st.button("Clear", key="fidc_review_clear"):
                        st.session_state.fidc_cnpjs = []
                        st.session_state.fidc_phase = "upload"
                        st.rerun()

                fidc_query = st.text_input(
                    "Filter CNPJ…",
                    key="fidc_review_filter",
                    placeholder="Filter CNPJ…",
                    label_visibility="collapsed",
                )
                st.markdown(
                    cota_theme.cnpj_table(
                        st.session_state.fidc_cnpjs, query=fidc_query
                    ),
                    unsafe_allow_html=True,
                )

        with rev_r:
            with st.container(border=True):
                st.markdown(
                    '<h2 class="cota-card-title">Run settings</h2>'
                    '<p class="cota-card-sub">Anti-bot behaviour for the FIDC run.</p>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    cota_theme.setting_text(
                        "Stealth mode",
                        "Use undetected ChromeDriver to evade bot detection.",
                    ),
                    unsafe_allow_html=True,
                )
                st.session_state.settings["stealth"] = st.toggle(
                    "Stealth mode (FIDC)",
                    value=st.session_state.settings["stealth"],
                    key="fidc_setting_stealth",
                    label_visibility="collapsed",
                )
                st.markdown(
                    cota_theme.setting_text(
                        "Headless browser",
                        "Faster, but more likely to trip detection. Required on Streamlit Cloud.",
                    ),
                    unsafe_allow_html=True,
                )
                st.session_state.settings["headless"] = st.toggle(
                    "Headless browser (FIDC)",
                    value=(True if is_cloud else st.session_state.settings["headless"]),
                    key="fidc_setting_headless",
                    label_visibility="collapsed",
                    disabled=is_cloud,
                )
                st.markdown(
                    cota_theme.setting_text(
                        "Polite delay", "Randomised pause between requests, in seconds."
                    ),
                    unsafe_allow_html=True,
                )
                st.session_state.settings["delay"] = st.slider(
                    "Polite delay (FIDC)",
                    0.5,
                    5.0,
                    st.session_state.settings["delay"],
                    0.5,
                    key="fidc_setting_delay",
                    label_visibility="collapsed",
                )

                st.markdown(
                    cota_theme.run_summary(
                        [
                            ("CNPJs queued", str(len(st.session_state.fidc_cnpjs))),
                            (
                                "Mode",
                                "Stealth"
                                if st.session_state.settings["stealth"]
                                else "Standard",
                            ),
                            ("Note", "1 CNPJ → N subclasses"),
                        ]
                    ),
                    unsafe_allow_html=True,
                )

                if st.button(
                    "▶  Start FIDC scrape",
                    type="primary",
                    width="stretch",
                    key="fidc_review_start",
                ):
                    kill_orphan_chrome()
                    st.session_state.fidc_stop = False
                    st.session_state.fidc_success_count = 0
                    st.session_state.fidc_failed_count = 0
                    st.session_state.fidc_activity_events = []
                    st.session_state.fidc_results = None
                    st.session_state.fidc_start_time = time.time()
                    st.session_state.fidc_phase = "scrape"
                    st.session_state.session_logger.info("=" * 80)
                    st.session_state.session_logger.info("FIDC SCRAPING STARTED")
                    st.session_state.session_logger.info(
                        f"Total CNPJs: {len(st.session_state.fidc_cnpjs)}"
                    )
                    st.rerun()

    # --- Phase: SCRAPE -------------------------------------------------------
    elif st.session_state.fidc_phase == "scrape":
        with st.container(border=True):
            head_l, head_r = st.columns([4, 1])
            with head_l:
                st.markdown(
                    '<h2 class="cota-card-title">FIDC scraping in progress</h2>'
                    f'<p class="cota-card-sub">'
                    f"{'Stealth driver' if st.session_state.settings['stealth'] else 'Standard driver'} · "
                    f"{st.session_state.settings['delay']:.1f}s delay</p>",
                    unsafe_allow_html=True,
                )
            with head_r:
                if st.button(
                    "⬛  Stop", type="secondary", width="stretch", key="fidc_stop_btn"
                ):
                    st.session_state.fidc_stop = True

            fidc_hero = st.empty()
            fidc_bar = st.empty()
            fidc_activity = st.empty()
            fidc_status = st.empty()

            def _render_fidc_live(current_event: dict | None = None) -> None:
                events = st.session_state.fidc_activity_events
                success = st.session_state.fidc_success_count
                failed = st.session_state.fidc_failed_count
                done_n = success + failed
                total_n = max(1, len(st.session_state.fidc_cnpjs))
                pct = done_n / total_n
                elapsed = (
                    time.time() - st.session_state.fidc_start_time
                    if st.session_state.fidc_start_time
                    else 0.0
                )
                remaining = (
                    ((elapsed / done_n) * (total_n - done_n) / 60)
                    if done_n > 0
                    else None
                )
                throughput = (
                    (done_n / (elapsed / 60)) if elapsed > 0 and done_n > 0 else None
                )
                fidc_hero.markdown(
                    cota_theme.progress_hero(
                        pct=pct,
                        processed=f"{done_n} / {total_n}",
                        success=success,
                        failed=failed,
                        elapsed_min=elapsed / 60,
                        remaining_min=remaining,
                        throughput_per_min=throughput,
                    ),
                    unsafe_allow_html=True,
                )
                fidc_bar.markdown(
                    cota_theme.progress_bar_html(pct), unsafe_allow_html=True
                )
                fidc_activity.markdown(
                    cota_theme.activity_panel(events, current_event=current_event),
                    unsafe_allow_html=True,
                )

            _render_fidc_live()

        scraper = None
        results = []
        total = len(st.session_state.fidc_cnpjs)
        was_interrupted = False

        # Incremental persistence (same safety net as the regular flow): write a
        # "_partial" Excel after every CNPJ so a killed process keeps everything
        # scraped so far. Promoted to the final name in finally on clean finish.
        _fidc_run_ts = datetime.fromtimestamp(
            st.session_state.fidc_start_time or time.time()
        ).strftime("%Y%m%d_%H%M%S")
        _fidc_partial_path = RESULTS_DIR / f"fidc_results_{_fidc_run_ts}_partial.xlsx"
        _fidc_persist_processor = DataProcessor()

        def _persist_fidc_partial():
            if not results:
                return
            try:
                RESULTS_DIR.mkdir(exist_ok=True)
                _fidc_persist_processor.process_fidc_data(results).to_excel(
                    _fidc_partial_path, index=False
                )
                st.session_state.fidc_last_excel_path = str(_fidc_partial_path)
            except Exception as e:
                st.session_state.session_logger.warning(
                    f"[FIDC] Incremental save failed: {e}"
                )

        try:
            use_stealth = st.session_state.settings["stealth"]
            headless = st.session_state.settings["headless"]
            if use_stealth:
                scraper = StealthANBIMAScraper(headless=headless)
            else:
                from anbima_scraper import ANBIMAScraper

                scraper = ANBIMAScraper(headless=headless)

            if not hasattr(scraper, "scrape_fidc_data"):
                fidc_status.error(
                    "❌ The selected scraper has no FIDC support. Turn Stealth mode ON "
                    "(the FIDC workflow requires the stealth scraper)."
                )
                st.session_state.fidc_phase = "review"
                st.stop()

            if not scraper.setup_driver():
                real_error = (
                    getattr(scraper, "last_init_error", None) or "Unknown error"
                )
                real_tb = getattr(scraper, "last_init_traceback", None)
                with fidc_status.container():
                    st.error(f"❌ Failed to initialize web driver:\n\n**{real_error}**")
                    with st.expander("🔧 Technical details"):
                        st.code(real_tb or real_error, language="text")
                st.session_state.session_logger.error(
                    f"[FIDC] setup_driver failed: {real_error}"
                )
                st.stop()

            driver_mode = getattr(scraper, "driver_mode", None)
            if driver_mode:
                fidc_status.success(f"✅ WebDriver: **{driver_mode}**")

            for idx, cnpj in enumerate(st.session_state.fidc_cnpjs, 1):
                if st.session_state.fidc_stop:
                    fidc_status.warning(
                        f"⚠️ Stopped by user after {idx - 1}/{total} CNPJs"
                    )
                    was_interrupted = True
                    break

                _render_fidc_live(current_event={"cnpj": cnpj, "name": "Fetching…"})
                t0 = time.time()
                st.session_state.session_logger.info(
                    f"[FIDC {idx}/{total}] CNPJ: {cnpj}"
                )
                try:
                    result = scraper.scrape_fidc_data(cnpj)
                    results.append(result)
                    ms = int((time.time() - t0) * 1000)
                    subs = result.get("subclasses", []) or []
                    n_subs = len(subs)
                    n_rows = sum(len(s.get("periodic_data", []) or []) for s in subs)
                    if result.get("Status") == "Success" and n_rows > 0:
                        st.session_state.fidc_success_count += 1
                        st.session_state.fidc_activity_events.append(
                            {
                                "cnpj": cnpj,
                                "name": f"{n_subs} subclasse{'s' if n_subs != 1 else ''}",
                                "status": "success",
                                "points": n_rows,
                                "ms": ms,
                            }
                        )
                        st.session_state.session_logger.info(
                            f"[FIDC {idx}/{total}] SUCCESS: {cnpj} - {n_subs} subclasses, {n_rows} rows"
                        )
                    else:
                        st.session_state.fidc_failed_count += 1
                        st.session_state.fidc_activity_events.append(
                            {
                                "cnpj": cnpj,
                                "name": result.get("Status", "Failed"),
                                "status": "failed",
                                "points": 0,
                                "ms": ms,
                            }
                        )
                        st.session_state.session_logger.warning(
                            f"[FIDC {idx}/{total}] FAILED: {cnpj} - {result.get('Status')}"
                        )
                except Exception as e:
                    ms = int((time.time() - t0) * 1000)
                    err = str(e)[:50]
                    st.session_state.fidc_failed_count += 1
                    st.session_state.fidc_activity_events.append(
                        {
                            "cnpj": cnpj,
                            "name": f"Error: {err}",
                            "status": "failed",
                            "points": 0,
                            "ms": ms,
                        }
                    )
                    st.session_state.session_logger.error(
                        f"[FIDC {idx}/{total}] EXCEPTION: {cnpj} - {str(e)}"
                    )
                    results.append(
                        {"CNPJ": cnpj, "Status": f"Error: {err}", "subclasses": []}
                    )

                _persist_fidc_partial()  # incremental save — survives a killed process
                _render_fidc_live()

                if getattr(scraper, "_driver_permanently_dead", False):
                    fidc_status.error(
                        "🛑 Chrome kept dying and could not be recovered — stopping the run. "
                        "Turn the **Headless browser** toggle OFF and retry. "
                        f"Partial results up to {idx}/{total} are saved (see History)."
                    )
                    st.session_state.session_logger.error(
                        f"[FIDC] Aborting run at {idx}/{total} — driver permanently dead"
                    )
                    was_interrupted = True
                    break

        except Exception as e:
            fidc_status.error(f"❌ Error during FIDC scraping: {str(e)}")
            st.session_state.session_logger.error(f"[FIDC] Fatal: {str(e)}")
            st.session_state.session_logger.debug(traceback.format_exc())
            was_interrupted = True

        finally:
            if scraper:
                try:
                    scraper.close()
                except Exception:
                    pass

            if results:
                try:
                    processor = DataProcessor()
                    fidc_df = processor.process_fidc_data(results)
                    st.session_state.fidc_results = fidc_df
                    try:
                        interrupted = was_interrupted or st.session_state.fidc_stop
                        suffix = "_partial" if interrupted else ""
                        fidc_path = (
                            RESULTS_DIR / f"fidc_results_{_fidc_run_ts}{suffix}.xlsx"
                        )
                        fidc_df.to_excel(fidc_path, index=False)
                        st.session_state.fidc_last_excel_path = str(fidc_path)
                        # Promote the partial to final on clean completion.
                        if (
                            not interrupted
                            and _fidc_partial_path.exists()
                            and _fidc_partial_path != fidc_path
                        ):
                            try:
                                _fidc_partial_path.unlink()
                            except Exception:
                                pass
                        st.session_state.session_logger.info(
                            f"[FIDC] Excel saved to {fidc_path}"
                        )
                    except Exception as e:
                        st.session_state.session_logger.warning(
                            f"[FIDC] Could not persist Excel: {e}"
                        )
                except Exception as e:
                    fidc_status.warning(f"⚠️ Could not process FIDC results: {str(e)}")
                    st.session_state.session_logger.error(
                        f"[FIDC] Processing error: {str(e)}"
                    )

            st.session_state.fidc_phase = "done"
            if st.session_state.fidc_stop or was_interrupted:
                st.session_state.fidc_stop = False
            st.session_state.session_logger.info("FIDC SCRAPING ENDED")
            st.rerun()

    # --- Phase: DONE ---------------------------------------------------------
    elif (
        st.session_state.fidc_phase == "done"
        and st.session_state.fidc_results is not None
    ):
        fidc_df = st.session_state.fidc_results
        success = st.session_state.fidc_success_count
        failed = st.session_state.fidc_failed_count
        total_cnpjs = len(st.session_state.fidc_cnpjs)
        processed_n = success + failed
        interrupted = processed_n < total_cnpjs and total_cnpjs > 0
        n_subclasses = int(fidc_df["Código"].nunique()) if not fidc_df.empty else 0
        n_rows = len(fidc_df)
        total_time = (
            time.time() - st.session_state.fidc_start_time
            if st.session_state.fidc_start_time
            else 0
        )
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fidc_filename = f"fidc_results_{ts}.xlsx"

        fidc_buffer = io.BytesIO()
        fidc_df.to_excel(fidc_buffer, index=False)
        fidc_buffer.seek(0)

        with st.container(border=True):
            head_l, head_m, head_r = st.columns([0.7, 4, 3])
            with head_l:
                st.markdown(
                    cota_theme.success_circle(variant="warn" if interrupted else "ok"),
                    unsafe_allow_html=True,
                )
            with head_m:
                title = (
                    "FIDC scrape interrupted" if interrupted else "FIDC scrape complete"
                )
                sub = f"{n_subclasses} subclasse(s) across {processed_n} CNPJ(s) · {n_rows:,} rows"
                st.markdown(
                    f'<h2 class="cota-card-title">{title}</h2>'
                    f'<p class="cota-card-sub">{sub}</p>',
                    unsafe_allow_html=True,
                )
            with head_r:
                new_col, dl_col = st.columns([1, 1])
                with new_col:
                    if st.button(
                        "↻  New FIDC scrape", width="stretch", key="fidc_done_new"
                    ):
                        st.session_state.fidc_results = None
                        st.session_state.fidc_cnpjs = []
                        st.session_state.fidc_success_count = 0
                        st.session_state.fidc_failed_count = 0
                        st.session_state.fidc_activity_events = []
                        st.session_state.fidc_start_time = None
                        st.session_state.fidc_phase = "upload"
                        st.rerun()
                with dl_col:
                    st.download_button(
                        "⬇  Download Excel",
                        data=fidc_buffer,
                        file_name=fidc_filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        width="stretch",
                        key="fidc_done_download",
                    )

            st.markdown(
                cota_theme.kpi_row(
                    [
                        ("CNPJs processed", str(processed_n)),
                        ("Subclasses", str(n_subclasses)),
                        ("Total rows", f"{n_rows:,}"),
                        ("Failed", str(failed), "err" if failed else ""),
                    ]
                ),
                unsafe_allow_html=True,
            )

        with st.container(border=True):
            st.markdown(
                '<h2 class="cota-card-title">Results</h2>'
                f'<p class="cota-card-sub">Long/tidy preview of <code>{fidc_filename}</code></p>',
                unsafe_allow_html=True,
            )
            st.dataframe(fidc_df, width="stretch", height=420)

    st.markdown(
        cota_theme.footer(version=f"v{APP_VERSION}", build=f"build {GIT_COMMIT}"),
        unsafe_allow_html=True,
    )
    st.stop()

# --- "scrape" route: title + stepper -----------------------------------------
st.markdown(
    cota_theme.page_head(
        title="New scrape",
        sub="Upload a list of CNPJs and pull historical fund quotes from ANBIMA.",
        right_html=cota_theme.stepper(st.session_state.phase),
    ),
    unsafe_allow_html=True,
)

# --- Phase: UPLOAD -----------------------------------------------------------
if st.session_state.phase == "upload":
    with st.container(border=True):
        st.markdown(
            f'<h2 class="cota-card-title">Upload your CNPJ list</h2>'
            f'<p class="cota-card-sub">Excel file (.xlsx or .xls) with a column named '
            f"<code>CNPJ</code>. Up to 500 CNPJs per run · ~2.2 min/CNPJ.</p>",
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader(
            "Drop file here, or browse",
            type=["xlsx", "xls"],
            label_visibility="collapsed",
            help="Upload Excel file with a 'CNPJ' column",
            key="upload_xlsx",
        )

        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                if "CNPJ" in df.columns:
                    st.session_state.cnpjs = df["CNPJ"].astype(str).tolist()
                    st.session_state.uploaded_filename = uploaded_file.name
                    st.session_state.session_logger.info(
                        f"File uploaded: {uploaded_file.name}"
                    )
                    st.session_state.session_logger.info(
                        f"CNPJs loaded: {len(st.session_state.cnpjs)}"
                    )
                    st.session_state.phase = "review"
                    st.rerun()
                else:
                    st.error("Missing 'CNPJ' column in the uploaded file.")
                    st.session_state.session_logger.error(
                        f"File missing CNPJ column: {uploaded_file.name}"
                    )
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
                st.session_state.session_logger.error(f"Error reading file: {str(e)}")
                st.session_state.session_logger.debug(traceback.format_exc())

# --- Phase: REVIEW (CNPJ table + Run settings) -------------------------------
elif st.session_state.phase == "review":
    review_left, review_right = st.columns([1.4, 1])

    # Left card: searchable CNPJ table
    with review_left:
        with st.container(border=True):
            top_l, top_r = st.columns([1, 1])
            with top_l:
                st.markdown(
                    f'<h2 class="cota-card-title">Review CNPJs</h2>'
                    f'<p class="cota-card-sub">{len(st.session_state.cnpjs)} entries loaded from '
                    f"<code>{st.session_state.get('uploaded_filename', 'input.xlsx')}</code></p>",
                    unsafe_allow_html=True,
                )
            with top_r:
                if st.button("Clear", key="review_clear"):
                    st.session_state.cnpjs = []
                    st.session_state.phase = "upload"
                    st.rerun()

            query = st.text_input(
                "Filter CNPJ…",
                key="review_filter",
                placeholder="Filter CNPJ…",
                label_visibility="collapsed",
            )
            st.markdown(
                cota_theme.cnpj_table(st.session_state.cnpjs, query=query),
                unsafe_allow_html=True,
            )

    # Right card: Run settings + Start scraping
    with review_right:
        with st.container(border=True):
            st.markdown(
                f'<h2 class="cota-card-title">Run settings</h2>'
                f'<p class="cota-card-sub">Tune anti-bot behaviour and parallelism.</p>',
                unsafe_allow_html=True,
            )

            # Stealth toggle
            st.markdown(
                cota_theme.setting_text(
                    "Stealth mode",
                    "Use undetected ChromeDriver to evade bot detection.",
                ),
                unsafe_allow_html=True,
            )
            st.session_state.settings["stealth"] = st.toggle(
                "Stealth mode",
                value=st.session_state.settings["stealth"],
                key="setting_stealth",
                label_visibility="collapsed",
            )

            # Headless toggle (locked on cloud)
            st.markdown(
                cota_theme.setting_text(
                    "Headless browser",
                    "Faster, but more likely to trip anti-bot detection. Required on Streamlit Cloud.",
                ),
                unsafe_allow_html=True,
            )
            st.session_state.settings["headless"] = st.toggle(
                "Headless browser",
                value=(True if is_cloud else st.session_state.settings["headless"]),
                key="setting_headless",
                label_visibility="collapsed",
                disabled=is_cloud,
            )

            # Parallel workers (segmented)
            workers_help = (
                "Sequential — most stable."
                if st.session_state.settings["workers"] == 1
                else f"{st.session_state.settings['workers']}× faster, slightly higher detection risk."
            )
            st.markdown(
                cota_theme.setting_text("Parallel workers", workers_help),
                unsafe_allow_html=True,
            )
            workers_idx = (
                [1, 2, 4].index(st.session_state.settings["workers"])
                if st.session_state.settings["workers"] in (1, 2, 4)
                else 0
            )
            st.session_state.settings["workers"] = st.radio(
                "Parallel workers",
                options=[1, 2, 4],
                index=workers_idx,
                key="setting_workers",
                horizontal=True,
                label_visibility="collapsed",
            )

            # Polite delay slider
            st.markdown(
                cota_theme.setting_text(
                    "Polite delay", "Randomised pause between requests, in seconds."
                ),
                unsafe_allow_html=True,
            )
            st.session_state.settings["delay"] = st.slider(
                "Polite delay",
                0.5,
                5.0,
                st.session_state.settings["delay"],
                0.5,
                key="setting_delay",
                label_visibility="collapsed",
            )

            # Run summary
            est_min = (len(st.session_state.cnpjs) * 2.2) / max(
                1, st.session_state.settings["workers"]
            )
            throughput = round((60 / 2.2) * st.session_state.settings["workers"])
            risk = (
                "Elevated"
                if (
                    st.session_state.settings["headless"]
                    and st.session_state.settings["workers"] > 2
                )
                else "Low"
            )
            risk_class = "cota-tag-warn" if risk == "Elevated" else "cota-tag-ok"
            st.markdown(
                cota_theme.run_summary(
                    [
                        ("Estimated duration", f"{est_min:.0f} min"),
                        ("Throughput", f"~{throughput} CNPJ/h"),
                        (
                            "Risk profile",
                            f'<span class="cota-tag {risk_class}">{risk}</span>',
                        ),
                    ]
                ),
                unsafe_allow_html=True,
            )

            # Start Scraping
            if st.button(
                "▶  Start scraping", type="primary", width="stretch", key="review_start"
            ):
                # Kill any orphan Chrome processes from a previous run before starting,
                # otherwise we risk tripping the Streamlit Cloud ~1 GB RAM ceiling.
                kill_orphan_chrome()

                # Refresh local aliases from the (possibly just-edited) settings.
                use_stealth = st.session_state.settings["stealth"]
                headless = st.session_state.settings["headless"]
                num_workers = st.session_state.settings["workers"]

                st.session_state.scraping_in_progress = True
                st.session_state.stop_scraping = False
                st.session_state.progress = 0
                st.session_state.success_count = 0
                st.session_state.failed_count = 0
                st.session_state.status_messages = []
                st.session_state.activity_events = []
                st.session_state.start_time = time.time()
                st.session_state.phase = "scrape"

                # Log scraping start
                st.session_state.session_logger.info("=" * 80)
                st.session_state.session_logger.info("SCRAPING STARTED")
                st.session_state.session_logger.info(
                    f"Total CNPJs: {len(st.session_state.cnpjs)}"
                )
                st.session_state.session_logger.info(f"Stealth Mode: {use_stealth}")
                st.session_state.session_logger.info(f"Headless Mode: {headless}")
                st.session_state.session_logger.info(f"Workers: {num_workers}")
                st.session_state.session_logger.info(
                    f"Polite delay: {st.session_state.settings['delay']}s"
                )
                st.session_state.session_logger.info(
                    f"Start Time: {datetime.now().isoformat()}"
                )
                st.session_state.session_logger.info("=" * 80)

                st.rerun()

# --- Phase: SCRAPE -----------------------------------------------------------
if st.session_state.phase == "scrape":
    # Header card: title + run summary line + Stop button
    with st.container(border=True):
        head_l, head_r = st.columns([4, 1])
        with head_l:
            settings_str = (
                f"{'Stealth driver' if use_stealth else 'Standard driver'} · "
                f"{num_workers} worker{'s' if num_workers > 1 else ''} · "
                f"{st.session_state.settings['delay']:.1f}s delay"
            )
            st.markdown(
                '<h2 class="cota-card-title">Scraping in progress</h2>'
                f'<p class="cota-card-sub">{settings_str}</p>',
                unsafe_allow_html=True,
            )
        with head_r:
            if st.button(
                "⬛  Stop", type="secondary", width="stretch", key="scrape_stop"
            ):
                st.session_state.stop_scraping = True

        # Live regions — written to from inside the loop via .markdown(...).
        hero_slot = st.empty()
        bar_slot = st.empty()
        activity_slot = st.empty()
        status_slot = st.empty()  # for inline success/error banners

        def _render_live(current_event: dict | None = None) -> None:
            """Re-render the three live regions from current session state."""
            events = st.session_state.activity_events
            success = st.session_state.success_count
            failed = st.session_state.failed_count
            done_n = success + failed
            total_n = max(1, len(st.session_state.cnpjs))
            pct = done_n / total_n
            elapsed = (
                time.time() - st.session_state.start_time
                if st.session_state.start_time
                else 0.0
            )
            remaining = (
                ((elapsed / done_n) * (total_n - done_n) / 60) if done_n > 0 else None
            )
            throughput = (
                (done_n / (elapsed / 60)) if elapsed > 0 and done_n > 0 else None
            )
            hero_slot.markdown(
                cota_theme.progress_hero(
                    pct=pct,
                    processed=f"{done_n} / {total_n}",
                    success=success,
                    failed=failed,
                    elapsed_min=elapsed / 60,
                    remaining_min=remaining,
                    throughput_per_min=throughput,
                ),
                unsafe_allow_html=True,
            )
            bar_slot.markdown(cota_theme.progress_bar_html(pct), unsafe_allow_html=True)
            activity_slot.markdown(
                cota_theme.activity_panel(events, current_event=current_event),
                unsafe_allow_html=True,
            )

        # Show empty live regions while the driver is booting.
        _render_live()

    # ─── Run scraping ─────────────────────────────────────────────────────
    scraper = None
    results = []
    total = len(st.session_state.cnpjs)
    was_interrupted = False

    # Incremental persistence: write a "_partial" Excel after every CNPJ so a
    # killed process (OOM, headless-Chrome recovery storm, tab disconnect)
    # never loses what was already scraped. The finally block promotes it to
    # the final filename on clean completion.
    _run_ts = datetime.fromtimestamp(
        st.session_state.start_time or time.time()
    ).strftime("%Y%m%d_%H%M%S")
    _partial_path = RESULTS_DIR / f"anbima_results_{_run_ts}_partial.xlsx"
    _persist_processor = DataProcessor()

    def _persist_partial():
        """Overwrite the partial Excel with everything collected so far."""
        if not results:
            return
        try:
            RESULTS_DIR.mkdir(exist_ok=True)
            _persist_processor.process_scraped_data(results).to_excel(
                _partial_path, index=False
            )
            st.session_state.last_excel_path = str(_partial_path)
        except Exception as e:
            st.session_state.session_logger.warning(f"Incremental save failed: {e}")

    try:
        # Initialize scraper
        if use_stealth:
            scraper = StealthANBIMAScraper(headless=headless)
        else:
            from anbima_scraper import ANBIMAScraper

            scraper = ANBIMAScraper(headless=headless)

        if not scraper.setup_driver():
            # Surface the underlying driver error directly in the status slot.
            real_error = getattr(scraper, "last_init_error", None) or "Unknown error"
            real_tb = getattr(scraper, "last_init_traceback", None)
            with status_slot.container():
                st.error(f"❌ Failed to initialize web driver:\n\n**{real_error}**")
                with st.expander(
                    "🔧 Technical details (share this with the developer)"
                ):
                    st.code(real_tb or real_error, language="text")
                    st.caption(
                        "Common causes: Streamlit Cloud Chrome version mismatch, "
                        "out-of-memory kill from a previous run (try the "
                        "'Kill Orphan Chrome' button in the sidebar), or the app "
                        "needs a hard reboot from the Streamlit Cloud dashboard."
                    )
            st.session_state.session_logger.error(f"setup_driver failed: {real_error}")
            if real_tb:
                st.session_state.session_logger.debug(real_tb)
            st.session_state.scraping_in_progress = False
            st.stop()

        # Surface the driver strategy that won (UC vs plain Selenium).
        driver_mode = getattr(scraper, "driver_mode", None)
        if driver_mode:
            if "plain Selenium" in driver_mode:
                status_slot.info(
                    f"ℹ️ WebDriver: **{driver_mode}** (UC unavailable — stealth level reduced)"
                )
            else:
                status_slot.success(f"✅ WebDriver: **{driver_mode}**")
        st.session_state.session_logger.info(
            f"WebDriver initialized successfully via: {driver_mode}"
        )

        for idx, cnpj in enumerate(st.session_state.cnpjs, 1):
            # Check if user requested stop
            if st.session_state.stop_scraping:
                st.session_state.session_logger.info(
                    f"Scraping stopped by user at CNPJ {idx}/{total}"
                )
                status_slot.warning(
                    f"⚠️ Scraping stopped by user after {idx - 1}/{total} CNPJs"
                )
                was_interrupted = True
                break

            # Show shimmering "Fetching…" row for the in-flight CNPJ.
            _render_live(current_event={"cnpj": cnpj, "name": "Fetching…"})

            cnpj_start_time = time.time()
            st.session_state.session_logger.info(
                f"[{idx}/{total}] Starting CNPJ: {cnpj}"
            )

            try:
                result = scraper.scrape_fund_data(cnpj)
                results.append(result)
                cnpj_elapsed = time.time() - cnpj_start_time
                cnpj_ms = int(cnpj_elapsed * 1000)
                fund_name = str(result.get("Nome do Fundo") or "—")

                if result.get("Status") == "Success":
                    data_points = len(result.get("periodic_data", []))
                    st.session_state.success_count += 1
                    st.session_state.activity_events.append(
                        {
                            "cnpj": cnpj,
                            "name": fund_name,
                            "status": "success",
                            "points": data_points,
                            "ms": cnpj_ms,
                        }
                    )
                    st.session_state.status_messages.append(
                        f"✅ {cnpj} - Success ({data_points} data points)"
                    )
                    st.session_state.session_logger.info(
                        f"[{idx}/{total}] SUCCESS: {cnpj} - {data_points} data points - {cnpj_elapsed:.1f}s"
                    )
                else:
                    status = result.get("Status", "Failed")
                    st.session_state.failed_count += 1
                    st.session_state.activity_events.append(
                        {
                            "cnpj": cnpj,
                            "name": fund_name,
                            "status": "failed",
                            "points": 0,
                            "ms": cnpj_ms,
                        }
                    )
                    st.session_state.status_messages.append(f"❌ {cnpj} - {status}")
                    st.session_state.session_logger.warning(
                        f"[{idx}/{total}] FAILED: {cnpj} - Status: {status} - {cnpj_elapsed:.1f}s"
                    )

            except Exception as e:
                cnpj_elapsed = time.time() - cnpj_start_time
                cnpj_ms = int(cnpj_elapsed * 1000)
                error_short = str(e)[:50]
                st.session_state.failed_count += 1
                st.session_state.activity_events.append(
                    {
                        "cnpj": cnpj,
                        "name": f"Error: {error_short}",
                        "status": "failed",
                        "points": 0,
                        "ms": cnpj_ms,
                    }
                )
                st.session_state.status_messages.append(
                    f"❌ {cnpj} - Error: {error_short}"
                )
                st.session_state.session_logger.error(
                    f"[{idx}/{total}] EXCEPTION: {cnpj} - {str(e)} - {cnpj_elapsed:.1f}s"
                )
                st.session_state.session_logger.debug(
                    f"Traceback:\n{traceback.format_exc()}"
                )
                results.append(
                    {
                        "CNPJ": cnpj,
                        "Nome do Fundo": "N/A",
                        "periodic_data": [],
                        "Status": f"Error: {error_short}",
                    }
                )

            # Update progress + re-render the live regions for this completed item.
            st.session_state.progress = idx / total
            _persist_partial()  # incremental save — survives a killed process
            _render_live()

            # Circuit breaker tripped: Chrome won't stay alive. Stop now instead
            # of iterating the rest of the list as instant failures.
            if getattr(scraper, "_driver_permanently_dead", False):
                status_slot.error(
                    "🛑 Chrome kept dying and could not be recovered — stopping the run. "
                    "Turn the **Headless browser** toggle OFF (Review screen) and retry. "
                    f"Partial results up to {idx}/{total} are saved (see History)."
                )
                st.session_state.session_logger.error(
                    f"Aborting run at {idx}/{total} — driver permanently dead"
                )
                was_interrupted = True
                break

    except Exception as e:
        error_msg = f"Error during scraping: {str(e)}"
        status_slot.error(f"❌ {error_msg}")
        st.session_state.session_logger.error(error_msg)
        st.session_state.session_logger.debug(
            f"Full traceback:\n{traceback.format_exc()}"
        )
        was_interrupted = True

    finally:
        # Always close the scraper, even if there was an error
        if scraper:
            try:
                scraper.close()
                st.session_state.session_logger.info("WebDriver closed successfully")
            except Exception as e:
                warning_msg = f"Could not close scraper properly - {str(e)}"
                status_slot.warning(f"⚠️ Warning: {warning_msg}")
                st.session_state.session_logger.warning(warning_msg)

        # Process results (even if some failed or scraping was interrupted)
        if results:
            try:
                st.session_state.session_logger.info(
                    f"Processing {len(results)} results..."
                )
                processor = DataProcessor()
                output_df = processor.process_scraped_data(results)
                st.session_state.results = output_df
                st.session_state.session_logger.info(
                    f"Results processed successfully - {len(output_df)} rows"
                )

                # Persist the final Excel. An incremental "_partial" file has
                # been written after every CNPJ; here we promote it to the
                # final name on clean completion (and remove the partial), or
                # keep the "_partial" file if the run was interrupted.
                try:
                    interrupted = was_interrupted or st.session_state.stop_scraping
                    suffix = "_partial" if interrupted else ""
                    excel_path = RESULTS_DIR / f"anbima_results_{_run_ts}{suffix}.xlsx"
                    output_df.to_excel(excel_path, index=False)
                    st.session_state.last_excel_path = str(excel_path)
                    # On clean completion, drop the now-redundant partial file.
                    if (
                        not interrupted
                        and _partial_path.exists()
                        and _partial_path != excel_path
                    ):
                        try:
                            _partial_path.unlink()
                        except Exception:
                            pass
                    st.session_state.session_logger.info(f"Excel saved to {excel_path}")
                except Exception as e:
                    st.session_state.session_logger.warning(
                        f"Could not persist Excel to disk: {e}"
                    )
            except Exception as e:
                status_slot.warning(
                    f"⚠️ Warning: Could not process all results - {str(e)}"
                )
                st.session_state.session_logger.error(
                    f"Error processing results: {str(e)}"
                )
                st.session_state.session_logger.debug(traceback.format_exc())

        # Final stats
        total_time = (
            time.time() - st.session_state.start_time
            if st.session_state.start_time
            else 0
        )

        # Mark complete and advance to the Cota "done" phase so the next
        # render shows the results screen. The post-scrape banner lives on
        # the done screen (phase 4).
        st.session_state.scraping_in_progress = False
        st.session_state.phase = "done"
        if st.session_state.stop_scraping or was_interrupted:
            st.session_state.stop_scraping = False

        # Log completion
        st.session_state.session_logger.info("=" * 80)
        st.session_state.session_logger.info("SCRAPING ENDED")
        st.session_state.session_logger.info(f"Total CNPJs requested: {total}")
        st.session_state.session_logger.info(f"CNPJs processed: {len(results)}")
        st.session_state.session_logger.info(
            f"Successful: {st.session_state.success_count}"
        )
        st.session_state.session_logger.info(f"Failed: {st.session_state.failed_count}")
        st.session_state.session_logger.info(
            f"Total Time: {total_time / 60:.2f} minutes"
        )
        if len(results) > 0:
            st.session_state.session_logger.info(
                f"Avg Time per CNPJ: {total_time / len(results):.1f} seconds"
            )
        st.session_state.session_logger.info("=" * 80)

        st.rerun()

# Results section
if st.session_state.phase == "done" and st.session_state.results is not None:
    # ---- aggregates ---------------------------------------------------------
    events = st.session_state.activity_events
    success = st.session_state.success_count
    failed = st.session_state.failed_count
    total_cnpjs = len(st.session_state.cnpjs)
    processed_n = success + failed
    interrupted = processed_n < total_cnpjs and total_cnpjs > 0
    success_rate = (success / total_cnpjs * 100) if total_cnpjs else 0
    total_points = sum(
        int(e.get("points") or 0) for e in events if e.get("status") == "success"
    )
    total_time = (
        time.time() - st.session_state.start_time if st.session_state.start_time else 0
    )
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"anbima_results_{timestamp}.xlsx"

    # ---- prepare Excel buffer once -----------------------------------------
    output_buffer = io.BytesIO()
    st.session_state.results.to_excel(output_buffer, index=False)
    output_buffer.seek(0)

    # ---- Card 1: Summary ---------------------------------------------------
    with st.container(border=True):
        head_l, head_m, head_r = st.columns([0.7, 4, 3])
        with head_l:
            st.markdown(
                cota_theme.success_circle(variant="warn" if interrupted else "ok"),
                unsafe_allow_html=True,
            )
        with head_m:
            if interrupted:
                title = "Scraping interrupted"
                sub = (
                    f"{processed_n} of {total_cnpjs} CNPJs processed · "
                    f"{total_points:,} data points · partial results saved"
                )
            else:
                title = "Scraping complete"
                sub = f"{success} of {total_cnpjs} funds extracted · {total_points:,} data points"
            st.markdown(
                f'<h2 class="cota-card-title">{title}</h2>'
                f'<p class="cota-card-sub">{sub}</p>',
                unsafe_allow_html=True,
            )
        with head_r:
            new_col, dl_col = st.columns([1, 1])
            with new_col:
                if st.button("↻  New scrape", width="stretch", key="done_new"):
                    st.session_state.results = None
                    st.session_state.cnpjs = []
                    st.session_state.success_count = 0
                    st.session_state.failed_count = 0
                    st.session_state.status_messages = []
                    st.session_state.activity_events = []
                    st.session_state.start_time = None
                    st.session_state.phase = "upload"
                    st.rerun()
            with dl_col:
                st.download_button(
                    "⬇  Download Excel",
                    data=output_buffer,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    width="stretch",
                    key="done_download_excel",
                )

        # KPI row
        st.markdown(
            cota_theme.kpi_row(
                [
                    ("Success rate", f"{success_rate:.1f}%"),
                    ("Funds processed", str(total_cnpjs)),
                    ("Data points", f"{total_points:,}"),
                    ("Failed", str(failed), "err" if failed else ""),
                ]
            ),
            unsafe_allow_html=True,
        )

    # ---- Card 2: Results table --------------------------------------------
    with st.container(border=True):
        rt_l, rt_r = st.columns([1.6, 1])
        with rt_l:
            st.markdown(
                '<h2 class="cota-card-title">Results</h2>'
                f'<p class="cota-card-sub">Preview of <code>{filename}</code></p>',
                unsafe_allow_html=True,
            )
        with rt_r:
            # Tabs (filter by status). segmented_control is available in
            # Streamlit 1.45+; falls back to a horizontal radio on older versions.
            tab_options = [
                f"All ({len(events)})",
                f"Success ({success})",
                f"Failed ({failed})",
            ]
            if hasattr(st, "segmented_control"):
                picked = (
                    st.segmented_control(
                        "Filter results",
                        options=tab_options,
                        default=tab_options[0],
                        key="results_tab_seg",
                        label_visibility="collapsed",
                    )
                    or tab_options[0]
                )
            else:
                picked = st.radio(
                    "Filter results",
                    options=tab_options,
                    horizontal=True,
                    label_visibility="collapsed",
                    key="results_tab_radio",
                )
            # Map back to the simple filter key
            if picked.startswith("Success"):
                filter_by = "Success"
            elif picked.startswith("Failed"):
                filter_by = "Failed"
            else:
                filter_by = "All"

        st.markdown(
            cota_theme.result_table(events, filter_by=filter_by),
            unsafe_allow_html=True,
        )

        # Download log + size info row
        size_col, log_col, info_col = st.columns([1, 1, 2])
        with size_col:
            excel_kb = len(output_buffer.getvalue()) / 1024
            st.markdown(
                f'<div class="cota-muted" style="font-size:12px;padding-top:8px;">'
                f'Excel: <span class="cota-mono">{excel_kb:.1f} KB</span>'
                f"</div>",
                unsafe_allow_html=True,
            )
        with log_col:
            if st.session_state.log_file.exists():
                log_content = st.session_state.log_file.read_text(encoding="utf-8")
                log_kb = st.session_state.log_file.stat().st_size / 1024
                st.download_button(
                    f"📋  Download log ({log_kb:.1f} KB)",
                    data=log_content,
                    file_name=st.session_state.log_file.name,
                    mime="text/plain",
                    width="stretch",
                    key="done_download_log",
                )
        with info_col:
            elapsed_str = f"{total_time / 60:.1f} min" if total_time else "—"
            avg_str = f"{(total_time / processed_n):.1f}s/CNPJ" if processed_n else "—"
            st.markdown(
                f'<div class="cota-muted" style="font-size:12px;padding-top:8px;text-align:right;">'
                f'Total time: <span class="cota-mono">{elapsed_str}</span> · '
                f'Avg: <span class="cota-mono">{avg_str}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )

# Cota footer
st.markdown(
    cota_theme.footer(version=f"v{APP_VERSION}", build=f"build {GIT_COMMIT}"),
    unsafe_allow_html=True,
)
