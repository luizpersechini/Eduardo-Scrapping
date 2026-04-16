"""
ANBIMA Fund Data Scraper - Web UI
Simple web interface for scraping ANBIMA fund data
"""

import os
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
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger, log_file

# Initialize session logger if not already done
if 'session_logger' not in st.session_state:
    st.session_state.session_logger, st.session_state.log_file = setup_session_logger()
    st.session_state.session_logger.info("="*80)
    st.session_state.session_logger.info("NEW SCRAPING SESSION STARTED")
    st.session_state.session_logger.info(f"Version: {APP_VERSION if 'APP_VERSION' in dir() else 'Unknown'}")
    st.session_state.session_logger.info(f"Timestamp: {datetime.now().isoformat()}")
    st.session_state.session_logger.info("="*80)

# Version info
def get_version_info():
    """Get version and git commit info"""
    try:
        # Read version from VERSION file
        version_file = Path(__file__).parent / "VERSION"
        version = version_file.read_text().strip() if version_file.exists() else "Unknown"

        # Try to get git commit hash
        try:
            commit = subprocess.check_output(
                ['git', 'rev-parse', '--short', 'HEAD'],
                cwd=Path(__file__).parent,
                stderr=subprocess.DEVNULL
            ).decode('utf-8').strip()
        except:
            commit = "N/A"

        return version, commit
    except:
        return "Unknown", "N/A"

APP_VERSION, GIT_COMMIT = get_version_info()

