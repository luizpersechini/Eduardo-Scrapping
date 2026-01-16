"""
Main script for ANBIMA Fund Data Scraper - PARALLEL VERSION
Uses ThreadPoolExecutor to run multiple scrapers simultaneously
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from collections import deque
from tqdm import tqdm
import pandas as pd

import config
from anbima_scraper import ANBIMAScraper
from data_processor import DataProcessor
# Stealth scraper will be imported conditionally if needed


# Global variables for thread-safe operations
results_lock = Lock()
all_results = []
processed_count = 0
success_count = 0
failed_count = 0
start_time = None


class GlobalRateLimiter:
    """
    Thread-safe global rate limiter to coordinate all workers
    Ensures total request rate across all workers stays under threshold
    """

    def __init__(self, max_requests_per_minute: int = 15):
        """
        Initialize rate limiter

        Args:
            max_requests_per_minute: Maximum requests allowed per minute across all workers
        """
        self.max_requests = max_requests_per_minute
        self.requests = []
        self.lock = Lock()
        self.logger = logging.getLogger("RateLimiter")

    def wait_if_needed(self):
        """Block if rate limit would be exceeded"""
        with self.lock:
            now = time.time()
            # Remove requests older than 60 seconds
            self.requests = [req_time for req_time in getattr(self, 'requests', [])
                           if now - req_time < 60]

            # If at limit, wait
            if len(self.requests) >= getattr(config, 'MAX_REQUESTS_PER_MINUTE', 15):
                if self.requests:
                    oldest_request = self.requests[0]
                    wait_time = 60 - (time.time() - oldest_request)
                    if wait_time > 0:
                        logging.info(f"Rate limit reached ({len(self.requests)} req/min). Waiting {wait_time:.1f}s")
                        time.sleep(wait_time)
                        # Clear old requests
                        self.requests = [t for t in self.requests if time.time() - t < 60]

            # Record this request
            self.requests.append(time.time())


# Global rate limiter instance
rate_limiter = GlobalRateLimiter(max_requests_per_minute=15)


def scrape_worker(worker_id: int, cnpj_list: list, headless: bool = True, pbar: tqdm = None, use_stealth: bool = False):
    """
    Worker function that processes a list of CNPJs

    Args:
        worker_id: ID of this worker (for logging)
        cnpj_list: List of CNPJs to process
        headless: Whether to run browser in headless mode
        pbar: Progress bar to update
        use_stealth: Whether to use stealth mode

    Returns:
        List of results
    """
    global all_results, processed_count, success_count, failed_count, start_time, rate_limiter

    logger = logging.getLogger(f"Worker-{worker_id}")
    logger.info(f"Worker {worker_id} starting with {len(cnpj_list)} CNPJs")

    worker_results = []
    worker_success = 0
    worker_failed = 0

    # Initialize scraper for this worker
    if use_stealth:
        from stealth_scraper import StealthANBIMAScraper
        scraper = StealthANBIMAScraper(headless=headless)
    else:
        scraper = ANBIMAScraper(headless=headless)

    if not scraper.setup_driver():
        logger.error(f"Worker {worker_id}: Failed to initialize web driver")
        return []

    logger.info(f"Worker {worker_id}: Web driver initialized successfully")

    try:
        for cnpj in cnpj_list:
            logger.info(f"Worker {worker_id}: Processing {cnpj}")

            # Wait for global rate limiter before making request
            rate_limiter.wait_if_needed()

            # Scrape fund data with retry logic and exponential backoff
            max_retries = config.MAX_RETRIES
            retry_count = 0
            result = None
            base_retry_delay = config.RETRY_DELAY

            while retry_count < max_retries:
                try:
                    result = scraper.scrape_fund_data(cnpj)

                    if result.get("Status") == "Success":
                        logger.info(f"Worker {worker_id}: ✓ Successfully scraped {cnpj}")
                        worker_success += 1
                        break
                    else:
                        error_msg = result.get('Status', 'Unknown error')
                        logger.warning(f"Worker {worker_id}: Failed to scrape {cnpj}: {error_msg}")

                        # Don't retry if CNPJ not found
                        if "not found" in error_msg.lower() or "no results" in error_msg.lower():
                            logger.info(f"Worker {worker_id}: CNPJ not found, skipping retries")
                            worker_failed += 1
                            break

                        # Exponential backoff for rate limiting
                        if "rate limit" in error_msg.lower():
                            if retry_count < max_retries - 1:
                                # Exponential backoff: 60s, 120s, 240s
                                backoff_delay = 60 * (2 ** retry_count)
                                logger.warning(f"Worker {worker_id}: Rate limited! Backing off for {backoff_delay}s (attempt {retry_count + 2}/{max_retries})")
                                time.sleep(backoff_delay)
                            else:
                                worker_failed += 1
                            retry_count += 1
                            continue

                        # Standard retry for other errors
                        if retry_count < max_retries - 1:
                            retry_delay = base_retry_delay * (1.5 ** retry_count)  # Mild exponential increase
                            logger.info(f"Worker {worker_id}: Retrying in {retry_delay:.1f}s... (attempt {retry_count + 2}/{max_retries})")
                            time.sleep(retry_delay)
                        else:
                            worker_failed += 1
                        retry_count += 1

                except Exception as e:
                    logger.error(f"Worker {worker_id}: Error scraping {cnpj}: {str(e)}")
                    if retry_count < max_retries - 1:
                        retry_delay = base_retry_delay * (1.5 ** retry_count)
                        logger.info(f"Worker {worker_id}: Retrying in {retry_delay:.1f}s... (attempt {retry_count + 2}/{max_retries})")
                        time.sleep(retry_delay)
                    else:
                        worker_failed += 1
                    retry_count += 1
                    result = {
                        "CNPJ": cnpj,
                        "Nome do Fundo": "N/A",
                        "periodic_data": [],
                        "Status": f"Error after {max_retries} retries: {str(e)}"
                    }

            if result:
                worker_results.append(result)

                # Update global counters (thread-safe)
                with results_lock:
                    all_results.append(result)
                    processed_count += 1
                    if result.get("Status") == "Success":
                        success_count += 1
                    else:
                        failed_count += 1

                    # Update progress bar
                    if pbar:
                        pbar.update(1)
                        # Calculate statistics
                        elapsed = time.time() - start_time
                        rate = processed_count / elapsed if elapsed > 0 else 0
                        remaining = len(cnpj_list) * 4 - processed_count  # Approximate total
                        eta = remaining / rate if rate > 0 else 0
                        pbar.set_postfix({
                            'success': success_count,
                            'failed': failed_count,
                            'rate': f'{rate:.2f}/s',
                            'eta': f'{eta/60:.1f}min'
                        })

            # Delay between requests - use full delay since we have 1 worker by default now
            time.sleep(config.SLEEP_BETWEEN_REQUESTS)

    finally:
        # Close browser for this worker
        scraper.close()
        logger.info(f"Worker {worker_id}: Finished. Success: {worker_success}, Failed: {worker_failed}")

    return worker_results


def setup_logging():
    """Setup logging configuration"""
    if not os.path.exists(config.LOG_DIR):
        os.makedirs(config.LOG_DIR)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(config.LOG_DIR, f"scraper_parallel_{timestamp}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format=config.LOG_FORMAT,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("="*80)
    logger.info("ANBIMA Fund Data Scraper - PARALLEL MODE Started")
    logger.info(f"Log file: {log_file}")
    logger.info("="*80)
    
    return logger, log_file


def preinitialize_chromedriver(headless: bool = True, use_stealth: bool = False) -> bool:
    """
    Pre-initializes ChromeDriver to avoid race condition when multiple workers start.
    Downloads and installs the driver before workers are created.
    
    Args:
        headless: Whether to use headless mode
        use_stealth: Whether to use stealth mode (undetected-chromedriver)
        
    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*80)
    logger.info(f"PRE-INITIALIZATION: Downloading ChromeDriver ({'STEALTH' if use_stealth else 'STANDARD'} mode)")
    logger.info("="*80)
    
    try:
        if use_stealth:
            from stealth_scraper import StealthANBIMAScraper
            scraper = StealthANBIMAScraper(headless=headless)
        else:
            scraper = ANBIMAScraper(headless=headless)
        
        if scraper.setup_driver():
            logger.info("✅ ChromeDriver downloaded and ready")
            scraper.close()
            return True
        else:
            logger.error("❌ Failed to initialize ChromeDriver")
            return False
    except Exception as e:
        logger.error(f"❌ Error during ChromeDriver pre-initialization: {e}")
        return False


