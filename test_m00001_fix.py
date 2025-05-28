#!/usr/bin/env python3
"""
Test script to verify that M00001 now correctly evaluates to 1.0 completeness
with the improved parser that handles nested parentheses.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from kegg_module_completeness.completeness_calculator import CompletenessCalculator

def test_m00001_parsing():
    """Test M00001 parsing and evaluation."""
    
    # M00001 definition from our analysis
    m00001_definition = "((K00134,K00150) K00927,K11389) (K01810,K06859,K13810,K15916) (K00850,K16370,K21071,K00918) (K01623,K01624,K11645,K16305,K16306) K01803 ((K00134,K00150) K15633,K15634,K15635) K01834 (K06859,K13810,K15916) K01689"
    
    # KOs present in our input file (from previous analysis)
    present_kos = {
        'K00150', 'K00927', 'K11389', 'K01810', 'K06859', 'K13810', 'K15916',
        'K00850', 'K16370', 'K21071', 'K00918', 'K01623', 'K01624', 'K11645',
        'K16305', 'K16306', 'K01803', 'K15633', 'K15634', 'K15635', 'K01834',
        'K01689'
    }
    
    print("Testing M00001 with improved parser...")
    print(f"Definition: {m00001_definition}")
    print(f"Number of KOs present: {len(present_kos)}")
    print(f"Present KOs: {sorted(present_kos)}")
    print()
    
    # Initialize calculator
    calculator = CompletenessCalculator()
    
    # Parse the module structure
    print("Parsing module structure...")
    module_structure = calculator.parse_module_definition(m00001_definition)
    print(f"Module type: {module_structure['type']}")
    print(f"Number of components: {len(module_structure['components'])}")
    print()
    
    # Show each component and its evaluation
    print("Component-by-component evaluation:")
    for i, component in enumerate(module_structure['components']):
        is_satisfied = calculator._evaluate_component(component, present_kos)
        print(f"Component {i+1}: {component['type']} - {'SATISFIED' if is_satisfied else 'NOT SATISFIED'}")
        
        if component['type'] == 'complex_or':
            print(f"  Alternatives: {len(component['alternatives'])}")
            for j, alt in enumerate(component['alternatives']):
                alt_satisfied = calculator._evaluate_alternative(alt, present_kos)
                print(f"    Alt {j+1}: {alt['type']} - {'SATISFIED' if alt_satisfied else 'NOT SATISFIED'}")
                if alt['type'] == 'and_group':
                    print(f"      Definition: {alt['definition']}")
        elif component['type'] == 'or':
            satisfied_options = [opt for opt in component['options'] if opt.upper() in present_kos]
            print(f"  Satisfied options: {satisfied_options}")
        elif component['type'] == 'single':
            print(f"  KO: {component['ko']} - {'PRESENT' if component['ko'].upper() in present_kos else 'MISSING'}")
    
    print()
    
    # Calculate final completeness
    completeness = calculator.evaluate_module_completeness(module_structure, present_kos)
    print(f"Final completeness: {completeness}")
    print(f"Expected: 1.0")
    print(f"Result: {'PASS' if completeness == 1.0 else 'FAIL'}")
    
    return completeness

def test_specific_problematic_component():
    """Test the specific problematic component that was causing issues."""
    
    print("\n" + "="*60)
    print("Testing the specific problematic component:")
    print("((K00134,K00150) K00927,K11389)")
    print("Expected logic: ((K00134 OR K00150) AND K00927) OR K11389")
    print()
    
    # Available KOs: K00150, K00927, K11389 (K00134 is missing)
    available_kos = {'K00150', 'K00927', 'K11389'}
    
    calculator = CompletenessCalculator()
    
    # Test the component directly
    component_def = "((K00134,K00150) K00927,K11389)"
    
    # Parse just this component
    test_module = f"({component_def[1:-1]})"  # Wrap in outer parentheses
    structure = calculator.parse_module_definition(test_module)
    
    if structure['components']:
        component = structure['components'][0]
        print(f"Component type: {component['type']}")
        
        if component['type'] == 'complex_or':
            print(f"Number of alternatives: {len(component['alternatives'])}")
            
            for i, alt in enumerate(component['alternatives']):
                satisfied = calculator._evaluate_alternative(alt, available_kos)
                print(f"Alternative {i+1}: {alt} - {'SATISFIED' if satisfied else 'NOT SATISFIED'}")
        
        final_result = calculator._evaluate_component(component, available_kos)
        print(f"\nFinal component result: {'SATISFIED' if final_result else 'NOT SATISFIED'}")
        print(f"Expected: SATISFIED")
        print(f"Test: {'PASS' if final_result else 'FAIL'}")

if __name__ == "__main__":
    # Test M00001 completeness
    completeness = test_m00001_parsing()
    
    # Test the specific problematic component
    test_specific_problematic_component()
    
    print(f"\n{'='*60}")
    if completeness == 1.0:
        print("SUCCESS: M00001 now correctly evaluates to 1.0 completeness!")
    else:
        print(f"ISSUE: M00001 evaluates to {completeness}, expected 1.0")
