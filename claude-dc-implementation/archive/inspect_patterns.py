import json

print("Inspecting loaded patterns...\n")

with open('data/patterns/pattern_report.json') as f:
    patterns = json.load(f)

# Total patterns loaded
print(f"Total patterns loaded: {patterns.get('total_patterns', 0)}\n")

# Pattern counts by category
print("Pattern counts by category:")
for category, count in patterns.get("pattern_count", {}).items():
    print(f"  {category}: {count}")

# Display top patterns
print("\nTop patterns (text, type, source, confidence):")
for p in patterns.get("top_patterns", []):
    print(f"  - {p['text']} ({p['pattern_type']}, {p['source']}, confidence: {p['confidence']})")

# Frequency distribution
print("\nFrequency distribution by pattern type:")
for category, freq in patterns.get("frequency_distribution", {}).items():
    print(f"  {category}: {freq:.2%}")

