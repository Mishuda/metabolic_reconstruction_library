#!/usr/bin/env python3
"""
Test different KEGG definition patterns to verify our parser works correctly for all rules.

KEGG format rules:
1. Space separation = AND
2. Comma separation in () = OR 
3. Comma separation outside () = OR at top level
4. Plus signs represent a complex (AND)
5. Minus sign denotes a non-essential component
"""

from kegg_module_completeness.completeness_calculator import CompletenessCalculator

def test_kegg_patterns():
    """Test various KEGG definition patterns."""
    print("🧪 Testing KEGG Definition Logic Patterns")
    print("=" * 60)
    
    calc = CompletenessCalculator()
    
    # Test case 1: M00986 (K18367,(K17219+K17220+K17221)) - Top-level OR
    definition = "K18367,(K17219+K17220+K17221)"
    print(f"\n1. Testing M00986 pattern: {definition}")
    
    result = calc.calculate_module_completeness(definition, {'K18367'})
    print(f"   With K18367 only: {result}")
    
    result = calc.calculate_module_completeness(definition, {'K17219', 'K17220', 'K17221'})
    print(f"   With complex only: {result}")
    
    result = calc.calculate_module_completeness(definition, {'K17219', 'K17220'})
    print(f"   With partial complex: {result}")
    
    # Test case 2: Simple comma separation outside parentheses (OR)
    definition = "K00001,K00002,K00003"
    print(f"\n2. Testing comma separation: {definition}")
    
    result = calc.calculate_module_completeness(definition, {'K00001'})
    print(f"   With K00001 only: {result}")
    
    result = calc.calculate_module_completeness(definition, {'K00002', 'K00003'})
    print(f"   With multiple options: {result}")
    
    result = calc.calculate_module_completeness(definition, {'K99999'})
    print(f"   With no matches: {result}")
    
    # Test case 3: Space separation (AND)
    definition = "K00001 K00002 K00003"
    print(f"\n3. Testing space separation (AND): {definition}")
    
    result = calc.calculate_module_completeness(definition, {'K00001', 'K00002', 'K00003'})
    print(f"   With all KOs: {result}")
    
    result = calc.calculate_module_completeness(definition, {'K00001', 'K00002'})
    print(f"   With 2/3 KOs: {result}")
    
    # Test case 4: Complex with plus signs
    definition = "K00001+K00002+K00003"
    print(f"\n4. Testing complex with plus signs: {definition}")
    
    result = calc.calculate_module_completeness(definition, {'K00001', 'K00002', 'K00003'})
    print(f"   With all complex components: {result}")
    
    result = calc.calculate_module_completeness(definition, {'K00001', 'K00002'})
    print(f"   With partial complex: {result}")
    
    # Test case 5: Optional component with minus sign
    definition = "K00001 -K00002 K00003"
    print(f"\n5. Testing optional component: {definition}")
    
    result = calc.calculate_module_completeness(definition, {'K00001', 'K00003'})
    print(f"   With required components only: {result}")
    
    result = calc.calculate_module_completeness(definition, {'K00001', 'K00002', 'K00003'})
    print(f"   With all components: {result}")
    
    # Test case 6: Complex nested structure
    definition = "(K00001,K00002) K00003 (K00004+K00005)"
    print(f"\n6. Testing complex nested structure: {definition}")
    
    result = calc.calculate_module_completeness(definition, {'K00001', 'K00003', 'K00004', 'K00005'})
    print(f"   With complete set: {result}")
    
    result = calc.calculate_module_completeness(definition, {'K00002', 'K00003', 'K00004', 'K00005'})
    print(f"   With alternative in first OR: {result}")
    
    result = calc.calculate_module_completeness(definition, {'K00001', 'K00003'})
    print(f"   With missing complex: {result}")

if __name__ == "__main__":
    test_kegg_patterns()
