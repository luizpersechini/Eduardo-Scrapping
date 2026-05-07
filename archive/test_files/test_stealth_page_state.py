"""Debug: Check page state with stealth scraper"""
from stealth_scraper import StealthANBIMAScraper
import time

def debug_stealth_page_state(headless=False):
    """Check what's on the page with stealth mode"""
    print(f"\n{'='*80}")
    print(f"DEBUGGING STEALTH PAGE STATE - {'HEADLESS' if headless else 'NON-HEADLESS'}")
    print(f"{'='*80}\n")
    
    scraper = StealthANBIMAScraper(headless=headless)
    
    try:
        # Setup and navigate
        if not scraper.setup_driver():
            print("Failed to setup driver")
            return
        
        print("Navigating to ANBIMA...")
        scraper.driver.get("https://data.anbima.com.br/busca/fundos")
        print("Waiting 8 seconds for page to load...")
        time.sleep(8)
        
        # Take screenshot
        screenshot_name = f"debug_stealth_{'headless' if headless else 'nonheadless'}_{int(time.time())}.png"
        scraper.driver.save_screenshot(screenshot_name)
        print(f"Screenshot saved: {screenshot_name}")
        
        # Get page state
        print(f"\nPage title: {scraper.driver.title}")
        print(f"Page URL: {scraper.driver.current_url}")
        
        # Check if we're on anti-bot page
        if "anti-robô" in scraper.driver.title.lower() or "/robo" in scraper.driver.current_url:
            print("\n❌ REDIRECTED TO ANTI-BOT PAGE!")
            return
        
        # Look for input elements
        from selenium.webdriver.common.by import By
        inputs = scraper.driver.find_elements(By.TAG_NAME, "input")
        print(f"\nFound {len(inputs)} input elements:")
        
        found_search = False
        for i, inp in enumerate(inputs[:10]):  # Show first 10
            try:
                placeholder = inp.get_attribute('placeholder')
                if placeholder and 'Busque' in placeholder:
                    found_search = True
                print(f"  {i+1}. placeholder={placeholder[:60]}")
            except:
                pass
        
        if found_search:
            print("\n✅ SEARCH INPUT FOUND! Stealth mode working!")
        else:
            print("\n⚠️  Search input not found")
        
    finally:
        scraper.close()

if __name__ == '__main__':
    debug_stealth_page_state(headless=False)






