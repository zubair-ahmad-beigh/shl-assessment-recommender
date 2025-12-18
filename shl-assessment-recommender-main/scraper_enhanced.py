"""
Enhanced scraper that tries multiple strategies to find all assessments.
"""
from scraper import SHLScraper
from playwright.sync_api import sync_playwright, Page
import json
import re
import logging

logger = logging.getLogger(__name__)

class EnhancedSHLScraper(SHLScraper):
    """Enhanced scraper with additional discovery strategies."""
    
    def discover_all_assessments(self, page: Page) -> list:
        """Try multiple strategies to discover all assessment URLs."""
        all_urls = set()
        
        # Strategy 1: Extract from rendered HTML (existing method)
        logger.info("Strategy 1: Extracting from rendered HTML...")
        assessments = self.extract_assessments_from_page(page)
        for a in assessments:
            all_urls.add(a['url'])
        logger.info(f"Found {len(all_urls)} URLs from HTML")
        
        # Strategy 2: Try to find and click "View All" or similar buttons
        logger.info("Strategy 2: Looking for 'View All' or pagination...")
        try:
            # Look for buttons that might load more content
            selectors = [
                'button:has-text("View All")',
                'button:has-text("Show All")',
                'a:has-text("View All")',
                'a:has-text("Show All")',
                '[data-action="load-more"]',
                '.load-more',
                '.view-all'
            ]
            
            for selector in selectors:
                try:
                    elements = page.locator(selector)
                    count = elements.count()
                    if count > 0:
                        logger.info(f"Found {count} elements matching '{selector}'")
                        for i in range(min(count, 3)):
                            elements.nth(i).click(timeout=5000)
                            page.wait_for_timeout(3000)
                            # Re-extract after clicking
                            new_assessments = self.extract_assessments_from_page(page)
                            for a in new_assessments:
                                all_urls.add(a['url'])
                except:
                    pass
        except Exception as e:
            logger.debug(f"Error in Strategy 2: {e}")
        
        # Strategy 3: Check for JSON data in script tags
        logger.info("Strategy 3: Checking for JSON data in scripts...")
        html = page.content()
        soup = self._get_soup(html)
        scripts = soup.find_all('script', type='application/json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                urls = self._extract_urls_from_json(data)
                all_urls.update(urls)
            except:
                pass
        
        # Also check regular script tags for embedded data
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and ('product' in script.string.lower() or 'catalog' in script.string.lower()):
                # Try to extract URLs from JavaScript
                urls = re.findall(r'/products/product-catalog/view/[a-zA-Z0-9\-]+/', script.string)
                for url in urls:
                    full_url = f"https://www.shl.com{url}"
                    all_urls.add(full_url)
        
        logger.info(f"Strategy 3 found {len(all_urls) - len([a for a in assessments])} additional URLs")
        
        # Strategy 4: Try sitemap or robots.txt
        logger.info("Strategy 4: Checking sitemap...")
        try:
            sitemap_urls = [
                'https://www.shl.com/sitemap.xml',
                'https://www.shl.com/robots.txt',
                'https://www.shl.com/sitemap_index.xml'
            ]
            for sitemap_url in sitemap_urls:
                try:
                    response = page.goto(sitemap_url, wait_until='domcontentloaded', timeout=10000)
                    if response and response.ok:
                        content = page.content()
                        urls = re.findall(r'/products/product-catalog/view/[a-zA-Z0-9\-]+/', content)
                        for url in urls:
                            full_url = f"https://www.shl.com{url}"
                            all_urls.add(full_url)
                        logger.info(f"Found {len(urls)} URLs in {sitemap_url}")
                        break
                except:
                    pass
        except Exception as e:
            logger.debug(f"Error in Strategy 4: {e}")
        
        return list(all_urls)
    
    def _get_soup(self, html):
        """Helper to get BeautifulSoup object."""
        from bs4 import BeautifulSoup
        return BeautifulSoup(html, 'html.parser')
    
    def _extract_urls_from_json(self, data, urls=None):
        """Recursively extract URLs from JSON data."""
        if urls is None:
            urls = set()
        
        if isinstance(data, dict):
            for key, value in data.items():
                if key in ['url', 'href', 'link'] and isinstance(value, str) and '/products/product-catalog/view/' in value:
                    urls.add(value)
                else:
                    self._extract_urls_from_json(value, urls)
        elif isinstance(data, list):
            for item in data:
                self._extract_urls_from_json(item, urls)
        elif isinstance(data, str) and '/products/product-catalog/view/' in data:
            urls.add(data)
        
        return urls

# This approach still won't work if the page truly only has 24 assessments.
# The real solution might be that we need to accept this limitation OR
# the assessments are accessed differently (via search, categories, etc.)


