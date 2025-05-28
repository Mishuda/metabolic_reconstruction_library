#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from kegg_module_completeness.report_generator import ReportGenerator
    print("Successfully imported ReportGenerator")
except Exception as e:
    print(f"Import error: {e}")
    sys.exit(1)

# Test the improved extraction logic
try:
    report_gen = ReportGenerator("dummy")
    print("Successfully created ReportGenerator instance")
except Exception as e:
    print(f"Creation error: {e}")
    sys.exit(1)

test_cases = [
    ("M00554", "K00849 K00965 K00965  UDPglucose--hexose-1-phosphate uridylyltransferase [EC:2.7.7.12] [RN:R00955]"),
    ("M00914", "K00606 K00077 K06982 K09722 K13038 K02201 K09735 K00077  2-dehydropantoate 2-reductase [EC:1.1.1.169] [RN:R02472]"),
    ("M00050", "K00088 K01951 K00942 (K00940,K18533) K01951  GMP synthase [EC:6.3.5.2] [RN:R01230 R01231]"),
    ("M00001", "(K00844,K12407,K00845,K25026,K00886,K08074,K00918) (K01810,K06859,K13810,K15916) (K00850,K16370,K21071,K24182,K00918) (K01623,K01624,K11645,K16305,K16306) K01803 ((K00134,K00150) K00927,K11389) (K01834,K15633,K15634,K15635) (K01689,K27394) (K00873,K12406) K00844,K12407,K00845,K25026,K00886,K08074,K00918  hexokinase [EC:2.7.1.1] [RN:R01786] K01810,K06859,K13810,K15916  glucose-6-phosphate isomerase [EC:5.3.1.9] [RN:R02740]")
]

print("Testing improved extraction logic:")
print("=" * 60)

for module_id, definition in test_cases:
    extracted = report_gen._extract_logical_definition(definition)
    print(f"\n{module_id}:")
    print(f"Original:  {definition}")
    print(f"Extracted: {extracted}")
    print("-" * 60)
