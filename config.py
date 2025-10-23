"""
Configuration file for ANBIMA scraper
Contains URLs, selectors, and other constants
"""

# ANBIMA URLs
ANBIMA_BASE_URL = "https://data.anbima.com.br/busca/fundos"

# Timeouts (in seconds) - Otimizados para melhor performance
PAGE_LOAD_TIMEOUT = 20  # Reduzido de 30s para 20s
ELEMENT_WAIT_TIMEOUT = 15  # Reduzido de 20s para 15s
IMPLICIT_WAIT = 5  # Reduzido de 10s para 5s
SLEEP_BETWEEN_REQUESTS = 1  # Reduzido de 2s para 1s (por worker)

# Parallel processing configuration
DEFAULT_WORKERS = 4  # Número padrão de workers paralelos
MAX_WORKERS = 8  # Máximo recomendado para evitar sobrecarga

# Selenium selectors
SELECTORS = {
    # Search box where CNPJ is entered
    "search_input": "input[placeholder*='Pesquise']",
    
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
    "--headless",  # Run in background
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--window-size=1920,1080",
    "--disable-blink-features=AutomationControlled",
    "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

