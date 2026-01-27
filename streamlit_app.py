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

# Import existing scrapers
from stealth_scraper import StealthANBIMAScraper
from data_processor import DataProcessor
import config

# Configure page
st.set_page_config(
    page_title="ANBIMA Fund Data Scraper",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
st.title("🏦 ANBIMA Fund Data Scraper")
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
    - ✅ Real-time progress
    - ✅ 36 validated CNPJs
    - ✅ Excel export
    """)

    st.markdown("---")
    st.caption("Phase 1 & 2 Anti-spam Active")

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

    # Template download
    if st.button("📥 Download Template (36 Valid CNPJs)"):
        template_path = Path("input_valid_cnpjs.xlsx")
        if template_path.exists():
            with open(template_path, 'rb') as f:
                st.download_button(
                    label="⬇️ Click to Download",
                    data=f,
                    file_name="input_valid_cnpjs.xlsx",
                    mime="application/vnd.ms-excel"
                )
        else:
            st.error("Template file not found. Please use your own CNPJ list.")

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
        st.dataframe(preview_df, use_container_width=True)

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

    # Status metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Progress", f"{st.session_state.progress:.0%}")

    with col2:
        st.metric("Success", st.session_state.success_count,
                 delta=None if st.session_state.success_count == 0 else st.session_state.success_count)

    with col3:
        st.metric("Failed", st.session_state.failed_count,
                 delta=None if st.session_state.failed_count == 0 else -st.session_state.failed_count)

    with col4:
        if st.session_state.start_time:
            elapsed = time.time() - st.session_state.start_time
            st.metric("Time Elapsed", f"{elapsed/60:.1f} min")

    # Current status
    status_container = st.container()

    # Activity log
    with st.expander("📜 Activity Log", expanded=True):
        log_container = st.container()

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
            status_container.info(f"🔄 Scraping: {cnpj} ({idx}/{total})")

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

            # Update UI
            progress_bar.progress(st.session_state.progress)

            with log_container:
                # Show last 10 messages
                for msg in st.session_state.status_messages[-10:]:
                    st.text(msg)

            # Refresh metrics
            col2.metric("Success", st.session_state.success_count)
            col3.metric("Failed", st.session_state.failed_count)

            if st.session_state.start_time:
                elapsed = time.time() - st.session_state.start_time
                col4.metric("Time Elapsed", f"{elapsed/60:.1f} min")

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
    st.dataframe(st.session_state.results.head(10), use_container_width=True)

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
