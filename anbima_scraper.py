"""
ANBIMA Fund Scraper using Selenium
Handles web scraping of fund data from ANBIMA website
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
    StaleElementReferenceException
)
from webdriver_manager.chrome import ChromeDriverManager

import config


class ANBIMAScraper:
    """Selenium-based scraper for ANBIMA fund data"""
    
    def __init__(self, headless: bool = True):
        """
        Initialize the scraper
        
        Args:
            headless: Whether to run browser in headless mode
        """
        self.driver = None
        self.wait = None
        self.headless = headless
        self.logger = logging.getLogger(__name__)
        
    def setup_driver(self):
        """Initialize Selenium WebDriver with Chrome"""
        try:
            chrome_options = Options()
            
            # Add options from config
            for option in config.CHROME_OPTIONS:
                if not self.headless and option == "--headless":
                    continue  # Skip headless if disabled
                chrome_options.add_argument(option)
            
            # Initialize the driver
            # Try to get the chromedriver path and fix it if necessary
            import os
            try:
                driver_path = ChromeDriverManager().install()
                self.logger.info(f"ChromeDriver initial path: {driver_path}")
                
                # Fix the path if it points to wrong file
                if not driver_path.endswith('chromedriver') or 'THIRD_PARTY' in driver_path:
                    driver_dir = os.path.dirname(driver_path)
                    # Look for the actual chromedriver executable
                    for file in os.listdir(driver_dir):
                        if file == 'chromedriver':
                            driver_path = os.path.join(driver_dir, file)
                            self.logger.info(f"Found chromedriver at: {driver_path}")
                            break
                
                # Make sure it's executable
                if os.path.exists(driver_path):
                    os.chmod(driver_path, 0o755)
                    service = Service(driver_path)
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                else:
                    raise FileNotFoundError(f"ChromeDriver not found at {driver_path}")
                    
            except Exception as e:
                self.logger.error(f"ChromeDriverManager failed: {e}")
                raise
            
            # Set timeouts
            self.driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
            self.driver.implicitly_wait(config.IMPLICIT_WAIT)
            
            # Initialize WebDriverWait
            self.wait = WebDriverWait(self.driver, config.ELEMENT_WAIT_TIMEOUT)
            
            self.logger.info("WebDriver initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {str(e)}")
            return False
    
    def search_fund(self, cnpj: str) -> Tuple[bool, str]:
        """
        Search for a fund by CNPJ
        
        Args:
            cnpj: The CNPJ to search for
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Navigate to ANBIMA page
            self.logger.info(f"Navigating to {config.ANBIMA_BASE_URL}")
            self.driver.get(config.ANBIMA_BASE_URL)
            
            # Wait for page to load
            time.sleep(3)
            
            # Close cookies banner if present
            try:
                cookie_button = self.driver.find_element(By.LINK_TEXT, "Prosseguir")
                cookie_button.click()
                time.sleep(1)
            except:
                pass
            
            # Find and fill search input
            self.logger.info(f"Searching for CNPJ: {cnpj}")
            search_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Busque fundos']"))
            )
            
            # Clear and enter CNPJ
            search_input.clear()
            search_input.send_keys(cnpj)
            
            # Wait for autocomplete dropdown to appear
            time.sleep(3)
            
            # Try to click on the dropdown result link
            self.logger.info("Looking for fund in dropdown results...")
            
            try:
                # Look for the link in the dropdown that says "em fundos de investimento"
                dropdown_link = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/busca/fundos?q=')]"))
                )
                
                dropdown_link.click()
                time.sleep(2)
                
                # Now we should be on the search results page
                # Wait for the results table
                self.logger.info("Waiting for search results...")
                time.sleep(2)
                
                # Try to close dropdown if it's still open
                try:
                    close_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='close-dropdown']")
                    close_button.click()
                    time.sleep(1)
                except:
                    pass
                
                # Now find and click the fund link in the results
                fund_links = self.driver.find_elements(By.CSS_SELECTOR, "article a[href*='/fundos/C']")
                
                if not fund_links:
                    return False, "No fund found for this CNPJ"
                
                self.logger.info(f"Found {len(fund_links)} result(s). Clicking on the first one...")
                fund_links[0].click()
                time.sleep(3)
                
                return True, "Fund found and clicked"
                
            except TimeoutException:
                return False, f"No results found for CNPJ: {cnpj}"
                
        except TimeoutException as e:
            self.logger.error(f"Timeout while searching for CNPJ {cnpj}: {str(e)}")
            return False, "Timeout: Page took too long to load"
        except Exception as e:
            self.logger.error(f"Error searching for CNPJ {cnpj}: {str(e)}")
            return False, f"Error: {str(e)}"
    
    def get_fund_name(self) -> Optional[str]:
        """
        Extract the fund name from the detail page
        
        Returns:
            Fund name or None if not found
        """
        try:
            # Try multiple selectors for fund name
            selectors = [
                "h1",
                "h2",
                ".fund-name",
                ".fund-title",
                "[class*='title']",
                "[class*='name']"
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    name = element.text.strip()
                    if name and len(name) > 5:  # Basic validation
                        self.logger.info(f"Found fund name: {name}")
                        return name
                except NoSuchElementException:
                    continue
            
            # If no name found, try to get from page source
            page_source = self.driver.page_source
            if "CLASSE" in page_source:
                # Extract from visible text
                lines = page_source.split('\n')
                for line in lines:
                    if 'CLASSE' in line.upper() and len(line) > 10:
                        # Clean HTML tags
                        import re
                        clean_line = re.sub('<[^<]+?>', '', line).strip()
                        if clean_line and len(clean_line) > 10:
                            return clean_line[:200]  # Limit length
            
            self.logger.warning("Could not find fund name")
            return "N/A"
            
        except Exception as e:
            self.logger.error(f"Error getting fund name: {str(e)}")
            return "N/A"
    
    def navigate_to_periodic_data(self) -> Tuple[bool, str]:
        """
        Navigate to the 'DADOS PERIÓDICOS' page
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            self.logger.info("Navigating to Dados Periódicos page...")
            
            # Get the current URL and modify it to go to dados-periodicos
            current_url = self.driver.current_url
            
            # Replace any existing path after the fund code with /dados-periodicos
            if '/fundos/C' in current_url:
                # Extract the fund code part
                base_url = current_url.split('/fundos/')[0]
                fund_code = current_url.split('/fundos/')[1].split('/')[0]
                
                # Construct the periodic data URL
                periodic_url = f"{base_url}/fundos/{fund_code}/dados-periodicos"
                
                self.logger.info(f"Navigating to {periodic_url}")
                self.driver.get(periodic_url)
                time.sleep(3)
                
                return True, "Successfully navigated to Dados Periódicos page"
            else:
                self.logger.error("Could not determine fund URL")
                return False, "Could not determine fund URL"
                
        except Exception as e:
            self.logger.error(f"Error navigating to periodic data page: {str(e)}")
            return False, f"Error: {str(e)}"
    
    def extract_periodic_data(self) -> Tuple[bool, List[Dict], str]:
        """
        Extract ALL periodic data from the table
        Extracts only: Data competência and Valor cota
        Scrolls to load all historical data
        
        Returns:
            Tuple of (success: bool, data: List[Dict], message: str)
        """
        try:
            self.logger.info("Extracting periodic data table...")
            
            # Wait for table to be present
            time.sleep(3)
            
            # Find the table on the page
            try:
                table = self.wait.until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )
            except TimeoutException:
                return False, [], "No table found on page"
            
            self.logger.info("Found periodic data table")
            
            try:
                # Get table headers to find the indices of the columns we need
                thead = table.find_element(By.TAG_NAME, "thead")
                header_cells = thead.find_elements(By.CSS_SELECTOR, "th, td")
                headers = [cell.text.strip() for cell in header_cells]
                self.logger.info(f"Table headers: {headers}")
                
                # Find indices of the columns we want
                date_idx = None
                cota_idx = None
                
                for idx, header in enumerate(headers):
                    header_upper = header.upper()
                    if "DATA" in header_upper and "COMPET" in header_upper:
                        date_idx = idx
                    elif "VALOR" in header_upper and "COTA" in header_upper and "PATRIMÔNIO" not in header_upper:
                        cota_idx = idx
                
                if date_idx is None or cota_idx is None:
                    self.logger.error(f"Could not find required columns. Date idx: {date_idx}, Cota idx: {cota_idx}")
                    return False, [], "Could not find required columns in table"
                
                self.logger.info(f"Found columns - Date index: {date_idx}, Cota index: {cota_idx}")
                
                # Scroll down to load all data (in case of lazy loading)
                self.logger.info("Scrolling to load all historical data...")
                last_height = 0
                same_height_count = 0
                max_scrolls = 50  # Limit to prevent infinite loops
                scroll_count = 0
                
                while scroll_count < max_scrolls:
                    # Scroll to bottom of page
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    
                    # Get new height
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    
                    if new_height == last_height:
                        same_height_count += 1
                        # If height hasn't changed for 3 consecutive scrolls, we're done
                        if same_height_count >= 3:
                            self.logger.info(f"Reached end of data after {scroll_count} scrolls")
                            break
                    else:
                        same_height_count = 0
                    
                    last_height = new_height
                    scroll_count += 1
                
                # Wait a bit for final data to load
                time.sleep(2)
                
                # Get table body again (it may have been updated)
                tbody = table.find_element(By.TAG_NAME, "tbody")
                rows = tbody.find_elements(By.TAG_NAME, "tr")
                
                if not rows:
                    return False, [], "No data rows found in table"
                
                self.logger.info(f"Found {len(rows)} total data rows after scrolling")
                
                # Extract data (only date and cota)
                data = []
                seen_dates = set()  # To avoid duplicates
                
                for row in rows:
                    try:
                        cells = row.find_elements(By.CSS_SELECTOR, "td")
                        if not cells or len(cells) <= max(date_idx, cota_idx):
                            continue
                        
                        date_value = cells[date_idx].text.strip()
                        cota_value = cells[cota_idx].text.strip()
                        
                        if date_value and cota_value and date_value not in seen_dates:
                            data.append({
                                "Data da cotização": date_value,
                                "Valor cota": cota_value
                            })
                            seen_dates.add(date_value)
                    
                    except Exception as e:
                        self.logger.warning(f"Error processing row: {str(e)}")
                        continue
                
                if data:
                    self.logger.info(f"Successfully extracted {len(data)} unique rows")
                    # Data is usually newest first, so reverse to get oldest first
                    data.reverse()
                    return True, data, f"Extracted {len(data)} periodic data records"
                else:
                    return False, [], "No data extracted from table"
            
            except Exception as e:
                self.logger.error(f"Error processing table: {str(e)}")
                return False, [], f"Error processing table: {str(e)}"
            
        except Exception as e:
            self.logger.error(f"Error extracting periodic data: {str(e)}")
            return False, [], f"Error: {str(e)}"
    
    def scrape_fund_data(self, cnpj: str) -> Dict:
        """
        Complete scraping workflow for a single CNPJ
        
        Args:
            cnpj: The CNPJ to scrape
            
        Returns:
            Dict with fund data and status
        """
        result = {
            "CNPJ": cnpj,
            "Nome do Fundo": "N/A",
            "periodic_data": [],
            "Status": "Unknown error"
        }
        
        try:
            # Step 1: Search for fund
            success, message = self.search_fund(cnpj)
            if not success:
                result["Status"] = message
                return result
            
            # Step 2: Get fund name
            fund_name = self.get_fund_name()
            result["Nome do Fundo"] = fund_name if fund_name else "N/A"
            
            # Step 3: Navigate to periodic data page
            success, message = self.navigate_to_periodic_data()
            if not success:
                result["Status"] = message
                return result
            
            # Step 4: Extract periodic data
            success, data, message = self.extract_periodic_data()
            if not success:
                result["Status"] = message
                return result
            
            result["periodic_data"] = data
            result["Status"] = "Success"
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in scrape_fund_data for {cnpj}: {str(e)}")
            result["Status"] = f"Error: {str(e)}"
            return result
    
    def close(self):
        """Close the browser and clean up"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("WebDriver closed")
            except Exception as e:
                self.logger.error(f"Error closing WebDriver: {str(e)}")
    
    def __enter__(self):
        """Context manager entry"""
        self.setup_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

