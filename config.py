"""
Configuration file for ANBIMA scraper
Contains URLs, selectors, and other constants
"""

# ANBIMA URLs
ANBIMA_BASE_URL = "https://data.anbima.com.br/busca/fundos"

# Timeouts (in seconds) - Optimized for anti-spam compliance
PAGE_LOAD_TIMEOUT = 60  # Increased for better stability
ELEMENT_WAIT_TIMEOUT = 40  # Increased for better stability
IMPLICIT_WAIT = 10  # Standard for stability
SLEEP_BETWEEN_REQUESTS = 5  # Increased to reduce rate limit triggers

# Parallel processing configuration
DEFAULT_WORKERS = 1  # Reduced to 1 to avoid rate limiting
MAX_WORKERS = 4  # Maximum allowed

# Selenium selectors
SELECTORS = {
    # Search box where CNPJ is entered
    "search_input": "input[placeholder*='Busque fundos']",
    
    # Search button
    "search_button": "button[type='submit']",
    
    # Fund result in the list (clickable)
    "fund_result": "table tbody tr",
    
    # "DADOS PERIÓDICOS" tab button
    "periodic_data_tab": "//button[contains(text(), 'DADOS PERIÓDICOS')] | //a[contains(text(), 'DADOS PERIÓDICOS')]",
    
    # Table with periodic data
    "periodic_data_table": "table",
    
    # Fund name from the detail page
    "fund_name": "h1, h2.fund-name, .fund-title",
}

# Output Excel columns
OUTPUT_COLUMNS = [
    "CNPJ",
    "Nome do Fundo",
    "Data da cotização",
    "Valor cota",
    "Status"
]

# Input Excel columns
INPUT_COLUMN_CNPJ = "CNPJ"

# Logging configuration
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_DIR = "logs"
LOG_FILE = "anbima_scraper.log"

# Chrome options
CHROME_OPTIONS = [
    "--headless=new",  # New headless mode (more stable)
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--window-size=1920,1080",
    "--disable-blink-features=AutomationControlled",
    "--disable-features=VizDisplayCompositor",
    "--disable-extensions",
    "--disable-logging",
    "--disable-web-security",
    "--ignore-certificate-errors",
    "--allow-running-insecure-content",
    "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
MAX_CNPJ_TIMEOUT = 180  # Maximum time per CNPJ (3 minutes)

# Stealth mode settings
STEALTH_MODE = True  # Enabled by default for anti-spam compliance
STEALTH_MIN_DELAY = 8.0  # Minimum delay between actions (seconds) - increased for anti-bot
STEALTH_MAX_DELAY = 15.0  # Maximum delay between actions (seconds) - increased for anti-bot
STEALTH_MOUSE_MOVEMENTS = True  # Simulate mouse movements
RECOMMEND_NON_HEADLESS = True  # Headless mode more likely to be detected

# Parse.bot Configuration
# SECURITY: API keys removed from code - set via environment variables
import os
PARSE_BOT_API_KEY = os.getenv("PARSE_BOT_API_KEY", "")  # Set in Streamlit Cloud secrets
PARSE_BOT_API_URL = "https://api.parse.bot"
# NOTE: The value below must be the SCRAPER ID (from the dashboard URL), NOT the API Key.
PARSE_BOT_SCRAPER_ID = os.getenv("PARSE_BOT_SCRAPER_ID", "")  # Set in Streamlit Cloud secrets
USE_PARSE_BOT = False  # Disabled by default (not used in Streamlit app)
