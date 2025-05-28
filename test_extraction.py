#!/usr/bin/env python3

import re

def test_extraction(definition: str) -> str:
    """Test version of the extraction logic."""
    if not definition:
        return ""
    
    # Clean whitespace
    definition = re.sub(r'\s+', ' ', definition).strip()
    
    # Find all K number positions
    k_positions = [(m.start(), m.end()) for m in re.finditer(r'K\d{5}', definition)]
    
    if not k_positions:
        return definition
    
    # Look for the first K number that's followed by an enzyme description
    for i, (start, end) in enumerate(k_positions):
        # Get the text after this K number
        after_k = definition[end:].lstrip()
        
        # Check if this looks like an enzyme description
        if after_k and not after_k.startswith(('K', '(', ')', ',', '+', ' ')):
            # This K number is followed by an enzyme description
            # Return everything up to this K number (including this K number)
            return definition[:end].strip()
    
    # Look for [EC: or [RN: patterns as fallback
    ec_match = re.search(r'\s*\[(?:EC|RN):', definition)
    if ec_match:
        return definition[:ec_match.start()].strip()
    
    # If no clear separation found, return the whole definition
    return definition

# Test cases
test_cases = [
    "K00849 K00965 K00965 UDPglucose--hexose-1-phosphate uridylyltransferase [EC:2.7.7.12]",
    "K00606 K00077 K06982 K09722 K13038 K02201 K09735 K00077 2-dehydropantoate 2-reductase [EC:1.1.1.169]",
    "K00088 K01951 K00942 (K00940,K18533) K01951 GMP synthase [EC:6.3.5.2]",
    "(K00844,K12407,K00845,K25026,K00886,K08074,K00918) (K01810,K06859,K13810,K15916) K00886 polyphosphate glucokinase",
    "K00948",
    "((K00404+K00405,K15862)+K00407+K00406)"
]

for i, test in enumerate(test_cases, 1):
    result = test_extraction(test)
    print(f"Test {i}:")
    print(f"  Input:  {test}")
    print(f"  Output: {result}")
    print()
