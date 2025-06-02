#!/usr/bin/env python3
"""
Debug M00986 Definition Parsing

Test how the completeness calculator is parsing the M00986 definition.
"""

from kegg_module_completeness.completeness_calculator import CompletenessCalculator
from kegg_module_completeness.kegg_repository import KeggRepository

def debug_parsing():
    """Debug the parsing of M00986 definition step by step."""
    print("🔍 Debugging M00986 Definition Parsing")
    print("=" * 50)
    
    repo = KeggRepository('pickled_data')
    calc = CompletenessCalculator()
    
    # Get the raw definition
    definition = repo.get_module_definition('M00986')
    print(f"Raw definition: {definition}")
    
    # Extract logical part
    logical_part = calc._extract_logical_definition(definition)
    print(f"Logical part: {logical_part}")
    
    # Tokenize
    tokens = calc._tokenize_respecting_parentheses(logical_part)
    print(f"Tokens: {tokens}")
    
    # Parse complete structure
    parsed_structure = calc.parse_module_definition(definition)
    print(f"Parsed structure: {parsed_structure}")
      # Test with sample KOs
    present_kos = {'K18367'}  # Only K18367
    print(f"\nTesting with KOs: {present_kos}")
    # Calculate completeness
    completeness = calc.calculate_module_completeness(definition, present_kos)
    print(f"Completeness result: {completeness}")
    
    # Step through calculation manually
    print("\n" + "=" * 30)
    print("MANUAL STEP-THROUGH:")
    print("=" * 30)
    
    # The definition should be: K18367,(K17219+K17220+K17221)
    # This means: K18367 OR (K17219 AND K17220 AND K17221)
    
    print("Expected interpretation:")
    print("  Component 1: K18367 (single KO)")
    print("  Component 2: (K17219+K17220+K17221) (complex)")
    print("  Logic: Component1 OR Component2")
    print("  Since K18367 is present, completeness should be 1.0")

if __name__ == "__main__":
    debug_parsing()
