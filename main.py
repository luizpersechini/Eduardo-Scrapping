"""
Main script for ANBIMA Fund Data Scraper
Orchestrates the scraping workflow
"""

import os
import sys
import time
import logging
from datetime import datetime
from tqdm import tqdm

import config
from anbima_scraper import ANBIMAScraper
from data_processor import DataProcessor


def setup_logging():
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    if not os.path.exists(config.LOG_DIR):
        os.makedirs(config.LOG_DIR)
    
    # Create log file path with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(config.LOG_DIR, f"scraper_{timestamp}.log")
    
    # Configure logging
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
    logger.info("ANBIMA Fund Data Scraper Started")
    logger.info(f"Log file: {log_file}")
    logger.info("="*80)
    
    return logger


def main(input_file: str = "input_cnpjs.xlsx", output_file: str = None, headless: bool = True):
    """
    Main execution function
    
    Args:
        input_file: Path to input Excel file with CNPJs
        output_file: Path to output Excel file (auto-generated if None)
        headless: Whether to run browser in headless mode
    """
    logger = setup_logging()
    
    try:
        # Generate output filename if not provided
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"output_anbima_data_{timestamp}.xlsx"
        
        logger.info(f"Input file: {input_file}")
        logger.info(f"Output file: {output_file}")
        logger.info(f"Headless mode: {headless}")
        
        # Initialize data processor
        processor = DataProcessor()
        
        # Read CNPJs from input file
        logger.info("\n" + "="*80)
        logger.info("Step 1: Reading CNPJs from input file")
        logger.info("="*80)
        
        if not os.path.exists(input_file):
            logger.error(f"Input file not found: {input_file}")
            print(f"\n❌ Error: Input file '{input_file}' not found!")
            print(f"Please create an Excel file with a column named '{config.INPUT_COLUMN_CNPJ}'")
            return False
        
        cnpjs = processor.read_cnpj_list(input_file)
        
        if not cnpjs:
            logger.error("No CNPJs found in input file")
            print("\n❌ Error: No CNPJs found in input file!")
            return False
        
        print(f"\n✓ Found {len(cnpjs)} CNPJ(s) to process")
        
        # Initialize scraper
        logger.info("\n" + "="*80)
        logger.info("Step 2: Initializing web scraper")
        logger.info("="*80)
        
        scraper = ANBIMAScraper(headless=headless)
        
        if not scraper.setup_driver():
            logger.error("Failed to initialize web driver")
            print("\n❌ Error: Failed to initialize web driver!")
            print("Please make sure Chrome is installed on your system.")
            return False
        
        print("✓ Web scraper initialized successfully")
        
        # Scrape data for each CNPJ
        logger.info("\n" + "="*80)
        logger.info("Step 3: Scraping fund data")
        logger.info("="*80)
        
        results = []
        
        print(f"\n🔍 Scraping data for {len(cnpjs)} fund(s)...\n")
        
        try:
            for idx, cnpj in enumerate(tqdm(cnpjs, desc="Progress", unit="fund")):
                logger.info(f"\n{'='*80}")
                logger.info(f"Processing CNPJ {idx+1}/{len(cnpjs)}: {cnpj}")
                logger.info(f"{'='*80}")
                
                # Scrape fund data with retry logic
                max_retries = config.MAX_RETRIES
                retry_count = 0
                result = None
                
                while retry_count < max_retries:
                    try:
                        result = scraper.scrape_fund_data(cnpj)
                        
                        if result.get("Status") == "Success":
                            logger.info(f"✓ Successfully scraped data for {cnpj}")
                            break
                        else:
                            logger.warning(f"Failed to scrape {cnpj}: {result.get('Status')}")
                            if retry_count < max_retries - 1:
                                logger.info(f"Retrying... (attempt {retry_count + 2}/{max_retries})")
                                time.sleep(config.RETRY_DELAY)
                            retry_count += 1
                    
                    except Exception as e:
                        logger.error(f"Error scraping {cnpj}: {str(e)}")
                        if retry_count < max_retries - 1:
                            logger.info(f"Retrying... (attempt {retry_count + 2}/{max_retries})")
                            time.sleep(config.RETRY_DELAY)
                        retry_count += 1
                        result = {
                            "CNPJ": cnpj,
                            "Nome do Fundo": "N/A",
                            "periodic_data": [],
                            "Status": f"Error after {max_retries} retries: {str(e)}"
                        }
                
                if result:
                    results.append(result)
                
                # Add delay between requests to avoid rate limiting
                if idx < len(cnpjs) - 1:  # Don't wait after the last one
                    time.sleep(config.SLEEP_BETWEEN_REQUESTS)
        
        finally:
            # Always close the browser
            scraper.close()
        
        # Process and save results
        logger.info("\n" + "="*80)
        logger.info("Step 4: Processing and saving results")
        logger.info("="*80)
        
        if not results:
            logger.error("No results to save")
            print("\n❌ Error: No results were collected!")
            return False
        
        # Process scraped data
        df = processor.process_scraped_data(results)
        
        # Save to Excel
        processor.save_results(df, output_file)
        
        # Generate summary report
        summary = processor.create_summary_report(results)
        
        # Print summary
        print("\n" + "="*80)
        print("SCRAPING SUMMARY")
        print("="*80)
        print(f"Total CNPJs processed: {summary['total_cnpjs']}")
        print(f"Successful: {summary['successful']} ({summary['success_rate']})")
        print(f"Failed: {summary['failed']}")
        
        if summary['error_breakdown']:
            print("\nError breakdown:")
            for error, count in summary['error_breakdown'].items():
                print(f"  - {error}: {count}")
        
        print(f"\n✓ Results saved to: {output_file}")
        print(f"✓ Log file saved to: {config.LOG_DIR}/")
        print("="*80 + "\n")
        
        logger.info("\n" + "="*80)
        logger.info("ANBIMA Fund Data Scraper Completed Successfully")
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
    parser = argparse.ArgumentParser(description="ANBIMA Fund Data Scraper")
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
    
    args = parser.parse_args()
    
    # Run main function
    success = main(
        input_file=args.input,
        output_file=args.output,
        headless=not args.no_headless
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

