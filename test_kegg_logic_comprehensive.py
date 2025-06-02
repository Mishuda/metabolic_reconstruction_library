#!/usr/bin/env python3
"""
Comprehensive test of KEGG definition logic parsing and evaluation.

Tests all the KEGG definition rules:
1. Comma separated K numbers indicate alternatives (OR)
2. Plus signs represent a complex (AND)
3. Minus sign denotes a non-essential component
4. Space separation = AND
5. Parentheses group OR alternatives
"""

from kegg_module_completeness.completeness_calculator import CompletenessCalculator

def test_kegg_logic():
    """Test all KEGG definition logic patterns."""
    calc = CompletenessCalculator()
    
    test_cases = [
        # Case 1: Simple OR with commas (like M00986)
        {
            "name": "Simple OR with commas",
            "definition": "K18367,K17219",
            "test_sets": [
                ({"K18367"}, 1.0, "First alternative present"),
                ({"K17219"}, 1.0, "Second alternative present"), 
                ({"K18367", "K17219"}, 1.0, "Both alternatives present"),
                ({"K12345"}, 0.0, "No alternatives present")
            ]
        },
        
        # Case 2: Complex with plus signs (AND within alternative)
        {
            "name": "Complex with plus signs",
            "definition": "K17219+K17220+K17221",
            "test_sets": [
                ({"K17219", "K17220", "K17221"}, 1.0, "All complex components present"),
                ({"K17219", "K17220"}, 0.0, "Missing one complex component"),
                ({"K17219"}, 0.0, "Missing two complex components"),
                ({}, 0.0, "No components present")
            ]
        },
        
        # Case 3: OR with complex (like M00986)
        {
            "name": "OR with complex (M00986 pattern)",
            "definition": "K18367,(K17219+K17220+K17221)",
            "test_sets": [
                ({"K18367"}, 1.0, "First alternative (single) present"),
                ({"K17219", "K17220", "K17221"}, 1.0, "Second alternative (complex) present"),
                ({"K18367", "K17219", "K17220", "K17221"}, 1.0, "All KOs present"),
                ({"K17219", "K17220"}, 0.0, "Incomplete complex, no single alternative"),
                ({}, 0.0, "No KOs present")
            ]
        },
        
        # Case 4: Space separation (AND)
        {
            "name": "Space separation (AND)",
            "definition": "K00001 K00002 K00003",
            "test_sets": [
                ({"K00001", "K00002", "K00003"}, 1.0, "All AND components present"),
                ({"K00001", "K00002"}, 0.67, "Two of three AND components present"),
                ({"K00001"}, 0.33, "One of three AND components present"),
                ({}, 0.0, "No AND components present")
            ]
        },
        
        # Case 5: OR in parentheses
        {
            "name": "OR in parentheses",
            "definition": "(K00001,K00002,K00003)",
            "test_sets": [
                ({"K00001"}, 1.0, "First OR option present"),
                ({"K00002"}, 1.0, "Second OR option present"),
                ({"K00003"}, 1.0, "Third OR option present"),
                ({"K00001", "K00002"}, 1.0, "Multiple OR options present"),
                ({}, 0.0, "No OR options present")
            ]
        },
        
        # Case 6: Mixed AND and OR
        {
            "name": "Mixed AND and OR",
            "definition": "K00001 (K00002,K00003) K00004",
            "test_sets": [
                ({"K00001", "K00002", "K00004"}, 1.0, "All components satisfied (with first OR option)"),
                ({"K00001", "K00003", "K00004"}, 1.0, "All components satisfied (with second OR option)"),
                ({"K00001", "K00004"}, 0.67, "Missing OR component"),
                ({"K00002", "K00004"}, 0.67, "Missing first AND component"),
                ({}, 0.0, "No components present")
            ]
        },
        
        # Case 7: Minus sign (optional component) - Test if our current implementation handles this
        {
            "name": "Optional component with minus",
            "definition": "K00001 -K00002 K00003",
            "test_sets": [
                ({"K00001", "K00003"}, 1.0, "Required components present, optional missing"),
                ({"K00001", "K00002", "K00003"}, 1.0, "All components including optional present"),
                ({"K00001"}, 0.5, "Missing one required component"),
                ({"K00002"}, 0.0, "Only optional component present"),
                ({"K00001", "K00002"}, 0.5, "Required and optional present, missing one required"),
                ({}, 0.0, "No components present")
            ]
        },
        
        # Case 8: Multiple optional components
        {
            "name": "Multiple optional components",
            "definition": "K00001 -K00002 -K00003 K00004",
            "test_sets": [
                ({"K00001", "K00004"}, 1.0, "Only required components present"),
                ({"K00001", "K00002", "K00004"}, 1.0, "Required plus one optional present"),
                ({"K00001", "K00002", "K00003", "K00004"}, 1.0, "All components present"),
                ({"K00001"}, 0.5, "Missing one required component"),
                ({"K00002", "K00003"}, 0.0, "Only optional components present"),
                ({}, 0.0, "No components present")
            ]
        },
        
        # Case 9: Optional in complex
        {
            "name": "Optional in complex with plus",
            "definition": "K00001+K00002+-K00003",
            "test_sets": [
                ({"K00001", "K00002"}, 1.0, "Required complex components present"),
                ({"K00001", "K00002", "K00003"}, 1.0, "Complex with optional present"),
                ({"K00001"}, 0.0, "Incomplete required complex"),
                ({"K00003"}, 0.0, "Only optional component present"),
                ({}, 0.0, "No components present")
            ]
        }
    ]
    
    print("🧪 Testing KEGG Definition Logic Patterns")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Definition: {test_case['definition']}")
        print("-" * 40)
        
        for ko_set, expected, description in test_case['test_sets']:
            try:
                completeness = calc.calculate_module_completeness(test_case['definition'], ko_set)
                status = "✅" if abs(completeness - expected) < 0.01 else "❌"
                print(f"   {status} {description}")
                print(f"      KOs: {ko_set}")
                print(f"      Expected: {expected:.2f}, Got: {completeness:.2f}")
                
                if abs(completeness - expected) >= 0.01:
                    # Debug the parsing for failed cases
                    structure = calc.parse_module_definition(test_case['definition'])
                    print(f"      DEBUG - Parsed structure: {structure}")
                    
            except Exception as e:
                print(f"   ❌ {description}")
                print(f"      KOs: {ko_set}")
                print(f"      ERROR: {e}")

