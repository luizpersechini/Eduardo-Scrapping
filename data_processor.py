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
                self.logger.warning(f"Column '{config.INPUT_COLUMN_CNPJ}' not found. Trying to auto-detect...")
                
                # Look for columns with CNPJ pattern (XX.XXX.XXX/XXXX-XX)
                import re
                cnpj_pattern = re.compile(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}')
                
                for col in df.columns:
                    # Check if column name looks like a CNPJ
                    if cnpj_pattern.match(str(col)):
                        self.logger.info(f"Found CNPJs in column: {col}")
                        # First CNPJ is the column name, rest are in the column
                        cnpjs = [str(col)] + df[col].astype(str).tolist()
                        cnpjs = [cnpj.strip() for cnpj in cnpjs if cnpj and cnpj.strip() and cnpj.lower() != 'nan']
                        self.logger.info(f"Found {len(cnpjs)} CNPJs to process (including column name)")
                        return cnpjs
                
                raise ValueError(f"Column '{config.INPUT_COLUMN_CNPJ}' not found and could not auto-detect CNPJs")
            
            # Extract CNPJs and convert to string
            cnpjs = df[config.INPUT_COLUMN_CNPJ].astype(str).tolist()
            
            # Clean CNPJs (remove NaN, empty strings)
            cnpjs = [cnpj.strip() for cnpj in cnpjs if cnpj and cnpj.strip() and cnpj.lower() != 'nan']
            
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
                        date_value, cota_value = self._extract_date_and_value(data_entry)
                        all_data.append({
                            "Data da cotização": date_value,
                            "CNPJ": cnpj,
                            "Valor cota": cota_value
                        })
            
            if not all_data:
                self.logger.warning("No periodic data to process")
                return pd.DataFrame()
            
            # Create DataFrame
            df = pd.DataFrame(all_data)
            
            # Pivot table: dates as rows, CNPJs as columns
            pivot_df = df.pivot_table(
                index='Data da cotização',
                columns='CNPJ',
                values='Valor cota',
                aggfunc='first'
            )
            
            # Reset index to make 'Data da cotização' a column
            pivot_df = pivot_df.reset_index()
            
            # Create multi-row header with fund names
            header_data = {}
            header_data['Data da cotização'] = ['', 'Data da cotização']
            
            for cnpj in pivot_df.columns[1:]:  # Skip 'Data da cotização' column
                fund_name = fund_names.get(cnpj, 'N/A')
                header_data[cnpj] = [fund_name, 'Valor cota']
            
            # Create header DataFrame
            header_df = pd.DataFrame(header_data)
            
            # Concatenate header with data
            final_df = pd.concat([header_df, pivot_df], ignore_index=True)
            
            self.logger.info(f"Processed into pivot format: {len(pivot_df)} dates × {len(pivot_df.columns)-1} funds")
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
            
            # Save to Excel
            df.to_excel(output_file, index=False, engine='openpyxl')
            
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
            "success_rate": f"{(successful/total*100):.1f}%" if total > 0 else "0%",
            "error_breakdown": error_types
        }
        
        return summary

