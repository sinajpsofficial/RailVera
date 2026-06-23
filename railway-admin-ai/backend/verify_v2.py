from app.core.rule_extractor import RuleExtractor
from collections import Counter

extractor = RuleExtractor()
rules = extractor.extract_rules("app/knowledge/rules.md")

print(f"Total rules extracted: {len(rules)}")

domains = Counter(r['domain'] for r in rules)
print("\nDomain breakdown:")
for d, c in sorted(domains.items(), key=lambda x: -x[1]):
    print(f"  {d:<22}: {c}")

with_conditions = sum(1 for r in rules if r['eligibility_conditions'])
with_documents  = sum(1 for r in rules if r['required_documents'])
with_disqual    = sum(1 for r in rules if r['disqualifying_conditions'])
with_exceptions = sum(1 for r in rules if r['exceptions'])
with_authority  = sum(1 for r in rules if r['authority'])

print(f"\nField quality:")
print(f"  eligibility_conditions : {with_conditions}/{len(rules)} ({with_conditions/len(rules)*100:.0f}%)")
print(f"  required_documents     : {with_documents}/{len(rules)} ({with_documents/len(rules)*100:.0f}%)")
print(f"  disqualifiers          : {with_disqual}/{len(rules)} ({with_disqual/len(rules)*100:.0f}%)")
print(f"  exceptions             : {with_exceptions}/{len(rules)} ({with_exceptions/len(rules)*100:.0f}%)")
print(f"  authority              : {with_authority}/{len(rules)} ({with_authority/len(rules)*100:.0f}%)")
