"""
ANBIMA Fund Scraper using Undetected ChromeDriver
Handles web scraping of fund data from ANBIMA website with stealth mode to avoid bot detection
"""

import time
import random
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
    StaleElementReferenceException
)

import config


class StealthANBIMAScraper:
    """Undetected ChromeDriver-based scraper for ANBIMA fund data"""
    
    def __init__(self, headless: bool = False):
        """
        Initialize the stealth scraper

        Args:
            headless: Whether to run browser in headless mode
        """
        self.driver = None
        self.wait = None
        self.headless = headless
        self.logger = logging.getLogger(__name__)
        self.rate_limit_count = 0
        
    def setup_driver(self):
        """Initialize Undetected ChromeDriver"""
        try:
            options = uc.ChromeOptions()
            
            # Add basic options (skip potentially problematic ones for undetected-chromedriver)
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-features=VizDisplayCompositor')
            # Don't add --headless here, undetected-chromedriver handles it
            # Don't add --disable-blink-features, it conflicts with UC
            # Don't add --disable-web-security or --allow-running-insecure-content, they crash UC
            
            # Initialize undetected ChromeDriver
            # Auto-detect Chrome version (will match current installation)
            self.driver = uc.Chrome(
                options=options,
                headless=self.headless
            )
            
            # Set timeouts
            self.driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
            self.driver.implicitly_wait(config.IMPLICIT_WAIT)
            
            # Initialize WebDriverWait
            self.wait = WebDriverWait(self.driver, config.ELEMENT_WAIT_TIMEOUT)
            
            self.logger.info("Stealth WebDriver initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Stealth WebDriver: {str(e)}")
            return False
    
    def human_delay(self, min_sec: float = None, max_sec: float = None):
        """
        Random delay to simulate human behavior
        
        Args:
            min_sec: Minimum delay in seconds (default from config)
            max_sec: Maximum delay in seconds (default from config)
        """
        if min_sec is None:
            min_sec = getattr(config, 'STEALTH_MIN_DELAY', 3.0)
        if max_sec is None:
            max_sec = getattr(config, 'STEALTH_MAX_DELAY', 7.0)
        
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
        self.logger.debug(f"Human delay: {delay:.2f}s")
    
    def simulate_human_behavior(self):
        """Simulate random human-like interactions"""
        try:
            # Random scroll
            if random.random() > 0.5:
                scroll_height = random.randint(50, 200)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_height});")
                time.sleep(random.uniform(0.5, 1.5))
            
            # Random mouse movement
            if random.random() > 0.5:
                try:
                    element = self.driver.find_element(By.TAG_NAME, 'body')
                    ActionChains(self.driver).move_to_element(element).perform()
                    time.sleep(random.uniform(0.3, 0.8))
                except:
                    pass
        except Exception as e:
            self.logger.debug(f"Human behavior simulation error (non-critical): {str(e)}")
    
    def search_fund(self, cnpj: str) -> Tuple[bool, str]:
        """
        Search for a fund by CNPJ with human-like behavior
        
        Args:
            cnpj: The CNPJ to search for
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Navigate to ANBIMA page
            self.logger.info(f"Navigating to {config.ANBIMA_BASE_URL}")
            self.driver.get(config.ANBIMA_BASE_URL)
            
            # Human delay after page load
            self.human_delay(3, 5)
            
            # Simulate human behavior
            if getattr(config, 'STEALTH_MOUSE_MOVEMENTS', True):
                self.simulate_human_behavior()
            
            # Close cookies banner if present
            try:
                cookie_button = self.driver.find_element(By.LINK_TEXT, "Prosseguir")
                cookie_button.click()
                self.human_delay(1, 2)
            except:
                pass
            
            # Find and fill search input
            self.logger.info(f"Searching for CNPJ: {cnpj}")
            search_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Busque fundos']"))
            )
            
            # Simulate human typing (delay between keystrokes)
            search_input.clear()
            for char in cnpj:
                search_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))  # Typing delay
            
            self.human_delay(2, 4)  # Wait before looking for dropdown
            
            # Try to click on the dropdown result link
            self.logger.info("Looking for fund in dropdown results...")
            
            try:
                dropdown_link = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/busca/fundos?q=')]"))
                )
                
                # Simulate mouse move before click
                if getattr(config, 'STEALTH_MOUSE_MOVEMENTS', True):
                    ActionChains(self.driver).move_to_element(dropdown_link).perform()
                    time.sleep(random.uniform(0.3, 0.8))
                
                dropdown_link.click()
                self.human_delay(2, 3)
                
                # Now we should be on the search results page
                self.logger.info("Waiting for search results...")
                self.human_delay(2, 3)
                
                # Try to close dropdown if it's still open
                try:
                    close_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='close-dropdown']")
                    close_button.click()
                    self.human_delay(0.5, 1)
                except:
                    pass
                
                # Now find and click the fund link in the results
                fund_links = self.driver.find_elements(By.CSS_SELECTOR, "article a[href*='/fundos/C']")
                
                if not fund_links:
                    return False, "No fund found for this CNPJ"
                
                self.logger.info(f"Found {len(fund_links)} result(s). Clicking on the first one...")
                
                # Move mouse and click
                if getattr(config, 'STEALTH_MOUSE_MOVEMENTS', True):
                    ActionChains(self.driver).move_to_element(fund_links[0]).perform()
                    time.sleep(random.uniform(0.3, 0.8))
                
                fund_links[0].click()
                self.human_delay(2, 4)
                
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
                self.human_delay(3, 5)
                
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
            self.human_delay(3, 5)
            
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
                    self.human_delay(0.8, 1.5)
                    
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
                self.human_delay(2, 3)
                
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
    
    def is_rate_limited(self) -> bool:
        """
        Detect if page shows rate limiting or blocking

        Returns:
            True if rate limited, False otherwise
        """
        try:
            # Don't check if we're on data:, or about:blank (initial page load)
            current_url = self.driver.current_url.lower()
            if 'data:' in current_url or 'about:blank' in current_url or not current_url:
                return False

            page_source = self.driver.page_source.lower()
            page_title = self.driver.title.lower()

            rate_limit_indicators = [
                'too many requests',
                '429',
                '423',
                'rate limit',
                'bloqueado',
                'blocked',
                'access denied',
                'temporarily unavailable',
                'try again later',
                'tente novamente',
                'acesso negado'
            ]

            # Only trigger if the indicator appears prominently (not just in page metadata)
            is_limited = any(indicator in page_title or
                           (indicator in page_source and len(page_source) < 5000)
                           for indicator in rate_limit_indicators)

            if is_limited:
                self.rate_limit_count += 1
                self.logger.warning(f"Rate limit detected! (count: {self.rate_limit_count})")
                self.logger.debug(f"Page title: {page_title[:100]}")
                self.logger.debug(f"URL: {current_url}")

            return is_limited

        except Exception as e:
            self.logger.debug(f"Error checking rate limit: {str(e)}")
            return False

    def scrape_fund_data(self, cnpj: str) -> Dict:
        """
        Complete scraping workflow for a single CNPJ with stealth mode

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
            # Check for rate limiting before starting
            if self.is_rate_limited():
                result["Status"] = "Rate limited"
                return result

            # Step 1: Search for fund
            success, message = self.search_fund(cnpj)
            if not success:
                result["Status"] = message
                return result

            # Check for rate limiting after search
            if self.is_rate_limited():
                result["Status"] = "Rate limited"
                return result

            # Step 2: Get fund name
            fund_name = self.get_fund_name()
            result["Nome do Fundo"] = fund_name if fund_name else "N/A"

            # Step 3: Navigate to periodic data page
            success, message = self.navigate_to_periodic_data()
            if not success:
                result["Status"] = message
                return result

            # Check for rate limiting after navigation
            if self.is_rate_limited():
                result["Status"] = "Rate limited"
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
                self.logger.info("Stealth WebDriver closed")
            except Exception as e:
                self.logger.error(f"Error closing WebDriver: {str(e)}")
    
    def __enter__(self):
        """Context manager entry"""
        self.setup_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

