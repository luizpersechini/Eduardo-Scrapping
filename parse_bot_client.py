import requests
import logging
import json
import time
from typing import Dict, Any, Optional

import config

logger = logging.getLogger(__name__)

class ParseBotClient:
    """Client for interacting with Parse.bot API"""
    
    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None, scraper_id: Optional[str] = None):
        self.api_key = api_key or config.PARSE_BOT_API_KEY
        self.api_url = api_url or config.PARSE_BOT_API_URL
        self.scraper_id = scraper_id or config.PARSE_BOT_SCRAPER_ID
        
        if not self.api_key:
            raise ValueError("PARSE_BOT_API_KEY is not set")
            
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
    def query_scraper(self, prompt: str, url: str) -> Dict[str, Any]:
        """
        Send a natural language query/instruction to the scraper
        
        Args:
            prompt: The instruction prompt
            url: The target URL
            
        Returns:
            Dict containing the response data
        """
        if not self.scraper_id:
            logger.warning("PARSE_BOT_SCRAPER_ID is not set. API calls may fail.")
            
        endpoint = f"{self.api_url}/scraper/{self.scraper_id}/query"
        
        payload = {
            "prompt": prompt,
            "url": url
        }
        
        try:
            logger.info(f"Sending query to Parse.bot: {endpoint}")
            logger.debug(f"Payload: {json.dumps(payload)}")
            
            response = requests.post(endpoint, headers=self.headers, json=payload, timeout=120)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Parse.bot API error: {response.status_code} - {response.text}")
                return {"error": response.text, "status": response.status_code}
                
        except Exception as e:
            logger.error(f"Error calling Parse.bot API: {e}")
            return {"error": str(e), "status": "exception"}

    def run_endpoint(self, endpoint_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a specific endpoint of the scraper
        """
        if not self.scraper_id:
            logger.warning("PARSE_BOT_SCRAPER_ID is not set.")
            
        url = f"{self.api_url}/scraper/{self.scraper_id}/{endpoint_name}"
        
        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=120)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.text, "status": response.status_code}
        except Exception as e:
            return {"error": str(e), "status": "exception"}




