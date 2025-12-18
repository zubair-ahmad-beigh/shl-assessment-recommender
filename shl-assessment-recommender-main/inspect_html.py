"""Inspect HTML structure to improve scraper."""
from bs4 import BeautifulSoup

with open('debug_catalog_page.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

tables = soup.find_all('table')
print(f"Found {len(tables)} tables\n")

for i, table in enumerate(tables[:5], 1):
    rows = table.find_all('tr')
    if len(rows) > 0:
        headers = [th.get_text(strip=True) for th in rows[0].find_all(['th', 'td'])]
        print(f"Table {i}:")
        print(f"  Headers: {headers}")
        print(f"  Total rows: {len(rows)}")
        print(f"  Data rows: {len(rows)-1}")
        
        # Show first few data rows
        if len(rows) > 1:
            print(f"  First data row cells:")
            first_row_cells = rows[1].find_all(['td', 'th'])
            for j, cell in enumerate(first_row_cells[:5], 1):
                text = cell.get_text(strip=True)[:80]
                link = cell.find('a')
                link_text = f" [LINK: {link.get('href', '')[:50]}]" if link else ""
                print(f"    Cell {j}: {text}{link_text}")
        print()

# Check for Individual Test Solutions section
print("\nLooking for 'Individual Test Solutions' section:")
section_headers = soup.find_all(['h1', 'h2', 'h3', 'h4'], string=lambda text: text and 'individual' in text.lower() and 'test' in text.lower())
print(f"Found {len(section_headers)} matching headers")
for header in section_headers[:3]:
    print(f"  - {header.name}: {header.get_text(strip=True)}")


