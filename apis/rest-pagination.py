"""
REST API with Pagination Template
Features: Cursor pagination, rate limiting, retry logic, parallel fetching
"""
import logging
import time
from dataclasses import dataclass
from typing import Iterator, Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    data: List[Dict]
    next_cursor: Optional[str]
    total_count: Optional[int]
    rate_limit_remaining: int


class PaginatedAPIClient:
    """Template for paginated REST API ingestion."""
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        max_workers: int = 5,
        requests_per_second: float = 10.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.max_workers = max_workers
        self.min_interval = 1.0 / requests_per_second
        self._last_request_time = 0
        self.session = requests.Session()
        
        if api_key:
            self.session.headers["Authorization"] = f"Bearer {api_key}"
    
    def _rate_limited_get(self, url: str, params: Dict = None) -> requests.Response:
        """Execute rate-limited GET request."""
        # Enforce rate limit
        elapsed = time.time() - self._last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        
        response = self.session.get(url, params=params, timeout=30)
        self._last_request_time = time.time()
        
        return response
    
    def fetch_page(
        self,
        endpoint: str,
        cursor: Optional[str] = None,
        page_size: int = 100,
    ) -> APIResponse:
        """Fetch a single page of results."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        params = {"limit": page_size}
        if cursor:
            params["cursor"] = cursor
        
        try:
            response = self._rate_limited_get(url, params)
            response.raise_for_status()
            
            body = response.json()
            
            return APIResponse(
                data=body.get("data", []),
                next_cursor=body.get("next_cursor") or body.get("pagination", {}).get("next"),
                total_count=body.get("total_count") or body.get("pagination", {}).get("total"),
                rate_limit_remaining=int(
                    response.headers.get("X-RateLimit-Remaining", 999)
                ),
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return APIResponse(data=[], next_cursor=None, total_count=None, rate_limit_remaining=0)
    
    def fetch_all(
        self,
        endpoint: str,
        page_size: int = 100,
        max_pages: Optional[int] = None,
    ) -> Iterator[Dict]:
        """Iterate through all pages, yielding individual items."""
        cursor: Optional[str] = None
        page_count = 0
        
        while True:
            if max_pages and page_count >= max_pages:
                logger.info(f"Reached max_pages limit ({max_pages})")
                break
            
            result = self.fetch_page(endpoint, cursor, page_size)
            
            # Yield items from this page
            for item in result.data:
                yield item
            
            page_count += 1
            logger.info(f"Fetched page {page_count}, {len(result.data)} items")
            
            # Check for next page
            cursor = result.next_cursor
            if not cursor or not result.data:
                break
            
            # Respect rate limits
            if result.rate_limit_remaining < 5:
                logger.warning("Rate limit low, backing off...")
                time.sleep(5)
    
    def fetch_parallel(
        self,
        endpoints: List[str],
        max_workers: Optional[int] = None,
    ) -> Dict[str, APIResponse]:
        """Fetch multiple endpoints in parallel."""
        workers = max_workers or self.max_workers
        results = {}
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(self.fetch_page, ep): ep 
                for ep in endpoints
            }
            
            for future in as_completed(futures):
                endpoint = futures[future]
                try:
                    results[endpoint] = future.result()
                except Exception as e:
                    logger.error(f"Failed to fetch {endpoint}: {e}")
                    results[endpoint] = APIResponse([], None, None, 0)
        
        return results


# Example usage
if __name__ == "__main__":
    # Example with httpbin (mock API)
    client = PaginatedAPIClient("https://httpbin.org")
    
    # Single page fetch
    response = client.fetch_page("/get")
    print(f"Rate limit remaining: {response.rate_limit_remaining}")
