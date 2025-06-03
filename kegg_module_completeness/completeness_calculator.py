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
        - Comma separation outside () = OR at top level
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
            
        # Check if there are top-level commas (indicating OR at the top level)
        if "," in logical_part and not self._is_comma_inside_parentheses_only(logical_part):
            # Handle top level OR structure
            or_parts = self._split_top_level_commas(logical_part)
            options = []
            for part in or_parts:
                # Parse each alternative as a separate definition
                # We wrap each part in a structure that preserves its type
                if "+" in part and not "(" in part:
                    # Simple complex: K00001+K00002
                    subunits = [sub.strip() for sub in part.split('+')]
                    options.append({
                        "type": "complex",
                        "subunits": subunits,
                        "optional": False
                    })
                elif part.startswith('(') and part.endswith(')'):
                    # Already a parenthetical structure
                    component = self._parse_parenthetical_structure(part)
                    options.append(component)
                elif re.match(r'K\d{5}', part):
                    # Simple KO
                    options.append({
                        "type": "single",
                        "ko": part,
                        "optional": False
                    })
                else:
                    # More complex structure, use regular parser
                    sub_components = self._parse_kegg_format(part)
                    if len(sub_components) == 1:
                        options.append(sub_components[0])
                    else:
                        # Wrap multiple components in an AND structure
                        options.append({
                            "type": "and_group",
                            "components": sub_components,
                            "optional": False
                        })
            
            return {
                "type": "module", 
                "components": [{
                    "type": "top_level_or",
                    "options": options,
                    "optional": False
                }]
            }
        else:
            # Regular AND-based module
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
        # Special handling for top-level comma-separated KO IDs
        if ',' in logical_def and not self._is_comma_inside_parentheses_only(logical_def):
            parts = self._split_top_level_commas(logical_def)
            options = []
            
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                
                # Handle optional (minus prefix)
                is_optional = part.startswith('-')
                if is_optional:
                    part = part[1:]
                    
                if part.startswith('(') and part.endswith(')'):
                    # Parenthetical structure
                    component = self._parse_parenthetical_structure(part)
                    component["optional"] = is_optional
                    options.append(component)
                elif '+' in part:
                    # Complex: K07432+K07441 (all subunits required)
                    subunits = [sub.strip() for sub in part.split('+')]
                    options.append({
                        "type": "complex",
                        "subunits": subunits,
                        "optional": is_optional
                    })
                elif re.match(r'K\d{5}', part):
                    # Simple KO
                    options.append({
                        "type": "single",
                        "ko": part,
                        "optional": is_optional
                    })
            
            return [{
                "type": "top_level_or", 
                "options": options,
                "optional": False
            }]
        
        # Standard AND logic
        tokens = self._tokenize_respecting_parentheses(logical_def)
        components = []
        
        for token in tokens:
            token = token.strip()
            if not token:
                continue

            # Handle optional (minus prefix)
            is_optional = token.startswith('-')
            if is_optional:
                token = token[1:]

            if token.startswith('(') and token.endswith(')'):
                # Could be simple OR or complex nested structure
                component = self._parse_parenthetical_structure(token)
                component["optional"] = is_optional
                components.append(component)

            elif '+' in token:
                # Complex: K07432+K07441 or K00001+K00002+-K00003 (all subunits required, some may be optional)
                subunit_parts = [sub.strip() for sub in token.split('+')]
                subunits = []
                optional_subunits = []

                for subunit in subunit_parts:
                    if subunit.startswith('-'):
                        # Optional subunit in complex
                        clean_subunit = subunit[1:].strip()
                        if clean_subunit:
                            optional_subunits.append(clean_subunit)
                    else:
                        clean_subunit = subunit.strip()
                        # Do not add any subunit with a leading '-' to required subunits
                        if clean_subunit and not clean_subunit.startswith('-'):
                            subunits.append(clean_subunit)

                components.append({
                    "type": "complex",
                    "subunits": subunits,  # Only required subunits
                    "optional_subunits": optional_subunits,  # Only optional subunits
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
    
    def _tokenize_respecting_parentheses(self, logical_def: str) -> List[str]:
        """
        Tokenize while respecting parentheses boundaries.
        Treats both spaces and commas as separators when outside parentheses.
        """
        tokens = []
        current_token = ""
        paren_depth = 0
        for i, char in enumerate(logical_def):
            if char == '(': 
                paren_depth += 1
                current_token += char
            elif char == ')':
                paren_depth -= 1
                current_token += char
            elif (char == ' ' or char == ',') and paren_depth == 0:
                if current_token.strip():
                    tokens.append(current_token.strip())
                current_token = ""
            else:
                current_token += char
        if current_token.strip():
            tokens.append(current_token.strip())
        return tokens

    def _parse_parenthetical_structure(self, token: str) -> Dict:
        """
        Parse a parenthetical structure which could be simple OR or complex nested.
        Recursively parses nested AND/OR logic.
        """
        # Remove outer parentheses
        inner = token[1:-1].strip()
        # If there are top-level commas, treat as OR
        if self._has_top_level_commas(inner):
            options = self._split_top_level_commas(inner)
            parsed_options = [self._parse_kegg_format_or_single(opt) for opt in options]
            return {"type": "or", "options": parsed_options}
        else:
            # Otherwise, treat as AND group (space-separated)
            tokens = self._tokenize_respecting_parentheses(inner)
            components = [self._parse_kegg_format_or_single(tok) for tok in tokens]
            return {"type": "and_group", "components": components}

    def _parse_kegg_format_or_single(self, s: str) -> Dict:
        s = s.strip()
        if s.startswith('(') and s.endswith(')'):
            return self._parse_parenthetical_structure(s)
        elif '+' in s:
            subunits = [sub.strip() for sub in s.split('+')]
            return {
                "type": "complex",
                "subunits": subunits,
                "optional": False
            }
        elif re.match(r'K\d{5}', s):
            return {
                "type": "single",
                "ko": s,
                "optional": False
            }
        else:
            # Fallback: parse as standard KEGG format (handles nested logic)
            return self._parse_kegg_format(s)[0] if self._parse_kegg_format(s) else {"type": "unknown", "value": s}

    def _has_top_level_commas(self, s: str) -> bool:
        paren_depth = 0
        for char in s:
            if char == '(': paren_depth += 1
            elif char == ')': paren_depth -= 1
            elif char == ',' and paren_depth == 0:
                return True
        return False

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
            if not component.get("optional", False):
                required += 1
                if self._evaluate_component(component, ko_set):
                    satisfied += 1
        # Optional components are ignored in completeness calculation, even if present in KO set
        return satisfied / required if required > 0 else 0.0

    def _evaluate_component(self, component: Dict, ko_set: Set[str]) -> bool:
        """
        Evaluate if a single component is satisfied.
        """
        comp_type = component["type"]
        if comp_type == "single":
            return component["ko"].upper() in ko_set
        elif comp_type == "or":
            return any(self._evaluate_component(opt, ko_set) for opt in component["options"])
        elif comp_type == "and_group":
            return all(self._evaluate_component(comp, ko_set) for comp in component["components"])
        elif comp_type == "top_level_or":
            return any(self._evaluate_component(option, ko_set) for option in component["options"])
        elif comp_type == "complex":
            required_present = all(ko.upper() in ko_set for ko in component["subunits"])
            return required_present
        # Remove 'complex_or', 'simple_ko', 'and_group' with 'definition', etc. (now handled by recursive parse)
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
    
    def _is_comma_inside_parentheses_only(self, logical_def: str) -> bool:
        """
        Check if all commas in the definition are inside parentheses.
        """
        paren_depth = 0
        for char in logical_def:
            if char == '(': paren_depth += 1
            elif char == ')': paren_depth -= 1
            elif char == ',' and paren_depth == 0:
                return False
        return True
    
    def _split_top_level_commas(self, logical_def: str) -> List[str]:
        """
        Split a definition by commas that appear outside parentheses.
        """
        parts = []
        current_part = ""
        paren_depth = 0
        for char in logical_def:
            if char == '(': paren_depth += 1; current_part += char
            elif char == ')': paren_depth -= 1; current_part += char
            elif char == ',' and paren_depth == 0:
                if current_part.strip():
                    parts.append(current_part.strip())
                current_part = ""
            else:
                current_part += char
        if current_part.strip():
            parts.append(current_part.strip())
        return parts