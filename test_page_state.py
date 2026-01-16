"""Debug: Check page state and available elements"""
from anbima_scraper import ANBIMAScraper
import time

def debug_page_state(headless=True):
    """Check what's on the page"""
    print(f"\n{'='*80}")
    print(f"DEBUGGING PAGE STATE - {'HEADLESS' if headless else 'NON-HEADLESS'}")
    print(f"{'='*80}\n")
    
    scraper = ANBIMAScraper(headless=headless)
    
    try:
        # Setup and navigate
        if not scraper.setup_driver():
            print("Failed to setup driver")
            return
        
        print("Navigating to ANBIMA...")
        scraper.driver.get("https://data.anbima.com.br/busca/fundos")
        print("Waiting 5 seconds for page to load...")
        time.sleep(5)
        
        # Take screenshot
        screenshot_name = f"debug_page_{'headless' if headless else 'nonheadless'}_{int(time.time())}.png"
        scraper.driver.save_screenshot(screenshot_name)
        print(f"Screenshot saved: {screenshot_name}")
        
        # Get page source and look for input elements
        page_source = scraper.driver.page_source
        print(f"\nPage title: {scraper.driver.title}")
        print(f"Page URL: {scraper.driver.current_url}")
        print(f"Page source length: {len(page_source)} characters")
        
        # Look for input elements
        from selenium.webdriver.common.by import By
        inputs = scraper.driver.find_elements(By.TAG_NAME, "input")
        print(f"\nFound {len(inputs)} input elements:")
        for i, inp in enumerate(inputs[:10]):  # Show first 10
            try:
                placeholder = inp.get_attribute('placeholder')
                inp_type = inp.get_attribute('type')
                inp_id = inp.get_attribute('id')
                inp_class = inp.get_attribute('class')
                print(f"  {i+1}. type={inp_type}, id={inp_id}, placeholder={placeholder}, class={inp_class[:50] if inp_class else ''}")
            except:
                print(f"  {i+1}. Could not get attributes")
        
        # Try to find by different selectors
        selectors_to_try = [
            "input[placeholder*='Busque fundos']",
            "input[placeholder*='Pesquise']",
            "input[type='text']",
            "input[type='search']",
            "input.search",
            "#search",
        ]
        
        print(f"\nTrying different selectors:")
        for selector in selectors_to_try:
            try:
                elements = scraper.driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"  '{selector}': {len(elements)} element(s)")
            except Exception as e:
                print(f"  '{selector}': Error - {str(e)[:30]}")
        
    finally:
        scraper.close()

if __name__ == '__main__':
    debug_page_state(headless=True)
    print("\n" + "="*80)
    time.sleep(2)
    debug_page_state(headless=False)






