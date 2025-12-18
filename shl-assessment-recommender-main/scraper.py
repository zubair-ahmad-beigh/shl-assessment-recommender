"""
SHL Product Catalog Scraper
Category-driven aggregation to extract all Individual Test Solutions.
"""

import csv
import json
import time
import re
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse
import logging

try:
    from playwright.sync_api import sync_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SHLScraper:
    """Category-driven scraper for SHL Individual Test Solutions using Playwright."""
    
    BASE_URL = "https://www.shl.com"
    CATALOG_URL = "https://www.shl.com/solutions/products/product-catalog/"
    
    def __init__(self):
        self.assessments = []
        self.seen_urls: Set[str] = set()
        self.category_stats = {}
    
    def extract_test_type(self, text: str) -> Optional[str]:
        """Extract test type (K or P) from text."""
        if not text:
            return None
        text_upper = text.upper()
        
        # Knowledge/Skills indicators (K)
        knowledge_keywords = [
            'KNOWLEDGE', 'SKILLS', 'COGNITIVE', 'ABILITY', 'APTITUDE',
            'REASONING', 'VERBAL', 'NUMERICAL', 'LOGICAL', 'ANALYTICAL',
            'TECHNICAL', 'CODING', 'PROGRAMMING', 'SKILL', 'COMPREHENSION',
            'CRITICAL THINKING', 'PROBLEM SOLVING', 'ANALYSIS', 'MATH',
            'ENGLISH', 'LANGUAGE', 'COMPUTER', 'SOFTWARE'
        ]
        
        # Personality/Behavior indicators (P)
        personality_keywords = [
            'PERSONALITY', 'BEHAVIOR', 'BEHAVIOURAL', 'TRAIT', 'MOTIVATION',
            'VALUES', 'PREFERENCES', 'STYLE', 'TEMPERAMENT', 'CHARACTER',
            'INTERPERSONAL', 'SOCIAL', 'EMOTIONAL'
        ]
        
        # Check for explicit K or P indicators
        if 'K' in text_upper and 'P' not in text_upper and len(text_upper) < 10:
            return 'K'
        if 'P' in text_upper and 'K' not in text_upper and len(text_upper) < 10:
            return 'P'
        
        # Check keywords
        for keyword in personality_keywords:
            if keyword in text_upper:
                return 'P'
        
        for keyword in knowledge_keywords:
            if keyword in text_upper:
                return 'K'
        
        return None
    
    def infer_test_type_from_name(self, name: str, description: str = "") -> str:
        """Infer test type from assessment name and description."""
        combined = (name + " " + description).upper()
        
        # Personality/Behavior patterns
        if any(kw in combined for kw in ['PERSONALITY', 'BEHAVIOR', 'BEHAVIOURAL', 'TRAIT', 
                                         'MOTIVATION', 'VALUES', 'TEMPERAMENT', 'STYLE',
                                         'INTERPERSONAL', 'SOCIAL', 'EMOTIONAL']):
            return 'P'
        
        # Knowledge/Skills patterns
        if any(kw in combined for kw in ['REASONING', 'VERBAL', 'NUMERICAL', 'LOGICAL', 
                                         'ANALYTICAL', 'TECHNICAL', 'CODING', 'PROGRAMMING',
                                         'SKILL', 'KNOWLEDGE', 'ABILITY', 'APTITUDE',
                                         'COMPREHENSION', 'CRITICAL THINKING', 'ASSESSMENT',
                                         'MATH', 'ENGLISH', 'LANGUAGE', 'COMPUTER']):
            return 'K'
        
        return "Unknown"
    
    def extract_categories(self, page: Page) -> List[Dict]:
        """Extract category and subcategory links from the main catalog page."""
        logger.info("Extracting categories from catalog page...")
        categories = []
        seen_urls = set()
        
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Focus on product/assessment category pages
        # Look for links under /products/assessments/ which typically contain assessment listings
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            if not href:
                continue
            
            # Focus on assessment-related category pages
            # Skip assessment detail pages
            if '/products/product-catalog/view/' in href:
                continue
            
            # Skip main catalog page
            if href in ['/solutions/products/product-catalog/', '/solutions/products/product-catalog']:
                continue
            
            # Look for assessment category pages
            # Common patterns:
            # - /products/assessments/[category]/
            # - /solutions/[solution-type]/
            if '/products/assessments/' in href or '/products/assessments' in href:
                full_url = urljoin(self.BASE_URL, href)
                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    categories.append({
                        'name': text.strip() if text else 'Assessment Category',
                        'url': full_url,
                        'type': 'assessment_category'
                    })
        
        # Also look for solution category pages that might contain assessments
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            if not href:
                continue
            
            # Look for solution pages
            if '/solutions/talent-acquisition/' in href or '/solutions/talent-management/' in href:
                full_url = urljoin(self.BASE_URL, href)
                if full_url not in seen_urls and '/view/' not in href:
                    seen_urls.add(full_url)
                    categories.append({
                        'name': text.strip() if text else 'Solution Category',
                        'url': full_url,
                        'type': 'solution_category'
                    })
        
        logger.info(f"Found {len(categories)} category links to explore")
        return categories
    
    def extract_assessments_from_page(self, page: Page, category_name: str = "") -> List[Dict]:
        """Extract all assessment cards/links from the current page."""
        assessments = []
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Strategy 1: Find all links to product-catalog/view (most reliable)
        all_links = soup.find_all('a', href=re.compile(r'/products/product-catalog/view/'))
        
        # Strategy 2: Also check for assessment cards/items that might have different structures
        # Look for cards, tiles, or list items that contain assessment information
        assessment_cards = soup.find_all(['div', 'article', 'li'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['card', 'tile', 'item', 'product', 'assessment']
        ))
        
        # Extract links from cards
        for card in assessment_cards:
            link = card.find('a', href=re.compile(r'/products/product-catalog/view/'))
            if link:
                all_links.append(link)
        
        logger.info(f"Found {len(all_links)} assessment links on page")
        
        for link in all_links:
            href = link.get('href', '')
            if not href or '/products/product-catalog/view/' not in href:
                continue
            
            # Skip Pre-packaged Job Solutions
            link_text = link.get_text(strip=True).lower()
            if 'pre-packaged' in link_text or 'job solution' in link_text.lower():
                continue
            
            full_url = urljoin(self.BASE_URL, href)
            
            # Deduplicate by URL
            if full_url in self.seen_urls:
                continue
            
            self.seen_urls.add(full_url)
            
            # Extract assessment name
            name = link.get_text(strip=True)
            if not name or len(name) < 3:
                continue
            
            # Skip if name suggests Pre-packaged
            if 'pre-packaged' in name.lower():
                continue
            
            # Try to extract description from nearby elements
            description = ""
            parent = link.parent
            if parent:
                parent_text = parent.get_text(strip=True)
                if parent_text and name in parent_text:
                    remaining = parent_text.replace(name, "").strip()
                    if len(remaining) > 20:
                        description = remaining
                
                # Check next siblings
                next_sibling = parent.find_next_sibling()
                if next_sibling:
                    sibling_text = next_sibling.get_text(strip=True)
                    if sibling_text and len(sibling_text) > 20:
                        description = sibling_text
            
            # Try to extract test_type from table if available
            test_type = None
            category = category_name
            
            # Look for table row containing this link
            row = link.find_parent('tr')
            if row:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 4:
                    test_type_cell = cells[-1].get_text(strip=True)
                    if not category:
                        category = test_type_cell
                    if test_type_cell:
                        test_type = self.extract_test_type(test_type_cell)
            
            # Infer test type if not found
            if not test_type or test_type == "Unknown":
                test_type = self.infer_test_type_from_name(name, description)
            
            assessment = {
                'assessment_name': name,
                'description': description or "No description available",
                'test_type': test_type,
                'category': category,
                'url': full_url
            }
            
            assessments.append(assessment)
        
        return assessments
    
    def scrape_category_page(self, page: Page, category_url: str, category_name: str) -> List[Dict]:
        """Scrape a category page for assessments."""
        try:
            logger.info(f"Scraping category: {category_name} ({category_url})")
            page.goto(category_url, wait_until='domcontentloaded', timeout=60000)
            time.sleep(8)  # Wait for JavaScript to load content
            
            # Scroll multiple times to trigger lazy loading
            for i in range(5):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                page.evaluate("window.scrollBy(0, -300)")
                time.sleep(1)
            
            # Final scroll to bottom
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(3)
            
            # Extract assessments
            assessments = self.extract_assessments_from_page(page, category_name)
            logger.info(f"Found {len(assessments)} assessments in category '{category_name}'")
            
            # Update category stats
            if category_name not in self.category_stats:
                self.category_stats[category_name] = 0
            self.category_stats[category_name] += len(assessments)
            
            return assessments
        except Exception as e:
            logger.warning(f"Error scraping category page {category_url}: {e}")
            return []
    
    def scrape_individual_page(self, page: Page, url: str) -> Optional[Dict]:
        """Scrape an individual assessment page for detailed information."""
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(2)
            
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract description from meta tag
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '') if meta_desc else ""
            
            # Try to get description from main content
            if not description or len(description) < 20:
                main_content = soup.find('main') or soup.find('article') or \
                              soup.find('div', class_=re.compile(r'content|description|intro', re.I))
                if main_content:
                    paragraphs = main_content.find_all('p')
                    if paragraphs:
                        description = ' '.join([p.get_text(strip=True) for p in paragraphs[:3]])
            
            return {
                'description': description.strip() if description else None
            }
        except Exception as e:
            logger.debug(f"Error scraping individual page {url}: {e}")
            return None
    
    def scrape(self, min_assessments: int = 377) -> List[Dict]:
        """Main scraping method using category-driven aggregation."""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is not installed. Please install it with: "
                "pip install playwright && playwright install chromium"
            )
        
        logger.info("Starting category-driven SHL catalog scrape...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            try:
                # Step 1: Load main catalog page and extract categories
                logger.info("Loading main catalog page...")
                page.goto(self.CATALOG_URL, wait_until='domcontentloaded', timeout=90000)
                time.sleep(8)
                
                # Also extract assessments from main page
                main_assessments = self.extract_assessments_from_page(page, "Main Catalog")
                self.assessments.extend(main_assessments)
                logger.info(f"Found {len(main_assessments)} assessments on main catalog page")
                
                # Extract category links
                categories = self.extract_categories(page)
                logger.info(f"Found {len(categories)} category links to explore")
                
                # Step 2: Visit each category page and extract assessments
                for i, category in enumerate(categories, 1):
                    if len(self.assessments) >= min_assessments:
                        logger.info(f"Reached target of {min_assessments} assessments, stopping category scraping")
                        break
                    
                    logger.info(f"Processing category {i}/{len(categories)}: {category['name']}")
                    category_assessments = self.scrape_category_page(
                        page, 
                        category['url'], 
                        category['name']
                    )
                    
                    # Deduplicate and add (strict deduplication by URL)
                    new_count = 0
                    for assessment in category_assessments:
                        if assessment['url'] not in self.seen_urls:
                            self.seen_urls.add(assessment['url'])
                            self.assessments.append(assessment)
                            new_count += 1
                    
                    if new_count > 0:
                        logger.info(f"Added {new_count} new assessments (total: {len(self.assessments)})")
                    
                    time.sleep(1)  # Rate limiting
                
                # Step 3: If we still don't have enough, discover more categories from visited pages
                if len(self.assessments) < min_assessments:
                    logger.info(f"Found {len(self.assessments)} assessments, discovering more category pages...")
                    discovered_categories = []
                    
                    # Re-visit main catalog page to find more category links we might have missed
                    try:
                        page.goto(self.CATALOG_URL, wait_until='domcontentloaded', timeout=60000)
                        time.sleep(5)
                        html = page.content()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Look for all links to assessment/product pages (broader search)
                        all_category_links = soup.find_all('a', href=re.compile(r'/products/assessments/'))
                        for link in all_category_links:
                            href = link.get('href', '')
                            if '/view/' not in href:
                                full_url = urljoin(self.BASE_URL, href)
                                if full_url not in [c['url'] for c in categories + discovered_categories]:
                                    discovered_categories.append({
                                        'name': link.get_text(strip=True) or 'Discovered Category',
                                        'url': full_url,
                                        'type': 'discovered'
                                    })
                    except Exception as e:
                        logger.warning(f"Error discovering additional categories: {e}")
                    
                    # Process discovered categories
                    for category in discovered_categories:
                        if len(self.assessments) >= min_assessments:
                            break
                        
                        category_assessments = self.scrape_category_page(
                            page, 
                            category['url'], 
                            category['name']
                        )
                        
                        new_count = 0
                        for assessment in category_assessments:
                            if assessment['url'] not in self.seen_urls:
                                self.seen_urls.add(assessment['url'])
                                self.assessments.append(assessment)
                                new_count += 1
                        
                        if new_count > 0:
                            logger.info(f"Added {new_count} new assessments from discovered category (total: {len(self.assessments)})")
                        
                        time.sleep(1)
                
                # Step 4: Optionally enrich descriptions by visiting individual pages
                # Limit to avoid too many requests
                if self.assessments:
                    logger.info("Enriching assessments with detailed descriptions...")
                    for i, assessment in enumerate(self.assessments[:100]):
                        if assessment['description'] == "No description available":
                            page_data = self.scrape_individual_page(page, assessment['url'])
                            if page_data and page_data.get('description'):
                                assessment['description'] = page_data['description']
                            
                            # Update test_type based on enriched description
                            if assessment['test_type'] == "Unknown":
                                inferred = self.infer_test_type_from_name(
                                    assessment['assessment_name'], 
                                    assessment['description']
                                )
                                if inferred != "Unknown":
                                    assessment['test_type'] = inferred
                        
                        if (i + 1) % 20 == 0:
                            logger.info(f"Enriched {i + 1}/{min(len(self.assessments), 100)} assessments")
                        
                        time.sleep(1)  # Rate limiting
                
            finally:
                browser.close()
        
        logger.info(f"Total assessments scraped: {len(self.assessments)}")
        return self.assessments
    
    def save_to_csv(self, filename: str = "shl_assessments.csv"):
        """Save scraped assessments to CSV."""
        if not self.assessments:
            logger.warning("No assessments to save")
            return
        
        # Filter out Pre-packaged Job Solutions
        filtered = [
            a for a in self.assessments 
            if 'pre-packaged' not in a.get('assessment_name', '').lower() and
               'pre-packaged' not in a.get('category', '').lower() and
               'job solution' not in a.get('assessment_name', '').lower()
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['assessment_name', 'description', 'test_type', 'category', 'url']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(filtered)
        
        logger.info(f"Saved {len(filtered)} assessments to {filename}")
    
    def save_to_json(self, filename: str = "shl_assessments.json"):
        """Save scraped assessments to JSON."""
        if not self.assessments:
            logger.warning("No assessments to save")
            return
        
        # Filter out Pre-packaged Job Solutions
        filtered = [
            a for a in self.assessments 
            if 'pre-packaged' not in a.get('assessment_name', '').lower() and
               'pre-packaged' not in a.get('category', '').lower() and
               'job solution' not in a.get('assessment_name', '').lower()
        ]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(filtered, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(filtered)} assessments to {filename}")


def main():
    """Main function to run the scraper."""
    scraper = SHLScraper()
    
    try:
        assessments = scraper.scrape(min_assessments=377)
        
        # Filter for Individual Test Solutions
        individual_solutions = [
            a for a in assessments 
            if '/products/product-catalog/view/' in a.get('url', '') and
               'pre-packaged' not in a.get('assessment_name', '').lower() and
               'job solution' not in a.get('assessment_name', '').lower()
        ]
        
        if individual_solutions:
            scraper.save_to_csv()
            scraper.save_to_json()
            
            # Print validation summary
            print(f"\n{'='*80}")
            print("SCRAPER VALIDATION SUMMARY")
            print(f"{'='*80}")
            print(f"Total Individual Test Solutions: {len(individual_solutions)}")
            print(f"Target: >= 377")
            print(f"Status: {'[OK]' if len(individual_solutions) >= 377 else '[INCOMPLETE]'}")
            
            print(f"\nCategory-wise counts:")
            for category, count in sorted(scraper.category_stats.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {category}: {count}")
            
            print(f"\nTest Type Distribution:")
            test_types = {}
            for a in individual_solutions:
                test_type = a.get('test_type', 'Unknown')
                test_types[test_type] = test_types.get(test_type, 0) + 1
            
            for k, v in sorted(test_types.items()):
                print(f"  - {k}: {v}")
            
            # Check for Pre-packaged solutions
            prepackaged = [a for a in individual_solutions if 'pre-packaged' in a.get('assessment_name', '').lower()]
            print(f"\nPre-packaged Job Solutions found: {len(prepackaged)} (should be 0)")
            
            print(f"\n{'='*80}")
        else:
            print("[ERROR] Failed to scrape assessments")
    
    except Exception as e:
        logger.error(f"Scraper failed: {e}", exc_info=True)
        print(f"\n[ERROR] Error: {e}")


if __name__ == "__main__":
    main()
