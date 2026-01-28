"""
ANBIMA Fund Data Scraper - Web UI
Simple web interface for scraping ANBIMA fund data
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime
import time
import logging
from pathlib import Path
import hashlib
import subprocess

# Import existing scrapers
from stealth_scraper import StealthANBIMAScraper
from data_processor import DataProcessor
import config

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

        if st.button("Login", type="primary", use_container_width=True):
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

    headless = st.checkbox("Headless Mode", value=True,
                          help="Run browser without GUI (faster)")

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

    # Logout button
    if st.button("🚪 Logout", use_container_width=True):
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
            else:
                st.error("❌ Missing 'CNPJ' column")
                st.session_state.cnpjs = []
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            st.session_state.cnpjs = []
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
        st.dataframe(preview_df, width="stretch")

# Scraping controls
if st.session_state.cnpjs and not st.session_state.scraping_in_progress:
    st.markdown("---")
    st.header("🚀 Step 2: Start Scraping")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if st.button("🚀 Start Scraping", type="primary", use_container_width=True):
            st.session_state.scraping_in_progress = True
            st.session_state.progress = 0
            st.session_state.success_count = 0
            st.session_state.failed_count = 0
            st.session_state.status_messages = []
            st.session_state.start_time = time.time()
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
    try:
        # Initialize scraper
        if use_stealth:
            scraper = StealthANBIMAScraper(headless=headless)
        else:
            from anbima_scraper import ANBIMAScraper
            scraper = ANBIMAScraper(headless=headless)

        if not scraper.setup_driver():
            st.error("❌ Failed to initialize web driver")
            st.session_state.scraping_in_progress = False
            st.stop()

        # Process CNPJs
        results = []
        total = len(st.session_state.cnpjs)

        for idx, cnpj in enumerate(st.session_state.cnpjs, 1):
            # Update status
            with status_container:
                st.info(f"🔄 Scraping: {cnpj} ({idx}/{total})")

            # Scrape
            result = scraper.scrape_fund_data(cnpj)
            results.append(result)

            # Update counters
            if result.get('Status') == 'Success':
                st.session_state.success_count += 1
                message = f"✅ {cnpj} - Success ({len(result.get('periodic_data', []))} data points)"
                st.session_state.status_messages.append(message)
            else:
                st.session_state.failed_count += 1
                message = f"❌ {cnpj} - {result.get('Status', 'Failed')}"
                st.session_state.status_messages.append(message)

            # Update progress
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

        # Close scraper
        scraper.close()

        # Process results
        if results:
            processor = DataProcessor()
            output_df = processor.process_scraped_data(results)
            st.session_state.results = output_df

        # Mark as complete
        st.session_state.scraping_in_progress = False
        status_container.success("✅ Scraping Complete!")

        st.rerun()

    except Exception as e:
        st.error(f"❌ Error during scraping: {str(e)}")
        st.session_state.scraping_in_progress = False
        try:
            scraper.close()
        except:
            pass

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
    st.dataframe(st.session_state.results.head(10), width="stretch")

    # Download button
    st.subheader("📥 Download Results")

    # Prepare Excel file
    output_buffer = io.BytesIO()
    st.session_state.results.to_excel(output_buffer, index=False)
    output_buffer.seek(0)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"anbima_results_{timestamp}.xlsx"

    col1, col2 = st.columns([1, 3])

    with col1:
        st.download_button(
            label="⬇️ Download Excel",
            data=output_buffer,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True
        )

    with col2:
        st.info(f"📄 File: {filename} | Size: {len(output_buffer.getvalue())/1024:.1f} KB")

    # New scraping button
    if st.button("🔄 Start New Scraping", use_container_width=False):
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
