"""
Quick check of categories in current processed data
"""
import pandas as pd

# Load processed data
df = pd.read_parquet('../data/processed/warranty_with_predictions.parquet')

print("=" * 80)
print("CURRENT CATEGORIES IN PROCESSED DATA")
print("=" * 80)

# Check rule-based categories
print("\nRule-Based Categories:")
print(df['category_rule_based'].value_counts())

print("\n" + "=" * 80)
print(f"Total unique categories: {df['category_rule_based'].nunique()}")

# Check for network management category
if 'Network Management & Bus Communication' in df['category_rule_based'].values:
    print("✅ Network Management category FOUND!")
    count = (df['category_rule_based'] == 'Network Management & Bus Communication').sum()
    print(f"   Issues in this category: {count}")
else:
    print("❌ Network Management category NOT FOUND")
    print("   This means the model needs to be retrained with the new code.")

# Check the specific issue
print("\n" + "=" * 80)
print("CHECKING SPECIFIC ISSUE: NUSENGCHR18009528")
print("=" * 80)

issue = df[df['issue_number'] == 'NUSENGCHR18009528']
if len(issue) > 0:
    issue = issue.iloc[0]
    print(f"\nIssue found!")
    print(f"  Rule-Based Category: {issue['category_rule_based']}")
    print(f"  Enhanced Type: {issue['issue_type_enhanced']}")
    print(f"  System Area: {issue['system_area']}")
    print(f"  Component: {issue['affected_component']}")
    print(f"  Problem Type: {issue['problem_type']}")
else:
    print("Issue not found in data")

print("\n" + "=" * 80)
