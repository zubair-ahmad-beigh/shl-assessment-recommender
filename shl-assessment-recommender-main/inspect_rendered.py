"""Inspect the rendered HTML to understand page structure."""
from bs4 import BeautifulSoup
import re

with open('debug_rendered_page.html', 'r', encoding='utf-8') as f:
    html = f.read()
    soup = BeautifulSoup(html, 'html.parser')

# Count product-catalog URLs
urls = re.findall(r'/products/product-catalog/view/[^"\'>\s\)]+', html)
unique_urls = sorted(set(urls))
print(f"Found {len(unique_urls)} unique product-catalog URLs in rendered HTML")
print(f"\nFirst 30 URLs:")
for i, url in enumerate(unique_urls[:30], 1):
    print(f"{i}. {url}")

# Check for tables
tables = soup.find_all('table')
print(f"\n\nFound {len(tables)} tables")
for i, table in enumerate(tables[:3], 1):
    rows = table.find_all('tr')
    print(f"\nTable {i}: {len(rows)} rows")
    if rows:
        headers = [th.get_text(strip=True) for th in rows[0].find_all(['th', 'td'])]
        print(f"  Headers: {headers}")
        print(f"  First data row: {rows[1].get_text(strip=True)[:100]}")

# Check for JavaScript data
print("\n\nChecking for embedded JavaScript data...")
scripts = soup.find_all('script')
for i, script in enumerate(scripts):
    if script.string and ('product' in script.string.lower() or 'assessment' in script.string.lower()):
        # Look for JSON arrays or objects
        if '{' in script.string and '[' in script.string:
            print(f"\nScript {i} contains JSON-like data")
            # Try to find array of objects
            matches = re.findall(r'\[.*?\{.*?\}.*?\]', script.string[:2000], re.DOTALL)
            if matches:
                print(f"  Found {len(matches)} potential JSON arrays")
                print(f"  Preview: {matches[0][:200]}")

# Check for data attributes
print("\n\nChecking for elements with data attributes...")
elements_with_data = soup.find_all(attrs=lambda x: x and isinstance(x, dict) and any('data' in str(k).lower() for k in x.keys()))
print(f"Found {len(elements_with_data)} elements with data attributes")


