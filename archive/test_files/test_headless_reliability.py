"""Test reliability of headless vs non-headless mode"""
import time
from anbima_scraper import ANBIMAScraper

def test_mode(headless, num_tests=10):
    """Test scraping reliability in specific mode"""
    results = []
    test_cnpj = '48.330.198/0001-06'
    
    print(f"\n{'='*80}")
    print(f"Testing {'HEADLESS' if headless else 'NON-HEADLESS'} mode - {num_tests} attempts")
    print(f"{'='*80}\n")
    
    for i in range(1, num_tests + 1):
        print(f"Attempt {i}/{num_tests}...", end=" ")
        start = time.time()
        
        scraper = ANBIMAScraper(headless=headless)
        
        try:
            if not scraper.setup_driver():
                results.append({'attempt': i, 'status': 'setup_failed', 'time': 0})
                print("❌ Setup failed")
                continue
            
            result = scraper.scrape_fund_data(test_cnpj)
            elapsed = time.time() - start
            
            status = result.get('Status', 'Unknown')
            data_count = len(result.get('periodic_data', []))
            
            results.append({
                'attempt': i,
                'status': status,
                'data_count': data_count,
                'time': elapsed
            })
            
            if status == 'Success':
                print(f"✓ Success ({data_count} records, {elapsed:.1f}s)")
            else:
                print(f"✗ {status} ({elapsed:.1f}s)")
                
        except Exception as e:
            elapsed = time.time() - start
            results.append({'attempt': i, 'status': f'Exception: {str(e)[:50]}', 'time': elapsed})
            print(f"✗ Exception ({elapsed:.1f}s)")
        finally:
            try:
                scraper.close()
            except:
                pass
        
        # Small delay between attempts
        time.sleep(2)
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY - {'HEADLESS' if headless else 'NON-HEADLESS'}")
    print(f"{'='*80}")
    
    successes = [r for r in results if r['status'] == 'Success']
    timeouts = [r for r in results if 'Timeout' in str(r['status'])]
    failures = [r for r in results if r['status'] not in ['Success'] and 'Timeout' not in str(r['status'])]
    
    print(f"✓ Success: {len(successes)}/{num_tests} ({len(successes)/num_tests*100:.1f}%)")
    print(f"⏱ Timeout: {len(timeouts)}/{num_tests} ({len(timeouts)/num_tests*100:.1f}%)")
    print(f"✗ Other Failures: {len(failures)}/{num_tests}")
    
    if successes:
        avg_time = sum(r['time'] for r in successes) / len(successes)
        print(f"⏰ Avg success time: {avg_time:.1f}s")
    
    if timeouts:
        print(f"\n⚠ Timeout attempts: {[r['attempt'] for r in timeouts]}")
    
    return results

if __name__ == '__main__':
    # Test headless mode
    headless_results = test_mode(headless=True, num_tests=10)
    
    print("\n" + "="*80)
    input("Press ENTER to continue with non-headless tests...")
    print("="*80)
    
    # Test non-headless mode
    non_headless_results = test_mode(headless=False, num_tests=10)
    
    # Final comparison
    print(f"\n{'='*80}")
    print("FINAL COMPARISON")
    print(f"{'='*80}")
    
    h_success = len([r for r in headless_results if r['status'] == 'Success'])
    nh_success = len([r for r in non_headless_results if r['status'] == 'Success'])
    
    print(f"Headless Success Rate: {h_success}/10 ({h_success*10}%)")
    print(f"Non-Headless Success Rate: {nh_success}/10 ({nh_success*10}%)")
    print(f"Difference: {abs(h_success - nh_success)} attempts ({abs(h_success - nh_success)*10}%)")