def test_workers(num_workers: int, headless: bool = True, use_stealth: bool = False) -> bool:
    """
    Test if all workers can initialize their drivers successfully.
    
    Args:
        num_workers: Number of workers to test
        headless: Whether to use headless mode
        use_stealth: Whether to use stealth mode (undetected-chromedriver)
        
    Returns:
        True if all workers initialized successfully, False otherwise
    """
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*80)
    logger.info(f"TESTING: Initializing {num_workers} workers ({'STEALTH' if use_stealth else 'STANDARD'} mode)")
    logger.info("="*80)
    
    scrapers = []
    success = True
    
    try:
        # Try to initialize all workers
        for i in range(1, num_workers + 1):
            logger.info(f"  Testing Worker {i}...")
            if use_stealth:
                from stealth_scraper import StealthANBIMAScraper
                scraper = StealthANBIMAScraper(headless=headless)
            else:
                scraper = ANBIMAScraper(headless=headless)
            
            if scraper.setup_driver():
                logger.info(f"  ✅ Worker {i}: Initialized successfully")
                scrapers.append(scraper)
                time.sleep(0.5)  # Small delay between initializations
            else:
                logger.error(f"  ❌ Worker {i}: Failed to initialize")
                success = False
                break
        
        if success:
            logger.info(f"\n✅ ALL {num_workers} WORKERS INITIALIZED SUCCESSFULLY!")
        else:
            logger.error(f"\n❌ WORKER INITIALIZATION FAILED")
            
    finally:
        # Clean up test scrapers
        logger.info("\nCleaning up test workers...")
        for scraper in scrapers:
            try:
                scraper.close()
            except:
                pass
        time.sleep(2)  # Wait for cleanup
    
    logger.info("="*80 + "\n")
    return success


