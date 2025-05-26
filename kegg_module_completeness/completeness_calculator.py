import re
from typing import Dict, Set, List, Union

class CompletenessCalculator:
    """
    Class to calculate KEGG module completeness using KEGG's standardized definition format.
    """
    
    def __init__(self):
        """Initialize the completeness calculator."""
        self.cached_module_structures = {}
    
    def parse_module_definition(self, definition: str) -> Dict:
        """
        Parse a KEGG module definition using KEGG's standard format.
        
        KEGG format rules:
        - Space separation = AND
        - Comma separation in () = OR
        - Plus separation = complex (all required)
        - Minus prefix = optional
        - Stop at first description text
        
        Args:
            definition: KEGG module definition string
            
        Returns:
            Structured representation of the module
        """
        if not definition:
            return {"type": "empty", "components": []}
        
        # Extract only the logical part (before descriptions)
        logical_part = self._extract_logical_definition(definition)
        
        if not logical_part:
            return {"type": "empty", "components": []}
        
        # Parse components using KEGG's simple rules
        components = self._parse_kegg_format(logical_part)
        
        return {"type": "module", "components": components}
    
    def _extract_logical_definition(self, definition: str) -> str:
        """
        Extract only the logical part of a KEGG definition.
        Stops at the first enzyme name or description.
        """
        # Clean whitespace
        definition = re.sub(r'\s+', ' ', definition).strip()
        
        # Find where descriptions start
        # Pattern: K##### followed by lowercase letter (enzyme name)
        desc_match = re.search(r'K\d{5}\s+[a-z]', definition)
        if desc_match:
            return definition[:desc_match.start()].strip()
        
        # Pattern: [EC: or [RN: 
        ec_match = re.search(r'\s*\[(?:EC|RN):', definition)
        if ec_match:
            return definition[:ec_match.start()].strip()
        
        return definition
    
    def _parse_kegg_format(self, logical_def: str) -> List[Dict]:
        """
        Parse KEGG definition using standard KEGG format rules.
        """
        components = []
        
        # Split by spaces = AND components
        tokens = logical_def.split()
        
        for token in tokens:
            token = token.strip()
            if not token:
                continue
                
            # Handle optional (minus prefix)
            is_optional = token.startswith('-')
            if is_optional:
                token = token[1:]
            
            if token.startswith('(') and token.endswith(')'):
                # OR group: (K01584,K01585,K02626)
                or_content = token[1:-1]  # Remove parentheses
                or_options = [opt.strip() for opt in or_content.split(',')]
                
                components.append({
                    "type": "or",
                    "options": or_options,
                    "optional": is_optional
                })
                
            elif '+' in token:
                # Complex: K07432+K07441 (all subunits required)
                subunits = [sub.strip() for sub in token.split('+')]
                
                components.append({
                    "type": "complex", 
                    "subunits": subunits,
                    "optional": is_optional
                })
                
            elif re.match(r'K\d{5}', token):
                # Single KO: K01480
                components.append({
                    "type": "single",
                    "ko": token,
                    "optional": is_optional
                })
        
        return components
    
    def evaluate_module_completeness(self, module_structure: Dict, ko_set: Set[str]) -> float:
        """
        Evaluate module completeness using KEGG's AND/OR logic.
        """
        if module_structure["type"] == "empty":
            return 0.0
        
        components = module_structure["components"]
        if not components:
            return 0.0
        
        # Count satisfied required components
        satisfied = 0
        required = 0
        
        for component in components:
            is_satisfied = self._evaluate_component(component, ko_set)
            
            if is_satisfied:
                satisfied += 1
            
            # Count as required if not optional
            if not component.get("optional", False):
                required += 1
        
        return satisfied / required if required > 0 else 0.0
    
    def _evaluate_component(self, component: Dict, ko_set: Set[str]) -> bool:
        """
        Evaluate if a single component is satisfied.
        """
        comp_type = component["type"]
        
        if comp_type == "single":
            # Single KO
            return component["ko"].upper() in ko_set
            
        elif comp_type == "or":
            # OR group - at least one must be present
            return any(ko.upper() in ko_set for ko in component["options"])
            
        elif comp_type == "complex":
            # Complex - all subunits must be present  
            return all(ko.upper() in ko_set for ko in component["subunits"])
        
        return False
    
    def calculate_module_completeness(self, module_definition: str, ko_set: Set[str]) -> float:
        """
        Calculate module completeness for a single module.
        """
        # Use caching to avoid re-parsing
        if module_definition in self.cached_module_structures:
            module_structure = self.cached_module_structures[module_definition]
        else:
            module_structure = self.parse_module_definition(module_definition)
            self.cached_module_structures[module_definition] = module_structure
            
        return self.evaluate_module_completeness(module_structure, ko_set)
    
    def calculate_all_modules(self, module_to_kos: Dict, ko_set: Set[str]) -> Dict[str, float]:
        """
        Calculate completeness for all modules.
        """
        results = {}
        
        for module_id, module_data in module_to_kos.items():
            definition = module_data.get('definition', '')
            
            if definition:
                completeness = self.calculate_module_completeness(definition, ko_set)
                
                # Only include modules with completeness > 0
                if completeness > 0:
                    results[module_id] = completeness
        
        return results