def test_edge_cases():
    """Test edge cases and complex nested structures."""
    calc = CompletenessCalculator()
    
    print("\n\n🔬 Testing Edge Cases")
    print("=" * 30)
    
    edge_cases = [
        {
            "name": "Complex nested OR with AND",
            "definition": "(K00001+K00002,K00003) K00004",
            "description": "Should be: ((K00001 AND K00002) OR K00003) AND K00004"
        },
        {
            "name": "Multiple comma separations",
            "definition": "K00001,K00002,K00003,K00004",
            "description": "Should be: K00001 OR K00002 OR K00003 OR K00004"
        },
        {
            "name": "Real module example (simplified)",
            "definition": "K01647 (K01681,K01682) K00232",
            "description": "Common pattern in metabolic modules"
        }
    ]
    
    for case in edge_cases:
        print(f"\n• {case['name']}")
        print(f"  Definition: {case['definition']}")
        print(f"  Expected: {case['description']}")
        
        try:
            structure = calc.parse_module_definition(case['definition'])
            print(f"  Parsed: {structure}")
            
            # Test with a sample KO set
            sample_kos = {"K00001", "K00002", "K01647", "K00232"}
            completeness = calc.calculate_module_completeness(case['definition'], sample_kos)
            print(f"  Sample completeness: {completeness:.2f}")
            
        except Exception as e:
            print(f"  ERROR: {e}")

if __name__ == "__main__":
    test_kegg_logic()
    test_edge_cases()
