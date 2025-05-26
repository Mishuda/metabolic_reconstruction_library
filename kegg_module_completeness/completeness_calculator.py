from typing import Dict, Set
import re

class CompletenessCalculator:
    """
    Class to calculate KEGG module completeness using structured definitions.
    """
    
    def __init__(self):
        """Initialize the completeness calculator."""
        self.cached_module_structures = {}
    
    def parse_module_definition(self, definition):
        """
        Parse a KEGG module definition into a structured format.
        
        Args:
            definition (str): KEGG module definition string
            
        Returns:
            dict: Structured representation of the module
        """
        if not definition:
            return {"type": "empty", "blocks": []}
        
        # Clean up definition
        definition = re.sub(r'\s+', ' ', definition).strip()
        
        # Handle optional components (marked with -)
        # Store their positions for later use
        optional_components = []
        def mark_optional(match):
            start, end = match.span()
            optional_components.append((start, end))
            return match.group(0).replace('-', '')
            
        definition = re.sub(r'-K\d{5}', lambda m: mark_optional(m), definition)
        
        # Replace multi-subunit enzyme notation with a special marker
        definition = definition.replace('+', ' __AND__ ')
        
        # Parse the definition into blocks (steps)
        blocks = []
        current_block = ""
        in_parentheses = 0
        
        for char in definition:
            if char == '(' and not in_parentheses:
                if current_block.strip():
                    blocks.append({"type": "step", "ko": current_block.strip()})
                    current_block = ""
                in_parentheses += 1
                current_block += char
            elif char == ')' and in_parentheses:
                current_block += char
                in_parentheses -= 1
                if not in_parentheses:
                    # Process OR block
                    or_block = current_block[1:-1].split(',')
                    blocks.append({"type": "or", "options": [ko.strip() for ko in or_block]})
                    current_block = ""
            elif in_parentheses or not char.isspace():
                current_block += char
            elif current_block.strip():
                blocks.append({"type": "step", "ko": current_block.strip()})
                current_block = ""
        
        if current_block.strip():
            blocks.append({"type": "step", "ko": current_block.strip()})
        
        # Mark optional components in the structured representation
        for block in blocks:
            if block["type"] == "step":
                ko = block["ko"]
                # Check if this KO is in any of the optional spans
                is_optional = any(start <= definition.find(ko) <= end for start, end in optional_components)
                if is_optional:
                    block["optional"] = True
            elif block["type"] == "or":
                for i, option in enumerate(block["options"]):
                    # Check if this option is in any of the optional spans
                    is_optional = any(start <= definition.find(option) <= end for start, end in optional_components)
                    if is_optional:
                        # Convert the option to a dict to mark it as optional
                        if isinstance(option, str):
                            block["options"][i] = {"ko": option, "optional": True}
        
        return {"type": "module", "blocks": blocks}
    
    def evaluate_module_completeness(self, module_structure, ko_set):
        """
        Evaluate a parsed module structure against a set of KOs.
        
        Args:
            module_structure (dict): Module structure from parse_module_definition
            ko_set (set): Set of KO identifiers present in the dataset
            
        Returns:
            float: Completeness score between 0 and 1
        """
        if module_structure["type"] == "empty":
            return 0.0
        
        blocks = module_structure["blocks"]
        if not blocks:
            return 0.0
        
        def evaluate_block(block):
            if block["type"] == "step":
                ko = block["ko"]
                is_optional = block.get("optional", False)
                
                # Handle multi-subunit enzymes
                if '__AND__' in ko:
                    subunits = ko.split('__AND__')
                    if all(sub.strip().upper() in ko_set for sub in subunits):
                        return 1.0
                    elif is_optional:
                        return 0.0  # Optional component is missing but doesn't count against us
                    else:
                        return 0.0
                else:
                    if ko.strip().upper() in ko_set:
                        return 1.0
                    elif is_optional:
                        return 0.0  # Optional component is missing but doesn't count against us
                    else:
                        return 0.0
            
            elif block["type"] == "or":
                options = block["options"]
                
                for option in options:
                    # Handle both string options and dict options (for optional components)
                    if isinstance(option, dict):
                        ko_option = option["ko"]
                        is_optional = option.get("optional", False)
                    else:
                        ko_option = option
                        is_optional = False
                    
                    # Handle multi-subunit enzymes within OR options
                    if '__AND__' in ko_option:
                        subunits = ko_option.split('__AND__')
                        if all(sub.strip().upper() in ko_set for sub in subunits):
                            return 1.0
                    else:
                        if ko_option.strip().upper() in ko_set:
                            return 1.0
                
                # All options are missing - check if any were optional
                if any(isinstance(opt, dict) and opt.get("optional", False) for opt in options):
                    return 0.0  # Optional branch is missing but doesn't count against us
                return 0.0
        
        # Count blocks, excluding optional blocks that are missing
        total_blocks = 0
        block_scores = []
        
        for block in blocks:
            score = evaluate_block(block)
            if score > 0 or not (block.get("optional", False) if block["type"] == "step" 
                               else any(isinstance(opt, dict) and opt.get("optional", False) 
                                      for opt in block["options"]) if block["type"] == "or" else False):
                total_blocks += 1
                block_scores.append(score)
        
        return sum(block_scores) / total_blocks if total_blocks else 0.0
    
    def calculate_module_completeness(self, module_definition, ko_set):
        """
        Calculate module completeness based on its Boolean structure.
        
        Args:
            module_definition (str): KEGG module definition string
            ko_set (set): Set of KO identifiers present in the dataset
            
        Returns:
            float: Scientifically meaningful completeness score between 0 and 1
        """
        # Cache the module structure to avoid repeated parsing
        if module_definition in self.cached_module_structures:
            module_structure = self.cached_module_structures[module_definition]
        else:
            module_structure = self.parse_module_definition(module_definition)
            self.cached_module_structures[module_definition] = module_structure
            
        return self.evaluate_module_completeness(module_structure, ko_set)
    
    def calculate_all_modules(self, module_to_kos, ko_set):
        """
        Calculate completeness for multiple modules using their Boolean definitions.
        
        Args:
            module_to_kos (dict): Standardized dictionary mapping module IDs to their data
            ko_set (set): Set of KO identifiers present in the dataset
            
        Returns:
            dict: Dictionary mapping module IDs to their completeness scores
        """
        results = {}
        
        for module_id, module_data in module_to_kos.items():
            # With standardized data, we always have a consistent structure
            definition = module_data.get('definition', '')
            
            if definition:
                # Use sophisticated Boolean structure analysis
                completeness = self.calculate_module_completeness(definition, ko_set)
            else:
                # Fallback to simple ratio for modules without definitions
                module_kos = module_data.get('ko_set', set())
                if module_kos:
                    present_kos = module_kos.intersection(ko_set)
                    completeness = len(present_kos) / len(module_kos)
                else:
                    completeness = 0.0
            
            results[module_id] = completeness
            
        return results
