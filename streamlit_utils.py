"""
Utility functions for Streamlit web UI
Helper functions for scraping, progress tracking, and data processing
"""

import streamlit as st
import pandas as pd
import logging
from typing import List, Dict, Callable
import time

def validate_cnpj_file(uploaded_file) -> tuple:
    """
    Validate uploaded CNPJ file

    Args:
        uploaded_file: Streamlit uploaded file object

    Returns:
        Tuple of (success: bool, cnpjs: list, message: str)
    """
    try:
        # Read Excel file
        df = pd.read_excel(uploaded_file)

        # Check for CNPJ column
        if 'CNPJ' not in df.columns:
            return False, [], "File must contain 'CNPJ' column"

        # Extract CNPJs
        cnpjs = df['CNPJ'].tolist()

        # Remove NaN values
        cnpjs = [c for c in cnpjs if pd.notna(c)]

        if not cnpjs:
            return False, [], "No valid CNPJs found in file"

        return True, cnpjs, f"Successfully loaded {len(cnpjs)} CNPJs"

    except Exception as e:
        return False, [], f"Error reading file: {str(e)}"


def format_time(seconds: float) -> str:
    """
    Format seconds into human-readable time

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string
    """
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} min"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"


def estimate_time(num_cnpjs: int, avg_time_per_cnpj: float = 132) -> str:
    """
    Estimate total scraping time

    Args:
        num_cnpjs: Number of CNPJs to scrape
        avg_time_per_cnpj: Average time per CNPJ in seconds (default: 132s = 2.2 min)

    Returns:
        Formatted estimated time string
    """
    total_seconds = num_cnpjs * avg_time_per_cnpj
    return format_time(total_seconds)


def calculate_eta(processed: int, total: int, start_time: float) -> str:
    """
    Calculate estimated time remaining

    Args:
        processed: Number of CNPJs processed
        total: Total number of CNPJs
        start_time: Start timestamp

    Returns:
        Formatted ETA string
    """
    if processed == 0:
        return "Calculating..."

    elapsed = time.time() - start_time
    avg_time_per_cnpj = elapsed / processed
    remaining = total - processed
    eta_seconds = remaining * avg_time_per_cnpj

    return format_time(eta_seconds)


def create_download_excel(df: pd.DataFrame) -> bytes:
    """
    Create Excel file in memory for download

    Args:
        df: DataFrame to convert to Excel

    Returns:
        Excel file bytes
    """
    import io

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='ANBIMA Data')
    output.seek(0)

    return output.getvalue()


def format_cnpj(cnpj: str) -> str:
    """
    Format CNPJ with proper punctuation

    Args:
        cnpj: CNPJ string (may or may not have punctuation)

    Returns:
        Formatted CNPJ (XX.XXX.XXX/XXXX-XX)
    """
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, str(cnpj)))

    # Check if valid length
    if len(digits) != 14:
        return str(cnpj)

    # Format
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:14]}"


def display_progress_metrics(col1, col2, col3, col4, progress_data: Dict):
    """
    Display progress metrics in columns

    Args:
        col1, col2, col3, col4: Streamlit column objects
        progress_data: Dictionary with progress information
    """
    with col1:
        progress_pct = progress_data.get('progress', 0) * 100
        st.metric("Progress", f"{progress_pct:.0f}%")

    with col2:
        success = progress_data.get('success', 0)
        st.metric("Success", success,
                 delta=None if success == 0 else success)

    with col3:
        failed = progress_data.get('failed', 0)
        st.metric("Failed", failed,
                 delta=None if failed == 0 else -failed)

    with col4:
        elapsed = progress_data.get('elapsed', 0)
        st.metric("Time Elapsed", format_time(elapsed))


def display_status_message(status: str, cnpj: str, message: str = None):
    """
    Display formatted status message

    Args:
        status: Status type ('success', 'error', 'info', 'warning')
        cnpj: CNPJ being processed
        message: Optional additional message
    """
    formatted_cnpj = format_cnpj(cnpj)

    if status == 'success':
        st.success(f"✅ {formatted_cnpj} - Success {message or ''}")
    elif status == 'error':
        st.error(f"❌ {formatted_cnpj} - {message or 'Failed'}")
    elif status == 'info':
        st.info(f"🔄 {formatted_cnpj} - {message or 'Processing...'}")
    elif status == 'warning':
        st.warning(f"⚠️ {formatted_cnpj} - {message or 'Warning'}")