def get_processed_cnpjs(output_file: str) -> set:
    """
    Read already processed CNPJs from existing output file
    
    Args:
        output_file: Path to output file
        
    Returns:
        Set of CNPJs that were successfully processed
    """
    processed = set()
    
    if os.path.exists(output_file):
        try:
            df = pd.read_excel(output_file)
            # The first column after row 2 should be CNPJs (pivot format)
            # Skip header rows and get CNPJs from column names
            if len(df.columns) > 1:
                for col in df.columns[1:]:  # Skip date column
                    if col and str(col) != 'nan':
                        processed.add(str(col))
            logging.info(f"Found {len(processed)} already processed CNPJs in {output_file}")
        except Exception as e:
            logging.warning(f"Could not read existing output file: {e}")
    
    return processed


def scrape_worker(worker_id: int, cnpj_list: list, headless: bool = True, pbar: tqdm = None, use_stealth: bool = False):
    """
    Worker function that processes a list of CNPJs
    
    Args:
        worker_id: ID of this worker (for logging)
        cnpj_list: List of CNPJs to process
        headless: Whether to run browser in headless mode
        pbar: Progress bar to update
        use_stealth: Whether to use stealth mode
        
    Returns:
        List of results
    """
    global all_results, processed_count, success_count, failed_count, start_time
    
    logger = logging.getLogger(f"Worker-{worker_id}")
    logger.info(f"Worker {worker_id} starting with {len(cnpj_list)} CNPJs")
    
    worker_results = []
    worker_success = 0
    worker_failed = 0
    
    # Initialize scraper for this worker
    if use_stealth:
        from stealth_scraper import StealthANBIMAScraper
        scraper = StealthANBIMAScraper(headless=headless)
    else:
        scraper = ANBIMAScraper(headless=headless)
    
    if not scraper.setup_driver():
        logger.error(f"Worker {worker_id}: Failed to initialize web driver")
        return []
    
    logger.info(f"Worker {worker_id}: Web driver initialized successfully")
    
    try:
        for cnpj in cnpj_list:
            logger.info(f"Worker {worker_id}: Processing {cnpj}")

            # Scrape fund data with retry logic and exponential backoff
            max_retries = config.MAX_RETRIES
            retry_count = 0
            result = None
            base_retry_delay = config.RETRY_DELAY

            while retry_count < max_retries:
                try:
                    result = scraper.scrape_fund_data(cnpj)

                    if result.get("Status") == "Success":
                        logger.info(f"Worker {worker_id}: ✓ Successfully scraped {cnpj}")
                        worker_success += 1
                        break
                    else:
                        error_msg = result.get('Status', 'Unknown error')
                        logger.warning(f"Worker {worker_id}: Failed to scrape {cnpj}: {error_msg}")

                        # Don't retry if CNPJ not found
                        if "not found" in error_msg.lower() or "no results" in error_msg.lower():
                            logger.info(f"Worker {worker_id}: CNPJ not found, skipping retries")
                            worker_failed += 1
                            break

                        # Exponential backoff for rate limiting
                        if "rate limit" in error_msg.lower():
                            if retry_count < max_retries - 1:
                                # Exponential backoff: 60s, 120s, 240s
                                backoff_delay = 60 * (2 ** retry_count)
                                logger.warning(f"Worker {worker_id}: Rate limited! Backing off for {backoff_delay}s (attempt {retry_count + 2}/{max_retries})")
                                time.sleep(backoff_delay)
                            else:
                                worker_failed += 1
                            retry_count += 1
                            continue

                        # Standard retry for other errors
                        if retry_count < max_retries - 1:
                            retry_delay = base_retry_delay * (1.5 ** retry_count)  # Mild exponential increase
                            logger.info(f"Worker {worker_id}: Retrying in {retry_delay:.1f}s... (attempt {retry_count + 2}/{max_retries})")
                            time.sleep(retry_delay)
                        else:
                            worker_failed += 1
                        retry_count += 1

                except Exception as e:
                    logger.error(f"Worker {worker_id}: Error scraping {cnpj}: {str(e)}")
                    if retry_count < max_retries - 1:
                        retry_delay = base_retry_delay * (1.5 ** retry_count)
                        logger.info(f"Worker {worker_id}: Retrying in {retry_delay:.1f}s... (attempt {retry_count + 2}/{max_retries})")
                        time.sleep(retry_delay)
                    else:
                        worker_failed += 1
                    retry_count += 1
                    result = {
                        "CNPJ": cnpj,
                        "Nome do Fundo": "N/A",
                        "periodic_data": [],
                        "Status": f"Error after {max_retries} retries: {str(e)}"
                    }

            if result:
                worker_results.append(result)

                # Update global counters (thread-safe)
                with results_lock:
                    all_results.append(result)
                    processed_count += 1
                    if result.get("Status") == "Success":
                        success_count += 1
                    else:
                        failed_count += 1

                    # Update progress bar
                    if pbar:
                        pbar.update(1)
                        # Calculate statistics
                        elapsed = time.time() - start_time
                        rate = processed_count / elapsed if elapsed > 0 else 0
                        remaining = len(cnpj_list) * 4 - processed_count  # Approximate total
                        eta = remaining / rate if rate > 0 else 0
                        pbar.set_postfix({
                            'success': success_count,
                            'failed': failed_count,
                            'rate': f'{rate:.2f}/s',
                            'eta': f'{eta/60:.1f}min'
                        })

            # Delay between requests - use full delay since we have 1 worker by default now
            time.sleep(config.SLEEP_BETWEEN_REQUESTS)
    
    finally:
        # Close browser for this worker
        scraper.close()
        logger.info(f"Worker {worker_id}: Finished. Success: {worker_success}, Failed: {worker_failed}")
    
    return worker_results


