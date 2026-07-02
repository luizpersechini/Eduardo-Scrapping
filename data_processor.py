"""
Data Processing Module
Handles Excel I/O and data transformation
"""

import pandas as pd
import logging
from typing import List, Dict
from datetime import datetime
import os

import config


# ── Output cleaning helpers (shared with cvm_processor) ────────────────────
# Eduardo's cosmetic requests for the Excel output:
#   1. dates as real dd/mm/yyyy dates (so Excel doesn't need "Text to Columns")
#   2. drop the "R$ " prefix and leave the quota as a plain number

_EMPTY = ("", "-", "—", "n/a", "nan", "none")


def brl_to_number(value):
    """'R$ 1.234,56' → 1234.56, '439,648005' → 439.648005, blank/'-' → None.

    Handles Brazilian formatting ('.' thousands, ',' decimal) and strips the
    'R$' currency prefix. Returns the original value untouched if it can't be
    parsed, so unexpected text is never silently lost.
    """
    if value is None or isinstance(value, (int, float)):
        return value
    t = str(value).replace("R$", "").replace("\xa0", " ").strip()
    if t.lower() in _EMPTY:
        return None
    cleaned = t.replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return value


def to_date(value):
    """Parse 'dd/mm/yyyy' (or dd/mm/yy, or ISO yyyy-mm-dd) to a datetime so the
    Excel cell is a real date. Returns the original value if unparseable."""
    if value is None or isinstance(value, datetime):
        return value
    s = str(value).strip()
    if not s or s.lower() in _EMPTY:
        return value
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    try:
        return pd.to_datetime(s, dayfirst=True).to_pydatetime()
    except Exception:
        return value


