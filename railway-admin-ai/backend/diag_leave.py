import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app.core.rule_extractor import RuleExtractor
from collections import Counter

extractor = RuleExtractor()
rules = extractor.extract_rules("app/knowledge/rules.md")

# Find Leave-domain rules and what chapter they are in
print("=== LEAVE DOMAIN RULES ===")
leave_rules = [r for r in rules if r['domain'] == 'Leave']
print(f"Count: {len(leave_rules)}")
ch_counter = Counter(r.get('chapter','') for r in leave_rules)
for ch, c in ch_counter.most_common():
    print(f"  [{c}] {ch}")

# Check all unique chapter names extracted
print("\n=== ALL UNIQUE CHAPTER NAMES IN EXTRACTED RULES ===")
chapters = Counter(r.get('chapter','') for r in rules)
for ch, c in sorted(chapters.items(), key=lambda x: -x[1]):
    dom = Counter(r['domain'] for r in rules if r.get('chapter','') == ch).most_common(1)
    print(f"  [{c:3d}] {ch[:60]} -> {dom[0][0] if dom else 'N/A'}")

# Print a leave-chapter rule's description to understand structure
print("\n=== SAMPLE SERVICE-CHAPTER RULE (to check if it contains leave content) ===")
for r in rules[:5]:
    if 'Chapter XII' in r.get('chapter','') or 'Chapter XIII' in r.get('chapter',''):
        print(f"  [{r['rule_id']}] ch={r['chapter']} | {r['rule_name'][:50]}")
        print(f"  desc: {r['description'][:200]}")
        break
