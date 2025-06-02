#!/usr/bin/env python3
"""
Simple M00986 Debug Script
"""

from kegg_module_completeness.kegg_repository import KeggRepository
from kegg_module_completeness.completeness_calculator import CompletenessCalculator

print("Testing M00986 completeness...")

repo = KeggRepository('pickled_data')
calc = CompletenessCalculator()

# Load T. kodakarensis KOs
with open('input_ko_lists/processed_KO_list_tkodarensis_funct_annot', 'r') as f:
    present_kos = set(line.strip() for line in f if line.strip())

print(f"K18367 present: {'K18367' in present_kos}")

# Test completeness calculation
try:
    definition = repo.get_module_definition('M00986')
    completeness = calc.calculate_module_completeness(definition, present_kos)
    print(f"M00986 completeness: {completeness}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
