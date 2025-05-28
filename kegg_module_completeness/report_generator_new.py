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
        The logical definition contains only K numbers, parentheses, commas, and spaces.
        Enzyme descriptions always follow the logical part.
        """
        if not definition:
            return ""
            
        # Clean whitespace
        definition = re.sub(r'\s+', ' ', definition).strip()
        
        # Find the first occurrence of a K number followed by space and lowercase text
        # This indicates the start of enzyme descriptions
        desc_match = re.search(r'K\d{5}\s+[a-z]', definition)
        if desc_match:
            logical_part = definition[:desc_match.start()].strip()
            
            # If we found a match but the logical part is empty, include just the K number
            if not logical_part:
                # Find all K numbers in the logical sequence
                k_numbers = re.findall(r'K\d{5}', definition[:desc_match.start() + 6])
                return ' '.join(k_numbers) if k_numbers else definition[:desc_match.start() + 6].strip()
            
            return logical_part
        
        # Fallback: if no enzyme descriptions found, check for [EC: or [RN: patterns
        ec_match = re.search(r'\s*\[(?:EC|RN):', definition)
        if ec_match:
            return definition[:ec_match.start()].strip()
        
        # If no clear separation found, return the whole definition
        # This handles cases where the definition might only be logical
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