class DataProcessor:
    """Handles reading input Excel and writing output Excel"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def read_cnpj_list(self, input_file: str) -> List[str]:
        """
        Read CNPJs from input Excel file

        Args:
            input_file: Path to input Excel file

        Returns:
            List of CNPJ strings
        """
        try:
            self.logger.info(f"Reading CNPJs from {input_file}")

            # Read Excel file
            df = pd.read_excel(input_file)

            # Check if CNPJ column exists
            if config.INPUT_COLUMN_CNPJ not in df.columns:
                # Try to find a column with CNPJ-like values
                self.logger.warning(
                    f"Column '{config.INPUT_COLUMN_CNPJ}' not found. Trying to auto-detect..."
                )

                # Look for columns with CNPJ pattern (XX.XXX.XXX/XXXX-XX)
                import re

                cnpj_pattern = re.compile(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}")

                for col in df.columns:
                    # Check if column name looks like a CNPJ
                    if cnpj_pattern.match(str(col)):
                        self.logger.info(f"Found CNPJs in column: {col}")
                        # First CNPJ is the column name, rest are in the column
                        cnpjs = [str(col)] + df[col].astype(str).tolist()
                        cnpjs = [
                            cnpj.strip()
                            for cnpj in cnpjs
                            if cnpj and cnpj.strip() and cnpj.lower() != "nan"
                        ]
                        self.logger.info(
                            f"Found {len(cnpjs)} CNPJs to process (including column name)"
                        )
                        return cnpjs

                raise ValueError(
                    f"Column '{config.INPUT_COLUMN_CNPJ}' not found and could not auto-detect CNPJs"
                )

            # Extract CNPJs and convert to string
            cnpjs = df[config.INPUT_COLUMN_CNPJ].astype(str).tolist()

            # Clean CNPJs (remove NaN, empty strings)
            cnpjs = [
                cnpj.strip()
                for cnpj in cnpjs
                if cnpj and cnpj.strip() and cnpj.lower() != "nan"
            ]

            self.logger.info(f"Found {len(cnpjs)} CNPJs to process")
            return cnpjs

        except Exception as e:
            self.logger.error(f"Error reading CNPJ list: {str(e)}")
            raise

    def process_scraped_data(self, results: List[Dict]) -> pd.DataFrame:
        """
        Process scraped data into pivot table format (dates as rows, CNPJs as columns)

        Args:
            results: List of scraping results from ANBIMAScraper

        Returns:
            DataFrame in pivot format with multi-row header
        """
        try:
            self.logger.info("Processing scraped data into pivot format...")

            # Collect all data and fund names
            all_data = []
            fund_names = {}  # CNPJ -> Nome do Fundo

            for result in results:
                cnpj = result.get("CNPJ", "N/A")
                fund_name = result.get("Nome do Fundo", "N/A")
                periodic_data = result.get("periodic_data", [])

                fund_names[cnpj] = fund_name

                if periodic_data and isinstance(periodic_data, list):
                    for data_entry in periodic_data:
                        date_value, cota_value = self._extract_date_and_value(
                            data_entry
                        )
                        all_data.append(
                            {
                                # real date (chronological sort + no "Text to
                                # Columns" in Excel) and a plain number (no "R$ ")
                                "Data da cotização": to_date(date_value),
                                "CNPJ": cnpj,
                                "Valor cota": brl_to_number(cota_value),
                            }
                        )

            if not all_data:
                self.logger.warning("No periodic data to process")
                return pd.DataFrame()

            # Create DataFrame
            df = pd.DataFrame(all_data)

            # Pivot table: dates as rows, CNPJs as columns
            pivot_df = df.pivot_table(
                index="Data da cotização",
                columns="CNPJ",
                values="Valor cota",
                aggfunc="first",
            )

            # Reset index to make 'Data da cotização' a column
            pivot_df = pivot_df.reset_index()

            # Create multi-row header with fund names
            header_data = {}
            header_data["Data da cotização"] = ["", "Data da cotização"]

            for cnpj in pivot_df.columns[1:]:  # Skip 'Data da cotização' column
                fund_name = fund_names.get(cnpj, "N/A")
                header_data[cnpj] = [fund_name, "Valor cota"]

            # Create header DataFrame
            header_df = pd.DataFrame(header_data)

            # Concatenate header with data
            final_df = pd.concat([header_df, pivot_df], ignore_index=True)

            self.logger.info(
                f"Processed into pivot format: {len(pivot_df)} dates × {len(pivot_df.columns) - 1} funds"
            )
            return final_df

        except Exception as e:
            self.logger.error(f"Error processing scraped data: {str(e)}")
            raise

    def _extract_date_and_value(self, data_entry: Dict) -> tuple:
        """
        Extract date and value from a periodic data entry

        Args:
            data_entry: Dict containing periodic data

        Returns:
            Tuple of (date_string, value_string)
        """
        # The data_entry should already have the correct format from the scraper
        # with keys "Data da cotização" and "Valor cota"
        date_value = data_entry.get("Data da cotização", "N/A")
        cota_value = data_entry.get("Valor cota", "N/A")

        return date_value, cota_value

    # The 6 FIDC periodic columns, in output order. Must match the keys produced
    # by StealthANBIMAScraper.extract_fidc_periodic_data().
    FIDC_PERIODIC_COLUMNS = [
        "Data competência",
        "Valor patrimônio líquido",
        "Valor cota",
        "Valor volume total de aplicação",
        "Valor volume total de resgates",
        "Número total de cotistas",
    ]

    def process_fidc_data(self, results: List[Dict]) -> pd.DataFrame:
        """
        Flatten FIDC scrape results into a single long/tidy DataFrame.

        Input shape (per CNPJ) — from StealthANBIMAScraper.scrape_fidc_data():
            {
              "CNPJ": str, "Status": str,
              "subclasses": [
                 {"subclasse_name": str, "subclasse_code": str,
                  "periodic_data": [ {<6 FIDC column keys>: str}, ... ]},
                 ...
              ]
            }

        Output columns (one row per subclasse × competência date):
            CNPJ | Subclasse | Código | Data competência |
            Valor patrimônio líquido | Valor cota |
            Valor volume total de aplicação | Valor volume total de resgates |
            Número total de cotistas
        """
        try:
            self.logger.info("Processing FIDC data into long/tidy format...")
            rows = []
            for result in results:
                cnpj = result.get("CNPJ", "N/A")
                for sub in result.get("subclasses", []) or []:
                    name = sub.get("subclasse_name", "N/A")
                    code = sub.get("subclasse_code", "N/A")
                    for entry in sub.get("periodic_data", []) or []:
                        row = {
                            "CNPJ": cnpj,
                            "Subclasse": name,
                            "Código": code,
                        }
                        for col in self.FIDC_PERIODIC_COLUMNS:
                            row[col] = entry.get(col, "")
                        rows.append(row)

            columns = ["CNPJ", "Subclasse", "Código"] + self.FIDC_PERIODIC_COLUMNS
            if not rows:
                self.logger.warning("No FIDC periodic data to process")
                return pd.DataFrame(columns=columns)

            df = pd.DataFrame(rows, columns=columns)

            # Cosmetic cleanup: real date + plain numbers (no "R$ ").
            if not df.empty:
                df["Data competência"] = df["Data competência"].map(to_date)
                for col in (
                    "Valor patrimônio líquido",
                    "Valor cota",
                    "Valor volume total de aplicação",
                    "Valor volume total de resgates",
                ):
                    df[col] = df[col].map(brl_to_number)
                # Number of shareholders → integer
                df["Número total de cotistas"] = pd.to_numeric(
                    df["Número total de cotistas"]
                    .astype(str)
                    .str.replace(r"[.\s\xa0]", "", regex=True),
                    errors="coerce",
                ).astype("Int64")

            self.logger.info(
                f"Processed FIDC data: {len(df)} rows across "
                f"{df['Código'].nunique()} subclass(es)"
            )
            return df

        except Exception as e:
            self.logger.error(f"Error processing FIDC data: {str(e)}")
            raise

    @staticmethod
    def write_excel(df: pd.DataFrame, target) -> None:
        """Write `df` to Excel (a path or a file-like buffer) forcing dd/mm/yyyy
        display for real date cells. Use this everywhere instead of df.to_excel
        so every output — regular, FIDC, CVM — shows dates the Brazilian way.

        The `datetime_format` writer option only styles pure datetime columns.
        The regular-scrape pivot keeps its date column as `object` dtype (string
        header rows sit above the dates), so pandas skips it and openpyxl falls
        back to an ISO format. To cover every shape, we also walk the written
        cells and stamp DD/MM/YYYY on any that hold a real date/datetime."""
        with pd.ExcelWriter(
            target,
            engine="openpyxl",
            datetime_format="DD/MM/YYYY",
            date_format="DD/MM/YYYY",
        ) as writer:
            df.to_excel(writer, index=False)
            for ws in writer.book.worksheets:
                for row in ws.iter_rows():
                    for cell in row:
                        if isinstance(cell.value, datetime):
                            cell.number_format = "DD/MM/YYYY"

    def save_results(self, df: pd.DataFrame, output_file: str):
        """
        Save results to Excel file

        Args:
            df: DataFrame with results
            output_file: Path to output Excel file
        """
        try:
            self.logger.info(f"Saving results to {output_file}")

            # Create output directory if it doesn't exist
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            self.write_excel(df, output_file)

            self.logger.info(f"Successfully saved {len(df)} rows to {output_file}")

        except Exception as e:
            self.logger.error(f"Error saving results: {str(e)}")
            raise

    def create_summary_report(self, results: List[Dict]) -> Dict:
        """
        Create a summary report of the scraping results

        Args:
            results: List of scraping results

        Returns:
            Dict with summary statistics
        """
        total = len(results)
        successful = sum(1 for r in results if r.get("Status") == "Success")
        failed = total - successful

        # Count different error types
        error_types = {}
        for r in results:
            status = r.get("Status", "Unknown")
            if status != "Success":
                error_types[status] = error_types.get(status, 0) + 1

        summary = {
            "total_cnpjs": total,
            "successful": successful,
            "failed": failed,
            "success_rate": f"{(successful / total * 100):.1f}%" if total > 0 else "0%",
            "error_breakdown": error_types,
        }

        return summary
