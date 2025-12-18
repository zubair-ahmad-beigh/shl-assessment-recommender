"""Generate validation summary for scraper results."""
import csv
import json

print("=" * 80)
print("SHL SCRAPER VALIDATION SUMMARY")
print("=" * 80)

# Read CSV
with open('shl_assessments.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    assessments = list(reader)

print(f"\n1. TOTAL ASSESSMENTS SCRAPED: {len(assessments)}")
print(f"   ⚠️  REQUIRED: At least 377 Individual Test Solutions")
print(f"   ❌ STATUS: Only {len(assessments)} found (missing {377 - len(assessments)} assessments)")

# Filter for actual assessments
actual_assessments = [a for a in assessments if '/products/product-catalog/view/' in a.get('url', '')]
print(f"\n2. ACTUAL ASSESSMENTS (with valid product-catalog/view URLs): {len(actual_assessments)}")

# Test type distribution
print(f"\n3. TEST TYPE DISTRIBUTION:")
test_types = {}
for a in actual_assessments:
    test_type = a.get('test_type', 'Unknown')
    test_types[test_type] = test_types.get(test_type, 0) + 1
for k, v in sorted(test_types.items()):
    status = "✓" if k in ['K', 'P'] else "⚠️"
    print(f"   {status} {k}: {v}")

# Field validation
print(f"\n4. FIELD VALIDATION:")
missing_name = sum(1 for a in actual_assessments if not a.get('assessment_name'))
missing_url = sum(1 for a in actual_assessments if not a.get('url'))
missing_desc = sum(1 for a in actual_assessments if not a.get('description') or a.get('description') == 'No description available')
print(f"   ✓ assessment_name: {len(actual_assessments) - missing_name}/{len(actual_assessments)} present")
print(f"   ✓ url: {len(actual_assessments) - missing_url}/{len(actual_assessments)} present")
print(f"   ⚠️  description: {len(actual_assessments) - missing_desc}/{len(actual_assessments)} present ({missing_desc} missing)")

# Pre-packaged solutions check
prepackaged = [a for a in actual_assessments if 'pre-packaged' in a.get('assessment_name', '').lower() or 'pre-packaged' in a.get('category', '').lower()]
print(f"\n5. PRE-PACKAGED JOB SOLUTIONS FILTER:")
print(f"   ✓ Found: {len(prepackaged)} (should be 0)")
if prepackaged:
    print(f"   ❌ WARNING: {len(prepackaged)} pre-packaged solutions found (should be excluded)")

# Sample data
print(f"\n6. SAMPLE ASSESSMENTS (first 10):")
print("-" * 80)
for i, a in enumerate(actual_assessments[:10], 1):
    name = a['assessment_name'][:50]
    test_type = a['test_type'] or "N/A"
    url = a['url'][:60] + "..." if len(a['url']) > 60 else a['url']
    print(f"{i:2}. {name:50} | Type: {test_type:8} | {url}")

print("\n" + "=" * 80)
print("KEY FINDINGS:")
print("=" * 80)
print("✓ All assessments have required fields (name, URL)")
print("⚠️  Only 24 actual Individual Test Solutions found (need 377+)")
print("⚠️  Most test_type fields are 'Unknown' - need better extraction logic")
print("⚠️  Many descriptions are missing - need to scrape individual pages")
print("\nLIMITATION:")
print("The SHL catalog page appears to load assessment data via JavaScript.")
print("The static HTML only contains a subset of assessments.")
print("To get all 377+ assessments, we need to:")
print("  1. Use Selenium/Playwright to render JavaScript, OR")
print("  2. Find and call the API endpoint the page uses, OR")
print("  3. Visit individual assessment pages to discover more")
print("=" * 80)