# Configure page
st.set_page_config(
    page_title="ANBIMA Fund Data Scraper",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Login credentials (hashed password)
USERNAME = "eduardo"
PASSWORD_HASH = "66d2bed9c29bd80dbbd578f6219a1b9003383e047955e0ba445498ac62e6a796"  # Secure random password

def check_password(password):
    """Check if password matches the stored hash"""
    return hashlib.sha256(password.encode()).hexdigest() == PASSWORD_HASH

def login_page():
    """Display login page"""
    st.title("🔐 ANBIMA Fund Data Scraper")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.subheader("Login")

        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", type="primary", width='stretch'):
            if username == USERNAME and check_password(password):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

        st.markdown("---")
        st.caption("🔒 Secure access to ANBIMA scraper")

# Check authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Show login page if not authenticated
if not st.session_state.authenticated:
    login_page()
    st.stop()

# Initialize session state
if 'scraping_in_progress' not in st.session_state:
    st.session_state.scraping_in_progress = False
if 'progress' not in st.session_state:
    st.session_state.progress = 0
if 'results' not in st.session_state:
    st.session_state.results = None
if 'cnpjs' not in st.session_state:
    st.session_state.cnpjs = []
if 'status_messages' not in st.session_state:
    st.session_state.status_messages = []
if 'success_count' not in st.session_state:
    st.session_state.success_count = 0
if 'failed_count' not in st.session_state:
    st.session_state.failed_count = 0
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'stop_scraping' not in st.session_state:
    st.session_state.stop_scraping = False


def kill_orphan_chrome():
    """Force-kill any lingering chrome/chromedriver processes.

    Orphan Chrome processes from a previous session are the #1 cause of
    Streamlit Cloud's "Argh. This app has gone over its resource limits"
    message — each instance holds ~500-700 MB of RAM and the container
    ceiling is ~1 GB. We run this on session init and before every new
    scraping run.
    """
    import platform
    if platform.system() != 'Linux':
        return
    try:
        for proc_name in ('chromedriver', 'chrome', 'chromium'):
            subprocess.call(
                ['pkill', '-9', '-f', proc_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except Exception:
        pass


# Clean up any orphan Chrome processes left over from a previous (possibly
# crashed) session. This runs once per new Streamlit session.
if 'orphan_cleanup_done' not in st.session_state:
    kill_orphan_chrome()
    st.session_state.orphan_cleanup_done = True

# Header
col_title, col_version = st.columns([4, 1])
with col_title:
    st.title("🏦 ANBIMA Fund Data Scraper")
with col_version:
    st.markdown(f"<div style='text-align: right; padding-top: 20px;'><code>v{APP_VERSION}</code></div>", unsafe_allow_html=True)
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")

    use_stealth = st.checkbox("Stealth Mode", value=True,
                              help="Use undetected ChromeDriver to avoid bot detection (Recommended)")

    # On Streamlit Cloud there is no display, so headless must be enabled
    is_cloud = os.environ.get("STREAMLIT_SHARING_MODE") or os.environ.get("IS_STREAMLIT_CLOUD")
    headless = st.checkbox("Headless Mode", value=True,
                          help="Run browser without GUI. Automatically enabled on Streamlit Cloud.",
                          disabled=bool(is_cloud))

    if is_cloud:
        st.info("ℹ️ Headless mode is required on Streamlit Cloud and has been enabled automatically.")
    elif headless:
        st.warning("⚠️ Headless mode may trigger anti-bot detection. If scraping fails repeatedly, disable headless mode.")

    num_workers = st.selectbox("Workers", options=[1, 2], index=0,
                               help="Number of parallel workers (1 recommended for stability)")

    st.markdown("---")
    st.header("📖 About")
    st.markdown("""
    This tool scrapes fund data from ANBIMA website.

    **Features:**
    - ✅ Anti-spam protection
    - ✅ Real-time progress tracking
    - ✅ Stealth mode enabled
    - ✅ Excel import/export
    """)

    st.markdown("---")

    # Session log viewer
    st.header("📋 Session Log")
    if st.session_state.log_file.exists():
        log_size = st.session_state.log_file.stat().st_size / 1024
        st.caption(f"Log file: {log_size:.1f} KB")

        with st.expander("View Recent Logs", expanded=False):
            try:
                # Read last 50 lines of log
                log_content = st.session_state.log_file.read_text(encoding='utf-8')
                log_lines = log_content.split('\n')
                recent_logs = '\n'.join(log_lines[-50:])
                st.text_area("Recent Activity", recent_logs, height=300, disabled=True)
            except Exception as e:
                st.error(f"Could not read log: {str(e)}")

        if st.button("📥 Download Session Log", width='stretch'):
            log_content = st.session_state.log_file.read_text(encoding='utf-8')
            st.download_button(
                label="Save Log File",
                data=log_content,
                file_name=st.session_state.log_file.name,
                mime="text/plain",
                width='stretch'
            )

    st.markdown("---")

    # Recovery: kill any orphan Chrome processes leaking RAM.
    # Use this if the app feels sluggish or scraping refuses to start.
    if st.button("🧹 Kill Orphan Chrome", width='stretch',
                 help="Force-kill any stuck Chrome/chromedriver processes from previous runs. Use if the app is slow or scraping fails to start."):
        kill_orphan_chrome()
        st.success("Chrome processes cleaned up.")

    # Logout button
    if st.button("🚪 Logout", width='stretch'):
        st.session_state.authenticated = False
        st.rerun()

    st.markdown("---")

    # Version info
    st.caption("Phase 1 & 2 Anti-spam Active")
    st.caption(f"Version: {APP_VERSION}")
    if GIT_COMMIT != "N/A":
        st.caption(f"Build: {GIT_COMMIT}")

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📤 Step 1: Upload CNPJ List")

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose an Excel file",
        type=['xlsx', 'xls'],
        help="Upload Excel file with 'CNPJ' column"
    )

    st.info("💡 **File format:** Excel file (.xlsx or .xls) with a column named 'CNPJ' containing the business tax IDs to scrape.")

with col2:
    st.header("📊 Quick Stats")
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            if 'CNPJ' in df.columns:
                st.session_state.cnpjs = df['CNPJ'].tolist()
                st.metric("CNPJs Loaded", len(st.session_state.cnpjs))
                st.success("✅ File validated")
                st.session_state.session_logger.info(f"File uploaded: {uploaded_file.name}")
                st.session_state.session_logger.info(f"CNPJs loaded: {len(st.session_state.cnpjs)}")
                st.session_state.session_logger.debug(f"CNPJ list: {st.session_state.cnpjs}")
            else:
                st.error("❌ Missing 'CNPJ' column")
                st.session_state.cnpjs = []
                st.session_state.session_logger.error(f"File missing CNPJ column: {uploaded_file.name}")
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            st.session_state.cnpjs = []
            st.session_state.session_logger.error(f"Error reading file: {str(e)}")
            st.session_state.session_logger.debug(traceback.format_exc())
    else:
        st.info("Upload file to see stats")

# Preview CNPJs
if st.session_state.cnpjs:
    st.markdown("---")
    st.header("📋 Preview CNPJs")

    preview_df = pd.DataFrame({
        'CNPJ': st.session_state.cnpjs,
        'Status': ['✓ Ready'] * len(st.session_state.cnpjs)
    })

    # Show first 10 CNPJs
    with st.expander(f"View {len(st.session_state.cnpjs)} CNPJs", expanded=False):
        st.dataframe(preview_df, width='stretch')

# Scraping controls
if st.session_state.cnpjs and not st.session_state.scraping_in_progress:
    st.markdown("---")
    st.header("🚀 Step 2: Start Scraping")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if st.button("🚀 Start Scraping", type="primary", width='stretch'):
            # Kill any orphan Chrome processes from a previous run before starting,
            # otherwise we risk tripping the Streamlit Cloud ~1 GB RAM ceiling.
            kill_orphan_chrome()

            st.session_state.scraping_in_progress = True
            st.session_state.stop_scraping = False
            st.session_state.progress = 0
            st.session_state.success_count = 0
            st.session_state.failed_count = 0
            st.session_state.status_messages = []
            st.session_state.start_time = time.time()

            # Log scraping start
            st.session_state.session_logger.info("="*80)
            st.session_state.session_logger.info("SCRAPING STARTED")
            st.session_state.session_logger.info(f"Total CNPJs: {len(st.session_state.cnpjs)}")
            st.session_state.session_logger.info(f"Stealth Mode: {use_stealth}")
            st.session_state.session_logger.info(f"Headless Mode: {headless}")
            st.session_state.session_logger.info(f"Start Time: {datetime.now().isoformat()}")
            st.session_state.session_logger.info("="*80)

            st.rerun()

    with col2:
        est_time = len(st.session_state.cnpjs) * 2.2  # 2.2 min per CNPJ
        st.metric("Estimated Time", f"{est_time:.0f} min")

    with col3:
        st.metric("Mode", "Stealth ✓" if use_stealth else "Standard")

# Scraping progress
if st.session_state.scraping_in_progress:
    st.markdown("---")
    st.header("📊 Scraping Progress")

    # Stop button
    if st.button("🛑 Stop Scraping", type="secondary", width='stretch'):
        st.session_state.stop_scraping = True

    # Progress bar
    progress_bar = st.progress(st.session_state.progress)

    # Status metrics - create empty containers
    col1, col2, col3, col4 = st.columns(4)

    # Current status
    status_container = st.container()

    # Activity log
    with st.expander("📜 Activity Log", expanded=True):
        log_placeholder = st.empty()

    # Run scraping
    scraper = None
    results = []
    total = len(st.session_state.cnpjs)
    was_interrupted = False
    try:
        # Initialize scraper
        if use_stealth:
            scraper = StealthANBIMAScraper(headless=headless)
        else:
            from anbima_scraper import ANBIMAScraper
            scraper = ANBIMAScraper(headless=headless)

        if not scraper.setup_driver():
            # Surface the *actual* underlying error so we can diagnose remotely
            # instead of just showing a generic "Failed to initialize web driver".
            real_error = getattr(scraper, 'last_init_error', None) or 'Unknown error'
            real_tb = getattr(scraper, 'last_init_traceback', None)
            st.error(f"❌ Failed to initialize web driver:\n\n**{real_error}**")
            with st.expander("🔧 Technical details (share this with the developer)"):
                st.code(real_tb or real_error, language='text')
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

        st.session_state.session_logger.info("WebDriver initialized successfully")

        for idx, cnpj in enumerate(st.session_state.cnpjs, 1):
            # Check if user requested stop
            if st.session_state.stop_scraping:
                st.session_state.session_logger.info(f"Scraping stopped by user at CNPJ {idx}/{total}")
                with status_container:
                    st.warning(f"⚠️ Scraping stopped by user after {idx - 1}/{total} CNPJs")
                was_interrupted = True
                break

            cnpj_start_time = time.time()
            st.session_state.session_logger.info(f"[{idx}/{total}] Starting CNPJ: {cnpj}")

            try:
                # Update status
                with status_container:
                    st.info(f"🔄 Scraping: {cnpj} ({idx}/{total})")

                # Scrape with timeout protection
                result = scraper.scrape_fund_data(cnpj)
                results.append(result)

                cnpj_elapsed = time.time() - cnpj_start_time

                # Update counters
                if result.get('Status') == 'Success':
                    st.session_state.success_count += 1
                    data_points = len(result.get('periodic_data', []))
                    message = f"✅ {cnpj} - Success ({data_points} data points)"
                    st.session_state.status_messages.append(message)
                    st.session_state.session_logger.info(f"[{idx}/{total}] SUCCESS: {cnpj} - {data_points} data points - {cnpj_elapsed:.1f}s")
                else:
                    st.session_state.failed_count += 1
                    status = result.get('Status', 'Failed')
                    message = f"❌ {cnpj} - {status}"
                    st.session_state.status_messages.append(message)
                    st.session_state.session_logger.warning(f"[{idx}/{total}] FAILED: {cnpj} - Status: {status} - {cnpj_elapsed:.1f}s")

            except Exception as e:
                cnpj_elapsed = time.time() - cnpj_start_time
                # Handle individual CNPJ failures
                st.session_state.failed_count += 1
                error_short = str(e)[:50]
                message = f"❌ {cnpj} - Error: {error_short}"
                st.session_state.status_messages.append(message)

                # Log full error details
                st.session_state.session_logger.error(f"[{idx}/{total}] EXCEPTION: {cnpj} - {str(e)} - {cnpj_elapsed:.1f}s")
                st.session_state.session_logger.debug(f"Traceback:\n{traceback.format_exc()}")

                results.append({
                    "CNPJ": cnpj,
                    "Nome do Fundo": "N/A",
                    "periodic_data": [],
                    "Status": f"Error: {error_short}"
                })

            # Update progress (even if CNPJ failed)
            st.session_state.progress = idx / total
            progress_bar.progress(st.session_state.progress)

            # Update metrics in their containers
            with col1:
                st.metric("Progress", f"{st.session_state.progress:.0%}")
            with col2:
                st.metric("Success", st.session_state.success_count)
            with col3:
                st.metric("Failed", st.session_state.failed_count)
            with col4:
                if st.session_state.start_time:
                    elapsed = time.time() - st.session_state.start_time
                    st.metric("Time Elapsed", f"{elapsed/60:.1f} min")

            # Update activity log
            with log_placeholder.container():
                # Show last 10 messages only
                for msg in st.session_state.status_messages[-10:]:
                    st.text(msg)

    except Exception as e:
        error_msg = f"Error during scraping: {str(e)}"
        st.error(f"❌ {error_msg}")
        st.session_state.session_logger.error(error_msg)
        st.session_state.session_logger.debug(f"Full traceback:\n{traceback.format_exc()}")
        was_interrupted = True

    finally:
        # Always close the scraper, even if there was an error
        if scraper:
            try:
                scraper.close()
                st.session_state.session_logger.info("WebDriver closed successfully")
            except Exception as e:
                warning_msg = f"Could not close scraper properly - {str(e)}"
                st.warning(f"⚠️ Warning: {warning_msg}")
                st.session_state.session_logger.warning(warning_msg)

        # Process results (even if some failed or scraping was interrupted)
        if results:
            try:
                st.session_state.session_logger.info(f"Processing {len(results)} results...")
                processor = DataProcessor()
                output_df = processor.process_scraped_data(results)
                st.session_state.results = output_df
                st.session_state.session_logger.info(f"Results processed successfully - {len(output_df)} rows")
            except Exception as e:
                st.warning(f"⚠️ Warning: Could not process all results - {str(e)}")
                st.session_state.session_logger.error(f"Error processing results: {str(e)}")
                st.session_state.session_logger.debug(traceback.format_exc())

        # Calculate final stats
        total_time = time.time() - st.session_state.start_time if st.session_state.start_time else 0

        # Mark as complete
        st.session_state.scraping_in_progress = False
        if st.session_state.stop_scraping or was_interrupted:
            if results:
                status_container.warning(f"⚠️ Scraping interrupted — {len(results)} partial results saved. Download below.")
            else:
                status_container.warning("⚠️ Scraping interrupted before any results were collected")
            st.session_state.stop_scraping = False
        else:
            status_container.success("✅ Scraping Complete!")

        # Log completion
        st.session_state.session_logger.info("="*80)
        st.session_state.session_logger.info("SCRAPING ENDED")
        st.session_state.session_logger.info(f"Total CNPJs requested: {total}")
        st.session_state.session_logger.info(f"CNPJs processed: {len(results)}")
        st.session_state.session_logger.info(f"Successful: {st.session_state.success_count}")
        st.session_state.session_logger.info(f"Failed: {st.session_state.failed_count}")
        st.session_state.session_logger.info(f"Total Time: {total_time/60:.2f} minutes")
        if len(results) > 0:
            st.session_state.session_logger.info(f"Avg Time per CNPJ: {total_time/len(results):.1f} seconds")
        st.session_state.session_logger.info("="*80)

        st.rerun()

# Results section
if st.session_state.results is not None and not st.session_state.scraping_in_progress:
    st.markdown("---")
    st.header("✅ Scraping Complete!")

    # Summary
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total CNPJs", len(st.session_state.cnpjs))

    with col2:
        success_rate = (st.session_state.success_count / len(st.session_state.cnpjs) * 100) if st.session_state.cnpjs else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")

    with col3:
        st.metric("Successful", st.session_state.success_count)

    with col4:
        if st.session_state.start_time:
            total_time = time.time() - st.session_state.start_time
            st.metric("Total Time", f"{total_time/60:.1f} min")

    # Results preview
    st.subheader("📊 Results Preview")
    st.dataframe(st.session_state.results.head(10), width='stretch')

    # Download buttons
    st.subheader("📥 Download Results")

    # Prepare Excel file
    output_buffer = io.BytesIO()
    st.session_state.results.to_excel(output_buffer, index=False)
    output_buffer.seek(0)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"anbima_results_{timestamp}.xlsx"

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        st.download_button(
            label="⬇️ Download Excel",
            data=output_buffer,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            width='stretch'
        )

    with col2:
        # Prepare log file for download
        if st.session_state.log_file.exists():
            log_content = st.session_state.log_file.read_text(encoding='utf-8')
            log_filename = st.session_state.log_file.name

            st.download_button(
                label="📋 Download Log",
                data=log_content,
                file_name=log_filename,
                mime="text/plain",
                width='stretch'
            )

    with col3:
        st.info(f"📄 Excel: {len(output_buffer.getvalue())/1024:.1f} KB | 📋 Log: {st.session_state.log_file.stat().st_size/1024:.1f} KB")

    # New scraping button
    if st.button("🔄 Start New Scraping", width='content'):
        st.session_state.results = None
        st.session_state.cnpjs = []
        st.session_state.success_count = 0
        st.session_state.failed_count = 0
        st.session_state.status_messages = []
        st.session_state.start_time = None
        st.rerun()

# Footer
st.markdown("---")
st.caption("🔒 Phase 1 & 2 Anti-Spam Active | 💡 Stealth Mode Recommended | 📖 [Documentation](https://github.com/luizpersechini/Eduardo-Scrapping)")