def main_parallel(input_file: str = "input_cnpjs.xlsx", 
                 output_file: str = None, 
                 headless: bool = True,
                 num_workers: int = 4,
                 skip_processed: bool = False,
                 use_stealth: bool = False):
    """
    Main execution function with parallel processing
    
    Args:
        input_file: Path to input Excel file with CNPJs
        output_file: Path to output Excel file (auto-generated if None)
        headless: Whether to run browser in headless mode
        num_workers: Number of parallel workers (default: 4)
        skip_processed: Whether to skip already processed CNPJs
        use_stealth: Whether to use stealth mode (undetected-chromedriver)
    """
    global all_results, processed_count, success_count, failed_count, start_time
    
    logger, log_file = setup_logging()
    
    try:
        # Generate output filename if not provided
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"output_anbima_data_parallel_{timestamp}.xlsx"
        
        logger.info(f"Input file: {input_file}")
        logger.info(f"Output file: {output_file}")
        logger.info(f"Headless mode: {headless}")
        logger.info(f"Stealth mode: {use_stealth}")
        logger.info(f"Number of workers: {num_workers}")
        logger.info(f"Skip processed: {skip_processed}")
        
        # Initialize data processor
        processor = DataProcessor()
        
        # Read CNPJs from input file
        logger.info("\n" + "="*80)
        logger.info("Step 1: Reading CNPJs from input file")
        logger.info("="*80)
        
        if not os.path.exists(input_file):
            logger.error(f"Input file not found: {input_file}")
            print(f"\n❌ Error: Input file '{input_file}' not found!")
            return False
        
        cnpjs = processor.read_cnpj_list(input_file)
        
        if not cnpjs:
            logger.error("No CNPJs found in input file")
            print("\n❌ Error: No CNPJs found in input file!")
            return False
        
        print(f"\n✓ Found {len(cnpjs)} CNPJ(s) to process")
        
        # PRE-INITIALIZE ChromeDriver to avoid race condition
        logger.info("\n" + "="*80)
        logger.info("Step 1.5: Pre-initializing ChromeDriver")
        logger.info("="*80)
        
        if not preinitialize_chromedriver(headless, use_stealth):
            logger.error("Failed to pre-initialize ChromeDriver")
            print("\n❌ Error: Failed to pre-initialize ChromeDriver!")
            return False
        
        # TEST workers before starting
        logger.info("\n" + "="*80)
        logger.info(f"Step 1.6: Testing {num_workers} workers")
        logger.info("="*80)
        
        if not test_workers(num_workers, headless, use_stealth):
            logger.error(f"Failed to initialize all {num_workers} workers")
            print(f"\n❌ Error: Not all workers could initialize!")
            print(f"   Try reducing the number of workers or check your system resources.")
            return False
        
        print(f"\n✅ All {num_workers} workers tested successfully!")
        
        # Skip already processed CNPJs if requested
        if skip_processed:
            logger.info("Checking for already processed CNPJs...")
            processed_cnpjs = get_processed_cnpjs(output_file)
            original_count = len(cnpjs)
            cnpjs = [cnpj for cnpj in cnpjs if cnpj not in processed_cnpjs]
            skipped = original_count - len(cnpjs)
            if skipped > 0:
                logger.info(f"Skipping {skipped} already processed CNPJs")
                print(f"✓ Skipping {skipped} already processed CNPJs")
                print(f"✓ Remaining to process: {len(cnpjs)} CNPJs")
        
        if not cnpjs:
            logger.info("All CNPJs already processed!")
            print("\n✓ All CNPJs already processed!")
            return True
        
        # Divide CNPJs among workers
        logger.info("\n" + "="*80)
        logger.info(f"Step 2: Dividing work among {num_workers} workers")
        logger.info("="*80)
        
        chunk_size = len(cnpjs) // num_workers
        remainder = len(cnpjs) % num_workers
        
        cnpj_chunks = []
        start_idx = 0
        for i in range(num_workers):
            # Distribute remainder among first workers
            end_idx = start_idx + chunk_size + (1 if i < remainder else 0)
            chunk = cnpjs[start_idx:end_idx]
            if chunk:  # Only add non-empty chunks
                cnpj_chunks.append(chunk)
                logger.info(f"Worker {i+1} will process {len(chunk)} CNPJs")
            start_idx = end_idx
        
        # Start parallel scraping
        logger.info("\n" + "="*80)
        logger.info(f"Step 3: Starting parallel scraping with {len(cnpj_chunks)} workers")
        logger.info("="*80)
        
        print(f"\n🔍 Scraping data for {len(cnpjs)} fund(s) using {len(cnpj_chunks)} parallel workers...\n")
        
        # Initialize global variables
        all_results = []
        processed_count = 0
        success_count = 0
        failed_count = 0
        start_time = time.time()
        
        # Create progress bar
        pbar = tqdm(total=len(cnpjs), desc="Overall Progress", unit="fund")
        
        # Execute workers in parallel
        with ThreadPoolExecutor(max_workers=len(cnpj_chunks)) as executor:
            # Submit all workers
            futures = []
            for i, chunk in enumerate(cnpj_chunks):
                future = executor.submit(scrape_worker, i+1, chunk, headless, pbar, use_stealth)
                futures.append(future)
            
            # Wait for all workers to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Worker failed with error: {str(e)}")
        
        pbar.close()
        
        total_time = time.time() - start_time
        
        # Process and save results
        logger.info("\n" + "="*80)
        logger.info("Step 4: Processing and saving results")
        logger.info("="*80)
        
        if not all_results:
            logger.error("No results to save")
            print("\n❌ Error: No results were collected!")
            return False
        
        # Process scraped data
        df = processor.process_scraped_data(all_results)
        
        # Save to Excel
        processor.save_results(df, output_file)
        
        # Generate summary report
        summary = processor.create_summary_report(all_results)
        
        # Print summary
        print("\n" + "="*80)
        print("PARALLEL SCRAPING SUMMARY")
        print("="*80)
        print(f"Number of workers: {len(cnpj_chunks)}")
        print(f"Total CNPJs processed: {summary['total_cnpjs']}")
        print(f"Successful: {summary['successful']} ({summary['success_rate']})")
        print(f"Failed: {summary['failed']}")
        print(f"Total time: {total_time/60:.2f} minutes")
        print(f"Average time per CNPJ: {total_time/len(cnpjs):.2f} seconds")
        print(f"Throughput: {len(cnpjs)/(total_time/3600):.2f} CNPJs/hour")
        
        if summary['error_breakdown']:
            print("\nError breakdown:")
            for error, count in summary['error_breakdown'].items():
                print(f"  - {error}: {count}")
        
        print(f"\n✓ Results saved to: {output_file}")
        print(f"✓ Log file saved to: {log_file}")
        print("="*80 + "\n")
        
        logger.info("\n" + "="*80)
        logger.info("ANBIMA Fund Data Scraper - PARALLEL MODE Completed Successfully")
        logger.info(f"Total time: {total_time/60:.2f} minutes")
        logger.info("="*80)
        
        return True
        
    except KeyboardInterrupt:
        logger.warning("\n\nScript interrupted by user")
        print("\n\n⚠️  Script interrupted by user")
        return False
        
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}", exc_info=True)
        print(f"\n❌ Unexpected error: {str(e)}")
        return False


if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="ANBIMA Fund Data Scraper - PARALLEL VERSION")
    parser.add_argument(
        "-i", "--input",
        default="input_cnpjs.xlsx",
        help="Input Excel file with CNPJs (default: input_cnpjs.xlsx)"
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output Excel file (default: auto-generated with timestamp)"
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser in visible mode (default: headless)"
    )
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)"
    )
    parser.add_argument(
        "--skip-processed",
        action="store_true",
        help="Skip already processed CNPJs from output file"
    )
    parser.add_argument(
        "--stealth",
        action="store_true",
        help="Use stealth mode (undetected-chromedriver) to avoid bot detection"
    )
    
    args = parser.parse_args()
    
    # Run main function
    success = main_parallel(
        input_file=args.input,
        output_file=args.output,
        headless=not args.no_headless,
        num_workers=args.workers,
        skip_processed=args.skip_processed,
        use_stealth=args.stealth
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

