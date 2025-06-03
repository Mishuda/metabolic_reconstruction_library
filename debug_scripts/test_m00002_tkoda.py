import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from kegg_module_completeness.completeness_calculator import CompletenessCalculator

def main():
    # M00002 definition from kegg_module_info.csv
    definition = "K01803 ((K00134,K00150) K00927,K11389) (K01834,K15633,K15634,K15635) (K01689,K27394) (K00873,K12406)"
    # tkodarensis KO set (reduced to relevant KOs)
    ko_set = {
        'K01803', 'K00134', 'K00150', 'K00927', 'K01834', 'K15633', 'K15634', 'K15635', 'K01689', 'K00873'
    }
    calc = CompletenessCalculator()
    # Print parsed structure for debugging
    parsed = calc.parse_module_definition(definition)
    print("Parsed structure for M00002:")
    print(parsed)
    print()
    completeness = calc.calculate_module_completeness(definition, ko_set)
    print(f"Completeness for M00002 with tkodarensis KOs: {completeness}")

if __name__ == "__main__":
    main()
