import os
import re
import pandas as pd
from typing import Dict, Set, List

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
    
    def generate_comparison_report(
        self, 
        all_results: Dict[str, Dict[str, float]], 
        module_info_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Generate a comparison report for all KO lists.
        
        Args:
            all_results: Results for all KO lists (file_name -> {module_id -> completeness})
            module_info_df: DataFrame with module information
            
        Returns:
            DataFrame with comparison results
        """
        # Get all module IDs with completeness > 0
        all_module_ids = set()
        for file_results in all_results.values():
            all_module_ids.update(file_results.keys())
        
        # Create a DataFrame for comparative results
        results_df = pd.DataFrame(index=sorted(all_module_ids))
        
        # Add completeness values for each file
        for file_name, module_results in all_results.items():
            results_df[file_name] = pd.Series(module_results)
        
        # Add module information
        results_df['Name'] = module_info_df['Name']
        results_df['Class'] = module_info_df['Class']
        results_df['Definition'] = module_info_df['Definition']
        
        # Fill NaN values with 0 for completeness values
        for file_name in all_results.keys():
            results_df[file_name] = results_df[file_name].fillna(0)
        
        # Sort by average completeness across all files
        results_df['Average'] = results_df[[col for col in results_df.columns 
                                          if col not in ['Name', 'Class', 'Definition']]].mean(axis=1)
        results_df = results_df.sort_values(by='Average', ascending=False)
        
        # Save results
        output_file = os.path.join(self.output_dir, "module_completeness_comparison.tsv")
        results_df.to_csv(output_file, sep='\t')
        print(f"Results saved to {output_file}")
        
        return results_df
    
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
        all_module_ids = set()
        for file_results in all_results.values():
            all_module_ids.update(file_results.keys())
            
        print("Generating individual module completeness files...")
        for file_name, file_results in all_results.items():
            # Create a dataframe with just this file's completeness values
            file_df = pd.DataFrame(index=sorted(all_module_ids))
            file_df['Completeness'] = pd.Series(file_results)
            file_df['Name'] = module_info_df['Name']
            file_df['Class'] = module_info_df['Class']
            file_df['Definition'] = module_info_df['Definition']
            file_df['Completeness'] = file_df['Completeness'].fillna(0)
            
            # Sort by completeness
            file_df = file_df.sort_values(by='Completeness', ascending=False)
            
            # Create output file name (replace spaces and special characters)
            safe_filename = re.sub(r'[^a-zA-Z0-9_]', '_', file_name)
            individual_output = os.path.join(self.output_dir, f"{safe_filename}_module_completeness.tsv")
            file_df.to_csv(individual_output, sep='\t')
            print(f"  - Created individual results for {file_name}")
    
    def generate_detailed_report(
        self, 
        all_results: Dict[str, Dict[str, float]],
        module_to_kos: Dict[str, Set[str]], 
        module_info_df: pd.DataFrame,
        ko_lists: Dict[str, Set[str]]
    ):
        """Generate a detailed report with present and missing KOs.
        
        Args:
            all_results: Results for all KO lists (file_name -> {module_id -> completeness})
            module_to_kos: Dictionary mapping module IDs to sets of KO IDs
            module_info_df: DataFrame with module information
            ko_lists: Dictionary mapping file names to sets of KO IDs
        """
        # Get all module IDs with completeness > 0
        all_module_ids = set()
        for file_results in all_results.values():
            all_module_ids.update(file_results.keys())
        
        # Calculate average completeness for each module
        avg_completeness = {}
        for module_id in all_module_ids:
            completeness_values = [file_results.get(module_id, 0) 
                                for file_results in all_results.values()]
            avg_completeness[module_id] = sum(completeness_values) / len(completeness_values)
        
        # Generate detailed report
        detailed_output = os.path.join(self.output_dir, "module_details.tsv")
        with open(detailed_output, 'w') as f:
            f.write("Module_ID\tName\tClass\tDefinition\tAverage_Completeness\tPresent_KOs\tMissing_KOs\tTotal_KOs\tBoolean_Structure\n")
            
            for module_id in sorted(all_module_ids, key=lambda m: avg_completeness.get(m, 0), reverse=True):
                if module_id in module_info_df.index:
                    name = module_info_df.loc[module_id, 'Name']
                    class_info = module_info_df.loc[module_id, 'Class']
                    definition = module_info_df.loc[module_id, 'Definition']
                    avg = avg_completeness.get(module_id, 0)
                    
                    # Get all KOs in this module
                    module_kos = module_to_kos.get(module_id, set())
                    total_kos = len(module_kos)
                    
                    # Find KOs present in any of the files
                    present_kos = set()
                    for file_name, ko_set in ko_lists.items():
                        present_kos.update(module_kos.intersection(ko_set))
                    
                    missing_kos = module_kos - present_kos
                    
                    f.write(f"{module_id}\t{name}\t{class_info}\t{definition}\t{avg:.2f}\t")
                    f.write(f"{','.join(present_kos)}\t{','.join(missing_kos)}\t{total_kos}\t{definition}\n")
        
        print(f"Detailed module information saved to {detailed_output}")
