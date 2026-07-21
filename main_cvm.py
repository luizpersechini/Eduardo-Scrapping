"""
Main script for CVM Fund Quota Ingest
Downloads a month of CVM's inf_diario_fi open data and looks up quotas for a
list of CNPJs — an alternative to scraping ANBIMA for the same numbers,
sourced directly from the regulator's bulk file. Independent of
anbima_scraper.py / main.py.
"""

import argparse
import logging
import os
import sys
from datetime import datetime

import config
import cvm_downloader
import cvm_processor
from data_processor import DataProcessor


def setup_logging():
    """Setup logging configuration"""
    if not os.path.exists(config.LOG_DIR):
        os.makedirs(config.LOG_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(config.LOG_DIR, f"cvm_{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,
        format=config.LOG_FORMAT,
        handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
    )

    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("CVM Fund Quota Ingest Started")
    logger.info(f"Log file: {log_file}")
    logger.info("=" * 80)

    return logger


def main(
    input_file: str = "input_cnpjs.xlsx",
    output_file: str = None,
    month: str = None,
) -> bool:
    """
    Main execution function

    Args:
        input_file: Path to input Excel file with CNPJs
        output_file: Path to output Excel file (auto-generated if None)
        month: Target month as YYYYMM (default: latest published)
    """
    logger = setup_logging()
    processor = DataProcessor()

    logger.info(f"Input file: {input_file}")

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

    try:
        resolved_month = cvm_downloader.resolve_month(month)
        logger.info(f"Target month: {resolved_month}")
        print(f"✓ Target month: {resolved_month}")

        csv_path = cvm_downloader.get_month_csv(resolved_month)
    except Exception as e:
        logger.error(f"Failed to fetch CVM data: {e}", exc_info=True)
        print(f"\n❌ Error fetching CVM data: {e}")
        return False

    df = cvm_processor.load_quotas(csv_path, cnpjs)
    missing = cvm_processor.missing_cnpjs(df, cnpjs)
    if missing:
        logger.warning(f"{len(missing)} CNPJ(s) had no match: {missing}")

    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"output_cvm_{resolved_month}_{timestamp}.xlsx"

    processor.save_results(df, output_file)

    print("\n" + "=" * 80)
    print("CVM INGEST SUMMARY")
    print("=" * 80)
    print(f"Month: {resolved_month}")
    print(f"CNPJs requested: {len(cnpjs)}")
    print(f"CNPJs matched: {len(cnpjs) - len(missing)}")
    if missing:
        print(f"CNPJs not found: {', '.join(missing)}")
    print(f"Rows written: {len(df)}")
    print(f"\n✓ Results saved to: {output_file}")
    print(f"✓ Log file saved to: {config.LOG_DIR}/")
    print("=" * 80 + "\n")

    logger.info("CVM Fund Quota Ingest Completed Successfully")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CVM Fund Quota Ingest")
    parser.add_argument(
        "-i",
        "--input",
        default="input_cnpjs.xlsx",
        help="Input Excel file with CNPJs (default: input_cnpjs.xlsx)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output Excel file (default: auto-generated with month + timestamp)",
    )
    parser.add_argument(
        "-m",
        "--month",
        default=None,
        help="Target month as YYYYMM (default: latest published month)",
    )

    args = parser.parse_args()

    success = main(input_file=args.input, output_file=args.output, month=args.month)

    sys.exit(0 if success else 1)
