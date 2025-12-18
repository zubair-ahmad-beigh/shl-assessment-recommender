"""Script to validate scraper results."""
import csv
import json

# Read CSV
with open('shl_assessments.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    assessments = list(reader)

print(f"Total assessments scraped: {len(assessments)}")
print(f"\nTest Type Distribution:")
test_types = {}
for a in assessments:
    test_type = a.get('test_type', 'Unknown')
    test_types[test_type] = test_types.get(test_type, 0) + 1
for k, v in sorted(test_types.items()):
    print(f"  {k}: {v}")

# Filter for actual assessments (URLs containing product-catalog/view)
actual_assessments = [a for a in assessments if '/product-catalog/view/' in a.get('url', '')]
print(f"\nActual assessments (with product-catalog/view URL): {len(actual_assessments)}")

print("\nSample assessments (first 10):")
for i, a in enumerate(actual_assessments[:10], 1):
    print(f"{i}. {a['assessment_name'][:60]:60} | Type: {a['test_type']:8} | URL: {a['url'][:70]}")

# Check for required fields
print("\n\nField validation:")
missing_fields = 0
for a in actual_assessments:
    if not a.get('assessment_name') or not a.get('url'):
        missing_fields += 1
print(f"Assessments with missing required fields: {missing_fields}")

# Check for pre-packaged solutions
prepackaged = [a for a in actual_assessments if 'pre-packaged' in a.get('assessment_name', '').lower() or 'pre-packaged' in a.get('category', '').lower()]
print(f"Pre-packaged solutions found: {len(prepackaged)}")


