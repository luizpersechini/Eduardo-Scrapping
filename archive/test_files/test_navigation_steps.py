"""Test each navigation step separately in headless mode"""
from anbima_scraper import ANBIMAScraper
import time

def test_navigation_steps(headless=True):
    """Test each step of navigation to find where timeout occurs"""
    test_cnpj = '48.330.198/0001-06'
    
    print(f"\n{'='*80}")
    print(f"TESTING NAVIGATION STEPS - {'HEADLESS' if headless else 'NON-HEADLESS'}")
    print(f"{'='*80}\n")
    
    scraper = ANBIMAScraper(headless=headless)
    
    try:
        # Step 1: Setup driver
        print("Step 1: Setup driver...", end=" ")
        start = time.time()
        if not scraper.setup_driver():
            print(f"❌ Failed ({time.time()-start:.1f}s)")
            return
        print(f"✓ ({time.time()-start:.1f}s)")
        
        # Step 2: Navigate to base URL
        print("Step 2: Navigate to ANBIMA...", end=" ")
        start = time.time()
        try:
            scraper.driver.get("https://data.anbima.com.br/busca/fundos")
            time.sleep(3)
            print(f"✓ ({time.time()-start:.1f}s)")
        except Exception as e:
            print(f"❌ {str(e)[:50]} ({time.time()-start:.1f}s)")
            return
        
        # Step 3: Find search input
        print("Step 3: Find search input...", end=" ")
        start = time.time()
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            search_input = WebDriverWait(scraper.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Busque fundos']"))
            )
            print(f"✓ ({time.time()-start:.1f}s)")
        except Exception as e:
            print(f"❌ {str(e)[:50]} ({time.time()-start:.1f}s)")
            return
        
        # Step 4: Type CNPJ
        print("Step 4: Type CNPJ...", end=" ")
        start = time.time()
        try:
            search_input.clear()
            search_input.send_keys(test_cnpj)
            time.sleep(2)
            print(f"✓ ({time.time()-start:.1f}s)")
        except Exception as e:
            print(f"❌ {str(e)[:50]} ({time.time()-start:.1f}s)")
            return
        
        # Step 5: Wait for dropdown
        print("Step 5: Wait for dropdown...", end=" ")
        start = time.time()
        try:
            dropdown = WebDriverWait(scraper.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='listbox'], ul[role='listbox']"))
            )
            print(f"✓ ({time.time()-start:.1f}s)")
        except Exception as e:
            print(f"❌ TIMEOUT or NOT FOUND ({time.time()-start:.1f}s)")
            print(f"   Error: {str(e)[:50]}")
            
            # Take screenshot if headless
            if headless:
                scraper.driver.save_screenshot(f"debug_step5_headless_{int(time.time())}.png")
                print(f"   Screenshot saved")
            
            return
        
        # Step 6: Find fund links
        print("Step 6: Find fund links...", end=" ")
        start = time.time()
        try:
            time.sleep(2)
            fund_links = scraper.driver.find_elements(By.CSS_SELECTOR, "article a[href*='/fundos/C']")
            if fund_links:
                print(f"✓ Found {len(fund_links)} link(s) ({time.time()-start:.1f}s)")
            else:
                print(f"❌ No links found ({time.time()-start:.1f}s)")
                return
        except Exception as e:
            print(f"❌ {str(e)[:50]} ({time.time()-start:.1f}s)")
            return
        
        # Step 7: Click first link
        print("Step 7: Click first link...", end=" ")
        start = time.time()
        try:
            fund_links[0].click()
            time.sleep(3)
            print(f"✓ ({time.time()-start:.1f}s)")
        except Exception as e:
            print(f"❌ {str(e)[:50]} ({time.time()-start:.1f}s)")
            return
        
        print(f"\n✓ ALL STEPS COMPLETED SUCCESSFULLY")
        
    finally:
        scraper.close()

if __name__ == '__main__':
    print("Testing HEADLESS mode:")
    test_navigation_steps(headless=True)
    
    print("\n" + "="*80)
    input("Press ENTER to test non-headless...")
    
    print("\nTesting NON-HEADLESS mode:")
    test_navigation_steps(headless=False)

