"""Check for JavaScript-loaded data or JSON structures."""
from bs4 import BeautifulSoup
import re
import json

with open('debug_catalog_page.html', 'r', encoding='utf-8') as f:
    content = f.read()
    soup = BeautifulSoup(content, 'html.parser')

# Check for JSON-LD or embedded JSON
print("Checking for embedded JSON data...")
scripts = soup.find_all('script')
print(f"Found {len(scripts)} script tags")

# Look for JSON in script tags
for i, script in enumerate(scripts[:10]):
    if script.string:
        text = script.string
        # Check if it looks like JSON data
        if 'product' in text.lower() or 'catalog' in text.lower() or 'test' in text.lower():
            if '{' in text and '}' in text:
                print(f"\nScript {i+1} contains JSON-like data:")
                print(text[:500])
                print("...")

# Check for data attributes
print("\n\nChecking for data attributes...")
divs_with_data = soup.find_all('div', attrs=lambda x: x and any(k.startswith('data-') for k in x.keys()))
print(f"Found {len(divs_with_data)} divs with data attributes")

# Check the raw HTML for patterns
print("\n\nChecking for 'product-catalog/view' URLs in raw HTML...")
urls = re.findall(r'/products/product-catalog/view/[^"\'>\s]+', content)
unique_urls = list(set(urls))
print(f"Found {len(unique_urls)} unique product-catalog URLs")
if len(unique_urls) > 0:
    print(f"Sample URLs: {unique_urls[:10]}")