def get_result_statistics(results: List[Dict]) -> Dict:
    """
    Calculate statistics from scraping results

    Args:
        results: List of result dictionaries from scraper

    Returns:
        Dictionary with statistics
    """
    total = len(results)
    success = sum(1 for r in results if r.get('Status') == 'Success')
    failed = total - success

    total_data_points = 0
    for r in results:
        if r.get('Status') == 'Success':
            total_data_points += len(r.get('periodic_data', []))

    return {
        'total': total,
        'success': success,
        'failed': failed,
        'success_rate': (success / total * 100) if total > 0 else 0,
        'total_data_points': total_data_points,
        'avg_data_points': (total_data_points / success) if success > 0 else 0
    }


def create_summary_report(results: List[Dict], elapsed_time: float) -> str:
    """
    Create text summary report

    Args:
        results: List of result dictionaries
        elapsed_time: Total time elapsed in seconds

    Returns:
        Formatted summary text
    """
    stats = get_result_statistics(results)

    report = f"""
    📊 SCRAPING SUMMARY
    ═══════════════════════════════════════

    Total CNPJs:        {stats['total']}
    Successful:         {stats['success']} ({stats['success_rate']:.1f}%)
    Failed:             {stats['failed']}

    Total Data Points:  {stats['total_data_points']}
    Avg per Fund:       {stats['avg_data_points']:.1f}

    Total Time:         {format_time(elapsed_time)}
    Avg per CNPJ:       {format_time(elapsed_time / stats['total']) if stats['total'] > 0 else 'N/A'}

    ═══════════════════════════════════════
    """

    return report


def setup_logging(level=logging.INFO):
    """
    Setup logging for Streamlit app

    Args:
        level: Logging level
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


class ScrapingCallback:
    """
    Callback class for progress updates during scraping
    """

    def __init__(self, total_cnpjs: int):
        """
        Initialize callback

        Args:
            total_cnpjs: Total number of CNPJs to process
        """
        self.total = total_cnpjs
        self.processed = 0
        self.success = 0
        self.failed = 0
        self.current_cnpj = None
        self.messages = []

    def update(self, cnpj: str, status: str, message: str = None):
        """
        Update progress

        Args:
            cnpj: CNPJ being processed
            status: Status ('success', 'failed', 'processing')
            message: Optional message
        """
        self.current_cnpj = cnpj

        if status == 'success':
            self.success += 1
            self.processed += 1
            self.messages.append(f"✅ {cnpj} - Success")
        elif status == 'failed':
            self.failed += 1
            self.processed += 1
            self.messages.append(f"❌ {cnpj} - {message or 'Failed'}")
        elif status == 'processing':
            self.messages.append(f"🔄 {cnpj} - Processing...")

    def get_progress(self) -> float:
        """Get progress percentage (0-1)"""
        return self.processed / self.total if self.total > 0 else 0

    def get_latest_messages(self, n: int = 10) -> List[str]:
        """Get last n messages"""
        return self.messages[-n:]


def display_help_section():
    """Display help information"""
    with st.expander("❓ Need Help?"):
        st.markdown("""
        ### How to Use

        1. **Upload CNPJ List**
           - Click "Choose a file" and select your Excel file
           - File must have a column named "CNPJ"
           - Download the template if you don't have a file

        2. **Configure Settings (Optional)**
           - Stealth Mode: Recommended to avoid bot detection
           - Headless Mode: Run without showing browser (faster)
           - Workers: Use 1 for stability

        3. **Start Scraping**
           - Click "Start Scraping" button
           - Watch progress in real-time
           - Wait for completion (~2 min per CNPJ)

        4. **Download Results**
           - Click "Download Excel" when complete
           - File includes all scraped data
           - Ready to use in Excel/Google Sheets

        ### Troubleshooting

        **Upload fails:**
        - Check file format (must be .xlsx or .xls)
        - Ensure "CNPJ" column exists
        - Make sure CNPJs are formatted correctly

        **Scraping stops:**
        - Refresh page and try again
        - Reduce number of workers to 1
        - Enable stealth mode

        **Download doesn't work:**
        - Check browser allows downloads
        - Try different browser
        - Clear browser cache

        ### Support

        📧 Contact: [Your Email]
        📖 Documentation: [GitHub Link]
        🐛 Report Issue: [GitHub Issues]
        """)
