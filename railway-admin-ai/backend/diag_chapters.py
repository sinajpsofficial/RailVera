import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app.core.rule_extractor import RuleExtractor
from collections import Counter

extractor = RuleExtractor()
rules = extractor.extract_rules("app/knowledge/rules.md")

# Show all unique chapter titles and their domains
chapter_domains = {}
for r in rules:
    ch = r.get('chapter', 'None') or 'None'
    domain = r['domain']
    if ch not in chapter_domains:
        chapter_domains[ch] = Counter()
    chapter_domains[ch][domain] += 1

print("Chapter -> Domain assignments:")
for chapter, domains in sorted(chapter_domains.items()):
    top = domains.most_common(1)[0]
    total = sum(domains.values())
    print(f"  [{total:3d}] {chapter[:70]}")
    print(f"         domain={top[0]}")

# What content lands in General
print("\nGeneral-domain rules (first 8):")
gen_rules = [r for r in rules if r['domain'] == 'General'][:8]
for r in gen_rules:
    print(f"  {r['rule_id']} | ch={r.get('chapter','')[:40]} | {r['rule_name'][:50]}")
