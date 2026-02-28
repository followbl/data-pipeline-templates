"""
Basic HTTP Scraper Template
Features: Retries, exponential backoff, user-agent rotation, structured logging
"""
import logging
import random
import time
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
]


@dataclass
class ScrapedItem:
    url: str
    data: Dict[str, Any]
    timestamp: float
    status_code: int


class BasicScraper:
    """Template for robust HTTP scraping."""
    
    def __init__(
        self,
        base_url: str,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        rate_limit_delay: float = 1.0,
    ):
        self.base_url = base_url
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
    
    def fetch(self, path: str = "") -> Optional[ScrapedItem]:
        """Fetch a URL with full error handling."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            
            # Rate limiting
            time.sleep(self.rate_limit_delay)
            
            return ScrapedItem(
                url=url,
                data={"content": response.text, "headers": dict(response.headers)},
                timestamp=time.time(),
                status_code=response.status_code,
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def fetch_multiple(self, paths: List[str]) -> List[ScrapedItem]:
        """Fetch multiple paths, returning only successful results."""
        results = []
        for path in paths:
            if item := self.fetch(path):
                results.append(item)
        return results


# Example usage
if __name__ == "__main__":
    scraper = BasicScraper("https://httpbin.org")
    result = scraper.fetch("/json")
    
    if result:
        print(f"Success: {result.url} (status {result.status_code})")
    else:
        print("Failed to fetch")
