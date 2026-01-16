import logging
import json
from typing import Dict, List, Optional
import config
from parse_bot_client import ParseBotClient

class ParseBotScraper:
    """
    Adapter for Parse.bot to match ANBIMAScraper interface.
    Uses natural language query to instruct the bot.
    """
    
    def __init__(self, headless: bool = True):
        # Headless param is ignored but kept for compatibility
        self.logger = logging.getLogger(__name__)
        try:
            self.client = ParseBotClient()
        except Exception as e:
            self.logger.error(f"Failed to initialize ParseBotClient: {e}")
            self.client = None
            
    def setup_driver(self):
        """Mock setup - verification of client configuration"""
        if not config.PARSE_BOT_API_KEY:
            self.logger.error("PARSE_BOT_API_KEY is missing")
            return False
        if not config.PARSE_BOT_SCRAPER_ID:
            self.logger.warning("PARSE_BOT_SCRAPER_ID is missing. Calls will likely fail.")
            # We return True to allow attempting (maybe user set it in env var or updated config)
            # or maybe we want to fail fast. But for now let's allow.
        return True

    def close(self):
        """No cleanup needed for API client"""
        pass
        
    def scrape_fund_data(self, cnpj: str) -> Dict:
        """
        Scrape fund data using Parse.bot
        """
        result = {
            "CNPJ": cnpj,
            "Nome do Fundo": "N/A",
            "periodic_data": [],
            "Status": "Unknown error"
        }
        
        if not self.client:
            result["Status"] = "Client initialization failed"
            return result
            
        try:
            # Construct the prompt
            prompt = (
                f"Go to {config.ANBIMA_BASE_URL}, search for CNPJ '{cnpj}', "
                "click the result, click 'DADOS PERIÓDICOS' tab. "
                "Extract the 'Fund Name' from the header. "
                "Extract the table with columns 'Data da cotização' and 'Valor cota'. "
                "Return JSON with keys: fund_name, periodic_data (list of {date, value})."
            )
            
            self.logger.info(f"Calling Parse.bot endpoint 'get_fund_data_by_cnpjs' for CNPJ {cnpj}")
            
            # This new endpoint takes a LIST of CNPJs
            payload = {
                "cnpjs": [cnpj]
            }
            
            # Call get_fund_data_by_cnpjs
            api_response = self.client.run_endpoint("get_fund_data_by_cnpjs", payload)
            
            self.logger.info(f"Response: {json.dumps(api_response)[:200]}...")

            if "error" in api_response:
                result["Status"] = f"API Error: {api_response.get('error')}"
                return result
            
            # Extract results
            results_list = api_response.get("results", [])
            
            # RETRY with stripped CNPJ if empty
            if not results_list:
                 import re
                 stripped_cnpj = re.sub(r'\D', '', cnpj)
                 if stripped_cnpj != cnpj:
                     self.logger.info(f"Retrying with stripped CNPJ: {stripped_cnpj}")
                     payload["cnpjs"] = [stripped_cnpj]
                     api_response = self.client.run_endpoint("get_fund_data_by_cnpjs", payload)
                     results_list = api_response.get("results", [])

            # Find our CNPJ in the results
            fund_data = None
            if results_list and len(results_list) > 0:
                # Assuming first result if we sent only one, or match by CNPJ
                fund_data = results_list[0]
                
            if not fund_data:
                result["Status"] = "No data returned for this CNPJ"
                return result
                
            # Extract fields
            result["Nome do Fundo"] = fund_data.get("fund_name", "N/A")
            periodic_data_raw = fund_data.get("periodic_data", [])
            
            parsed_periodic = []
            for item in periodic_data_raw:
                # Map keys: the sample shows 'date' and 'value'
                date_val = item.get("date")
                cota_val = item.get("value")
                
                if date_val and cota_val:
                    parsed_periodic.append({
                        "Data da cotização": date_val,
                        "Valor cota": cota_val
                    })
            
            if parsed_periodic:
                result["periodic_data"] = parsed_periodic
                result["Status"] = "Success"
            else:
                result["Status"] = "No periodic data found"
                
            return result
                
            # Parse the response
            # Note: We need to know the structure of api_response. 
            # Usually it returns what we asked for in JSON.
            # Let's assume the bot follows the instruction to return specific keys.
            
            self.logger.info(f"Received response from Parse.bot: {json.dumps(api_response)[:200]}...")
            
            # Map response to result
            # We might need to adjust this based on actual response structure
            data = api_response.get("data", api_response)
            
            fund_name = data.get("fund_name")
            periodic_data_raw = data.get("periodic_data", [])
            
            if fund_name:
                result["Nome do Fundo"] = fund_name
                
            parsed_periodic = []
            for item in periodic_data_raw:
                # Map keys if needed
                # We asked for {date, value} but let's be flexible
                date_val = item.get("date") or item.get("Data da cotização")
                cota_val = item.get("value") or item.get("Valor cota")
                
                if date_val and cota_val:
                    parsed_periodic.append({
                        "Data da cotização": date_val,
                        "Valor cota": cota_val
                    })
            
            if parsed_periodic:
                result["periodic_data"] = parsed_periodic
                result["Status"] = "Success"
            else:
                result["Status"] = "No data found or parsing failed"
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error in ParseBotScraper: {e}")
            result["Status"] = f"Error: {str(e)}"
            return result

