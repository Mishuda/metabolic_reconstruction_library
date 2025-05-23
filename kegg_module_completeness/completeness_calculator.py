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
                
                # Handle multi-subunit enzymes
                if '__AND__' in ko:
                    subunits = ko.split('__AND__')
                    return 1.0 if all(sub.strip().upper() in ko_set for sub in subunits) else 0.0
                else:
                    return 1.0 if ko.strip().upper() in ko_set else 0.0
            
            elif block["type"] == "or":
                options = block["options"]
                
                for option in options:
                    # Handle multi-subunit enzymes within OR options
                    if '__AND__' in option:
                        subunits = option.split('__AND__')
                        if all(sub.strip().upper() in ko_set for sub in subunits):
                            return 1.0
                    else:
                        if option.strip().upper() in ko_set:
                            return 1.0
                
                return 0.0
        
        block_scores = [evaluate_block(block) for block in blocks]
        return sum(block_scores) / len(block_scores) if block_scores else 0.0
    
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
        Calculate completeness for multiple modules.
        
        Args:
            module_to_kos (dict): Dictionary mapping module IDs to their KO sets
            ko_set (set): Set of KO identifiers present in the dataset
            
        Returns:
            dict: Dictionary mapping module IDs to their completeness scores
        """
        results = {}
        
        for module_id, module_kos in module_to_kos.items():
            # For modules where we have the definition, we use the Boolean structure
            # Otherwise, we'd need to fetch the definition from KEGG
            # Currently, we're just using the KO sets without structure information
            
            # To properly implement this, we would need to fetch the module definitions
            # and use them with the parse_module_definition function
            
            # This is a placeholder that could be improved by fetching actual module definitions
            present_kos = module_kos.intersection(ko_set)
            completeness = 0
            
            if present_kos:
                # This is where the real structured calculation would happen
                # with actual module definitions
                
                # Since we don't have the actual Boolean definitions here,
                # we'll use a simple approximation for now
                # TODO: Replace this with actual Boolean structure evaluation
                completeness = len(present_kos) / len(module_kos) if len(module_kos) > 0 else 0
            
            results[module_id] = completeness
            
        return results
