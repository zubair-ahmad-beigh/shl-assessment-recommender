"""Find where the assessment data is actually stored."""
from bs4 import BeautifulSoup
import re
import json

with open('debug_catalog_page.html', 'r', encoding='utf-8') as f:
    content = f.read()
    soup = BeautifulSoup(content, 'html.parser')

# Check for window.__INITIAL_STATE__ or similar data structures
print("Looking for JavaScript data structures...")
data_patterns = [
    r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
    r'window\.__DATA__\s*=\s*({.+?});',
    r'products\s*[:=]\s*(\[[^\]]+\])',
    r'assessments\s*[:=]\s*(\[[^\]]+\])',
]

for pattern in data_patterns:
    matches = re.findall(pattern, content, re.DOTALL)
    if matches:
        print(f"\nFound matches for pattern: {pattern[:50]}")
        print(f"Number of matches: {len(matches)}")
        if matches:
            print(f"First match preview: {matches[0][:500]}")

# Check for JSON in script tags more carefully
print("\n\nChecking script tags for JSON data...")
scripts = soup.find_all('script')
for i, script in enumerate(scripts):
    if script.string and ('product' in script.string.lower() or 'catalog' in script.string.lower()):
        # Try to find JSON objects
        text = script.string
        # Look for array patterns
        array_matches = re.findall(r'\[[^\]]{100,}\],?\s*\]', text)
        if array_matches:
            print(f"\nScript {i+1} contains potential array data")
            print(f"Found {len(array_matches)} array-like structures")

# Check for data attributes that might contain URLs
print("\n\nChecking for data attributes with URLs...")
elements_with_data = soup.find_all(attrs=lambda x: x and any('catalog' in str(v).lower() or 'product' in str(v).lower() 
                                                              for v in (x.values() if hasattr(x, 'values') else [])))
print(f"Found {len(elements_with_data)} elements with catalog/product in attributes")


