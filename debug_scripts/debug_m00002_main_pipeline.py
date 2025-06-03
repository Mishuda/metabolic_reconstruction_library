#!/usr/bin/env python3
"""
Debug script to check M00002 completeness for tkodarensis using main pipeline logic and data sources.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kegg_module_completeness.kegg_repository import KeggRepository
from kegg_module_completeness.completeness_calculator import CompletenessCalculator

# Path to KO list and cache directory (match main pipeline)
ko_list_path = os.path.join('tkoda_input', 'processed_KO_list_tkodarensis_funct_annot')
cache_dir = 'pickled_data'

# Load KO set
with open(ko_list_path, 'r') as f:
    ko_set = set(line.strip().upper() for line in f if line.strip())
print(f"Loaded {len(ko_set)} KOs from {ko_list_path}")

# Load module definition for M00002
repo = KeggRepository(cache_dir)
# Print the raw definition from the module info
raw_definition = repo.get_module_info('M00002').get('Definition', '')
print(f"Raw M00002 definition: {raw_definition}")
definition = repo.get_module_definition('M00002')
print(f"M00002 definition: {definition}")

# Calculate completeness
calc = CompletenessCalculator()
completeness = calc.calculate_module_completeness(definition, ko_set)
print(f"Completeness for M00002 with tkodarensis KOs: {completeness}")

# Print parsed structure for extra debugging
parsed = calc.parse_module_definition(definition)
print(f"Parsed structure for M00002:\n{parsed}")

# Print which KOs are required and which are present
import re
required_kos = set(re.findall(r'K\d{5}', definition))
missing_kos = required_kos - ko_set
print(f"Required KOs for M00002: {sorted(required_kos)}")
print(f"Missing KOs from tkodarensis: {sorted(missing_kos)}")
