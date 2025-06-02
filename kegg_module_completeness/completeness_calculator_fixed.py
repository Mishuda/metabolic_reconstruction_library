import re
from typing import Dict, Set, List, Union

class CompletenessCalculator:
    """
    Class to calculate KEGG module completeness using KEGG's standardized definition format.
    
    KEGG Format Rules (CORRECTED):
    1. Comma separation outside parentheses = OR at top level
    2. Space separation = AND  
    3. Comma separation inside parentheses = OR within that group
    4. Plus signs (+) = complex/protein complex (all subunits required)
    5. Minus signs (-) = optional component
    """
    
    def __init__(self):
        """Initialize the completeness calculator."""
        self.cached_module_structures = {}

    def parse_module_definition(self, definition: str) -> Dict:
        """
        Parse a KEGG module definition using KEGG's standard format.
        
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
            
        # Check if there are top-level commas (indicating OR at the top level)
        if self._has_top_level_commas(logical_part):
            # This is a top-level OR structure like "K18367,(K17219+K17220+K17221)"
            return self._parse_top_level_or(logical_part)
        else:
            # Regular AND-based module structure
            components = self._parse_and_components(logical_part)
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

    def _has_top_level_commas(self, logical_def: str) -> bool:
        """
        Check if there are commas outside of parentheses (top-level OR).
        """
        paren_depth = 0
        for char in logical_def:
            if char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
            elif char == ',' and paren_depth == 0:
                # Found comma outside parentheses
                return True
        return False

    def _split_top_level_commas(self, logical_def: str) -> List[str]:
        """
        Split a definition by commas that appear outside parentheses.
        """
        parts = []
        current_part = ""
        paren_depth = 0
        
        for char in logical_def:
            if char == '(':
                paren_depth += 1
                current_part += char
            elif char == ')':
                paren_depth -= 1
                current_part += char
            elif char == ',' and paren_depth == 0:
                # Top-level comma = OR separator
                if current_part.strip():
                    parts.append(current_part.strip())
                current_part = ""
            else:
                current_part += char
        
        if current_part.strip():
            parts.append(current_part.strip())
            
        return parts

    def _parse_top_level_or(self, logical_def: str) -> Dict:
        """
        Parse a top-level OR structure like "K18367,(K17219+K17220+K17221)"
        """
        or_parts = self._split_top_level_commas(logical_def)
        options = []
        
        for part in or_parts:
            part = part.strip()
            if not part:
                continue
                
            # Parse each OR alternative
            if part.startswith('(') and part.endswith(')'):
                # Parenthetical group: (K17219+K17220+K17221)
                inner = part[1:-1]
                option = self._parse_parenthetical_content(inner)
            elif '+' in part:
                # Complex: K17219+K17220+K17221
                subunits = [sub.strip() for sub in part.split('+') if sub.strip()]
                option = {
                    "type": "complex",
                    "subunits": subunits,
                    "optional": False
                }
            elif re.match(r'K\d{5}$', part):
                # Single KO: K18367
                option = {
                    "type": "single",
                    "ko": part,
                    "optional": False
                }
            else:
                # More complex part - parse as AND components
                and_components = self._parse_and_components(part)
                if len(and_components) == 1:
                    option = and_components[0]
                else:
                    option = {
                        "type": "and_group",
                        "components": and_components,
                        "optional": False
                    }
            
            options.append(option)
        
        return {
            "type": "module",
            "components": [{
                "type": "top_level_or",
                "options": options,
                "optional": False
            }]
        }

    def _parse_parenthetical_content(self, inner: str) -> Dict:
        """
        Parse content inside parentheses.
        """
        inner = inner.strip()
        
        if '+' in inner and ',' not in inner:
            # Complex: K17219+K17220+K17221
            subunits = [sub.strip() for sub in inner.split('+') if sub.strip()]
            return {
                "type": "complex",
                "subunits": subunits,
                "optional": False
            }
        elif ',' in inner:
            # OR group: K01584,K01585,K02626
            options = [opt.strip() for opt in inner.split(',') if opt.strip()]
            return {
                "type": "or",
                "options": options,
                "optional": False
            }
        else:
            # Single item or space-separated AND
            if ' ' in inner:
                # Space-separated AND
                components = self._parse_and_components(inner)
                if len(components) == 1:
                    return components[0]
                else:
                    return {
                        "type": "and_group",
                        "components": components,
                        "optional": False
                    }
            else:
                # Single KO
                return {
                    "type": "single",
                    "ko": inner,
                    "optional": False
                }

    def _parse_and_components(self, logical_def: str) -> List[Dict]:
        """
        Parse space-separated AND components.
        """
        # Split by spaces, but respect parentheses
        tokens = self._tokenize_by_spaces(logical_def)
        components = []
        
        for token in tokens:
            token = token.strip()
            if not token:
                continue
                
            # Handle optional (minus prefix)
            is_optional = token.startswith('-')
            if is_optional:
                token = token[1:].strip()
            
            if token.startswith('(') and token.endswith(')'):
                # Parenthetical structure
                inner = token[1:-1]
                component = self._parse_parenthetical_content(inner)
                component["optional"] = is_optional
                components.append(component)
                
            elif '+' in token:
                # Complex: K07432+K07441 (all subunits required)
                subunits = [sub.strip() for sub in token.split('+') if sub.strip()]
                components.append({
                    "type": "complex", 
                    "subunits": subunits,
                    "optional": is_optional
                })
                
            elif re.match(r'K\d{5}$', token):
                # Single KO: K01480
                components.append({
                    "type": "single",
                    "ko": token,
                    "optional": is_optional
                })
        
        return components

    def _tokenize_by_spaces(self, logical_def: str) -> List[str]:
        """
        Tokenize by spaces while respecting parentheses boundaries.
        """
        tokens = []
        current_token = ""
        paren_depth = 0
        
        for char in logical_def:
            if char == '(':
                current_token += char
                paren_depth += 1
            elif char == ')':
                current_token += char
                paren_depth -= 1
            elif char == ' ' and paren_depth == 0:
                # Space outside parentheses = separator
                if current_token.strip():
                    tokens.append(current_token.strip())
                    current_token = ""
            else:
                current_token += char
        
        # Add final token
        if current_token.strip():
            tokens.append(current_token.strip())
        
        return tokens

    def evaluate_module_completeness(self, module_structure: Dict, ko_set: Set[str]) -> float:
        """
        Evaluate module completeness using KEGG's AND/OR logic.
        """
        if module_structure["type"] == "empty":
            return 0.0
        
        components = module_structure["components"]
        if not components:
            return 0.0
        
        # Check for top-level OR components
        for component in components:
            if component["type"] == "top_level_or":
                # For top-level OR, if any option is satisfied, the module is complete
                for option in component["options"]:
                    if self._evaluate_component(option, ko_set):
                        return 1.0
                # If no options satisfied, return 0
                return 0.0
        
        # Regular AND logic for other components
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
            
        elif comp_type == "top_level_or":
            # Top-level OR group - at least one option must be satisfied
            return any(self._evaluate_component(option, ko_set) for option in component["options"])
            
        elif comp_type == "and_group":
            # AND group - all components must be satisfied
            return all(self._evaluate_component(comp, ko_set) for comp in component.get("components", []))
            
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
