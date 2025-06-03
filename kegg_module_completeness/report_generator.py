import os
import re
import pandas as pd
from typing import Dict

class ReportGenerator:
    """Generates reports and output files."""
    
    def __init__(self, output_dir: str):
        """Initialize the report generator.
        
        Args:
            output_dir: Directory to save report files
        """
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def _extract_logical_definition(self, definition: str) -> str:
        """
        Extract only the logical part of a KEGG definition.
        The logical definition contains only K numbers, parentheses, commas, spaces, and + signs.
        Enzyme descriptions always follow the logical part.
        Also removes any trailing KO list after the logic block (e.g., ... (K00873,K12406) K00134,K00150 ...)
        """
        if not definition:
            return ""
            
        # Clean whitespace
        definition = re.sub(r'\s+', ' ', definition).strip()
        
        # Find all K number positions
        k_positions = [(m.start(), m.end()) for m in re.finditer(r'K\d{5}', definition)]
        
        if not k_positions:
            return definition
        
        # Look for [EC: or [RN: patterns first (most reliable indicators)
        ec_rn_match = re.search(r'\s*\[(?:EC|RN):', definition)
        if ec_rn_match:
            return definition[:ec_rn_match.start()].strip()
        
        # Look for enzyme descriptions by finding K numbers followed by text that doesn't look like structural elements
        for i, (start, end) in enumerate(k_positions):
            # Get the text after this K number
            after_k = definition[end:].lstrip()
            
            # Skip if this is the last K number and there's nothing after it
            if not after_k:
                continue
                
            # Check if the text after this K number looks like an enzyme description
            # Enzyme descriptions typically start with:
            # 1. Lowercase letter (like "guanylate kinase")
            # 2. A digit followed by hyphen (like "2-dehydropantoate")
            # 3. Uppercase compound names followed by lowercase (like "GMP synthase", "UDPglucose--hexose")
            # 4. But NOT structural elements like: K, (, ), ,, +, space
            
            # Check for clear enzyme description patterns
            if re.match(r'^[a-z]', after_k):  # Starts with lowercase
                return definition[:end].strip()
            elif re.match(r'^\d+-', after_k):  # Starts with digit-hyphen (like "2-dehydro")
                return definition[:end].strip()
            elif re.match(r'^[A-Z]+[a-z]', after_k):  # Uppercase followed by lowercase (like "GMP synthase")
                return definition[:end].strip()
            elif re.match(r'^[A-Z]+[a-z]*--', after_k):  # Compound names with double dash (like "UDPglucose--hexose")
                return definition[:end].strip()
            elif re.match(r'^[A-Z]{2,}[a-z]', after_k):  # Multi-uppercase followed by lowercase (like "UDPglucose")
                return definition[:end].strip()
        
        # Remove trailing KO list after logic block
        logic_end = None
        paren_matches = list(re.finditer(r'\)', definition))
        if paren_matches:
            logic_end = paren_matches[-1].end()
        else:
            k_matches = list(re.finditer(r'K\d{5}', definition))
            if k_matches:
                logic_end = k_matches[-1].end()
        if logic_end:
            return definition[:logic_end].strip()
        
        # If all else fails, return the whole definition
        return definition
    
    def generate_individual_reports(
        self, 
        all_results: Dict[str, Dict[str, float]], 
        module_info_df: pd.DataFrame
    ):
        """Generate individual reports for each KO list.
        
        Args:
            all_results: Results for all KO lists (file_name -> {module_id -> completeness})
            module_info_df: DataFrame with module information
        """
        print("Generating individual module completeness files...")
        for file_name, file_results in all_results.items():
            # Only include modules with completeness > 0
            filtered_results = {module_id: completeness 
                              for module_id, completeness in file_results.items() 
                              if completeness > 0}
            
            if not filtered_results:
                print(f"  - No modules with completeness > 0 found for {file_name}")
                continue
                
            # Create a dataframe with only modules that have completeness > 0
            file_df = pd.DataFrame(index=sorted(filtered_results.keys()))
            file_df['Completeness'] = pd.Series(filtered_results)
            
            # Map information from module_info_df, handling missing modules
            names = {}
            classes = {}
            logical_definitions = {}
            
            for module_id in file_df.index:
                # Look up module info (try without md: prefix first)
                if module_id in module_info_df.index:
                    names[module_id] = module_info_df.loc[module_id, 'Name']
                    classes[module_id] = module_info_df.loc[module_id, 'Class']
                    full_definition = module_info_df.loc[module_id, 'Definition']
                    logical_definitions[module_id] = self._extract_logical_definition(full_definition)
                else:
                    # Try with md: prefix as fallback
                    info_key = f"md:{module_id}"
                    if info_key in module_info_df.index:
                        names[module_id] = module_info_df.loc[info_key, 'Name']
                        classes[module_id] = module_info_df.loc[info_key, 'Class']
                        full_definition = module_info_df.loc[info_key, 'Definition']
                        logical_definitions[module_id] = self._extract_logical_definition(full_definition)
                    else:
                        names[module_id] = "Unknown"
                        classes[module_id] = "Unknown"
                        logical_definitions[module_id] = "Unknown"
            
            file_df['Name'] = pd.Series(names)
            file_df['Class'] = pd.Series(classes)
            file_df['Definition'] = pd.Series(logical_definitions)
            
            # Sort by completeness (descending)
            file_df = file_df.sort_values(by='Completeness', ascending=False)
            
            # Create output file name (replace spaces and special characters)
            safe_filename = re.sub(r'[^a-zA-Z0-9_]', '_', file_name)
            individual_output = os.path.join(self.output_dir, f"{safe_filename}_module_completeness.tsv")
            file_df.to_csv(individual_output, sep='\t')
            print(f"  - Created individual results for {file_name} ({len(filtered_results)} modules)")
