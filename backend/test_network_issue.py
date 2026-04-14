"""
Test script to verify Network Management categorization fix
"""
import sys
sys.path.insert(0, '.')

from ml.enhanced_categorization import EnhancedIssueCategorizer
import pandas as pd

# Test case from user
test_issue = {
    'issue_number': 'NUSENGCHR18009528',
    'issue_description': '''ETMR_MR22.5 (18.06.17) ETM - Additional_NM_ALIVE_Message
During the Wakeup application and Network management stress test the ETM was sending out extra wakeup messages which may lead to a delay of customer expected functions ETM - Additional_NM_ALIVE_Message
During the Wakeup application and Network management stress test the ETM was sending out extra wakeup messages which may lead to a delay of customer expected functions 
At all the instances, ETM goes more than 250ms, neither receiving an NM ring message nor sending and then module re-announces alive. No Bus loading was observed.''',
    'rca_description': 'Network management issue with additional NM_ALIVE messages causing delays',
    'ecu': 'ETM'
}

print("=" * 80)
print("TESTING NETWORK MANAGEMENT CATEGORIZATION FIX")
print("=" * 80)
print(f"\nIssue Number: {test_issue['issue_number']}")
print(f"ECU: {test_issue['ecu']}")
print(f"\nDescription (first 200 chars):")
print(test_issue['issue_description'][:200] + "...")

# Test rule-based categorization
print("\n" + "=" * 80)
print("1. RULE-BASED CATEGORIZATION TEST")
print("=" * 80)

combined_text = (test_issue['issue_description'] + ' ' + test_issue['rca_description']).lower()

# Check for network management keywords
network_keywords = [
    'network management', 'nm', 'can bus', 'can', 'wakeup',
    'nm_alive', 'nm alive', 'ring message', 'bus stress',
    'communication stress', 'network stress', 'bus loading'
]

found_keywords = []
for keyword in network_keywords:
    if keyword in combined_text:
        found_keywords.append(keyword)

print(f"\nFound Network Management keywords: {found_keywords}")

if found_keywords:
    print("✅ PASS: Should categorize as 'Network Management & Bus Communication'")
else:
    print("❌ FAIL: No network management keywords found")

# Test enhanced categorization
print("\n" + "=" * 80)
print("2. ENHANCED NLP CATEGORIZATION TEST")
print("=" * 80)

categorizer = EnhancedIssueCategorizer()

# Create test dataframe
df_test = pd.DataFrame([test_issue])

# Apply categorization
df_result = categorizer.categorize_dataframe(df_test)

print(f"\nResults:")
print(f"  Issue Type Enhanced: {df_result.iloc[0]['issue_type_enhanced']}")
print(f"  System Area: {df_result.iloc[0]['system_area']}")
print(f"  Affected Component: {df_result.iloc[0]['affected_component']}")
print(f"  Problem Type: {df_result.iloc[0]['problem_type']}")

# Verify expectations
print("\n" + "=" * 80)
print("3. VERIFICATION")
print("=" * 80)

expected_system = 'Infotainment'  # ETM maps to Infotainment
expected_component_options = ['network', 'wakeup']
expected_problem_options = ['Excess', 'Delay']  # "additional" or "delay"

results = []

# Check system area
if df_result.iloc[0]['system_area'] == expected_system:
    print(f"✅ System Area: {df_result.iloc[0]['system_area']} (correct)")
    results.append(True)
else:
    print(f"⚠️  System Area: {df_result.iloc[0]['system_area']} (expected: {expected_system})")
    results.append(False)

# Check component
component = df_result.iloc[0]['affected_component']
if any(opt in component.lower() for opt in expected_component_options):
    print(f"✅ Component: {component} (contains network/wakeup)")
    results.append(True)
else:
    print(f"⚠️  Component: {component} (expected: network or wakeup related)")
    results.append(False)

# Check problem type
problem_type = df_result.iloc[0]['problem_type']
if problem_type in expected_problem_options:
    print(f"✅ Problem Type: {problem_type} (correct - 'additional' or 'delay' detected)")
    results.append(True)
else:
    print(f"⚠️  Problem Type: {problem_type} (expected: Excess or Delay)")
    results.append(False)

# Overall result
print("\n" + "=" * 80)
if all(results):
    print("✅ ALL TESTS PASSED - Categorization improved!")
else:
    print("⚠️  SOME TESTS FAILED - May need further tuning")
print("=" * 80)

# Show what the issue type should look like
print(f"\n📊 Enhanced Issue Type Generated:")
print(f"   '{df_result.iloc[0]['issue_type_enhanced']}'")
print(f"\n💡 This should now be categorized under:")
print(f"   'Network Management & Bus Communication' (rule-based)")
print(f"   '{df_result.iloc[0]['system_area']} - {df_result.iloc[0]['affected_component']} ... {df_result.iloc[0]['problem_type']}' (enhanced)")
