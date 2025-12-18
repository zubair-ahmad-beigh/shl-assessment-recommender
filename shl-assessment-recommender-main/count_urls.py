"""Count product-catalog URLs in HTML."""
import re

with open('debug_catalog_page.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all product-catalog URLs
urls = re.findall(r'/products/product-catalog/view/[^"\'\\s\\)]+', content)
unique_urls = sorted(set(urls))

print(f"Found {len(unique_urls)} unique product-catalog URLs")
print("\nFirst 30 URLs:")
for i, url in enumerate(unique_urls[:30], 1):
    print(f"{i}. {url}")



