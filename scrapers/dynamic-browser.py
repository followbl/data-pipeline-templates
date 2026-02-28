"""
Dynamic Browser Scraper Template
Features: Playwright-based, JS rendering, stealth mode, screenshot capture
"""
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

from playwright.sync_api import sync_playwright, Page

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BrowserResult:
    url: str
    content: str
    title: str
    screenshot_path: Optional[str]
    metrics: Dict[str, Any]


class DynamicScraper:
    """Template for JavaScript-rendered content extraction."""
    
    def __init__(
        self,
        headless: bool = True,
        stealth: bool = True,
        viewport: Dict = None,
    ):
        self.headless = headless
        self.stealth = stealth
        self.viewport = viewport or {"width": 1920, "height": 1080}
        self._playwright = None
        self._browser = None
    
    def __enter__(self):
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        return self
    
    def __exit__(self, *args):
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
    
    def _setup_page(self, context) -> Page:
        """Configure page with stealth and viewport."""
        page = context.new_page(viewport=self.viewport)
        
        if self.stealth:
            # Inject stealth scripts to avoid detection
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
        
        # Set timeout defaults
        page.set_default_timeout(30000)
        page.set_default_navigation_timeout(30000)
        
        return page
    
    def scrape(
        self,
        url: str,
        wait_for: Optional[str] = None,
        screenshot: bool = False,
    ) -> Optional[BrowserResult]:
        """Scrape a dynamic page."""
        context = self._browser.new_context()
        page = self._setup_page(context)
        
        try:
            logger.info(f"Navigating to: {url}")
            response = page.goto(url, wait_until="networkidle")
            
            # Wait for specific element if requested
            if wait_for:
                page.wait_for_selector(wait_for)
            
            # Capture metrics
            metrics = {
                "status": response.status if response else None,
                "load_time": page.evaluate("performance.now()"),
            }
            
            # Optional screenshot
            screenshot_path = None
            if screenshot:
                screenshot_path = f"screenshot_{hash(url)}.png"
                page.screenshot(path=screenshot_path, full_page=True)
            
            return BrowserResult(
                url=url,
                content=page.content(),
                title=page.title(),
                screenshot_path=screenshot_path,
                metrics=metrics,
            )
            
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return None
            
        finally:
            context.close()


# Example usage
if __name__ == "__main__":
    with DynamicScraper(headless=True) as scraper:
        result = scraper.scrape(
            "https://httpbin.org/html",
            screenshot=True,
        )
        
        if result:
            print(f"Title: {result.title}")
            print(f"Content length: {len(result.content)}")
