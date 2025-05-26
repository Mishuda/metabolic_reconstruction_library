#!/usr/bin/env python3
"""
KEGG Module Completeness Analysis Tool

This script analyzes the completeness of KEGG modules in multiple KO lists
and generates comparative reports.

Usage: python kegg_module_completeness.py ko_lists_dir/ output_dir/ [module_ko_mapping.tsv]

If module_ko_mapping.tsv is not provided, a cached mapping will be used,
which is automatically refreshed every 30 days.
"""

import os
import sys
import datetime
from kegg_module_completeness.ko_manager import KoListManager
from kegg_module_completeness.kegg_manager import KeggModuleManager
from kegg_module_completeness.completeness_calculator import CompletenessCalculator
from kegg_module_completeness.report_generator import ReportGenerator

def main():
    # Check command line arguments
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python kegg_module_completeness.py ko_lists_dir/ output_dir/ [module_ko_mapping.tsv]")
        print("If mapping file is not provided, a cached mapping will be used (auto-refreshed every 30 days)")
        return 1

    ko_lists_dir = sys.argv[1]
    output_dir = sys.argv[2]
    mapping_file = sys.argv[3] if len(sys.argv) == 4 else None

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Initialize components
    ko_manager = KoListManager()
    kegg_manager = KeggModuleManager(output_dir)
    calculator = CompletenessCalculator()
    report_generator = ReportGenerator(output_dir)

    # Load module to KO mapping
    print("Loading module to KO mapping...")
    if mapping_file:
        # Use provided mapping file
        module_to_kos = kegg_manager.load_module_to_ko_mapping(mapping_file)
    else:
        # Use the manager's internal pickle directory structure
        pickle_filename = "kegg_module_to_kos.pickle"
        pickle_path = os.path.join(kegg_manager.pickled_data_dir, pickle_filename)
        
        if (os.path.exists(pickle_path) and 
            (datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(pickle_path))).days < 30):
            print("Using cached KEGG module mapping...")
            module_to_kos = kegg_manager.load_pickled_mapping(pickle_path)
        else:
            print("Cached mapping not found or outdated. Downloading fresh KEGG module data...")
            module_to_kos = kegg_manager.download_and_pickle_mapping(pickle_path)

    # Standardize module data structure - ensure all components use consistent format
    # This eliminates the need for redundant transformations later
    standardized_module_data = kegg_manager.standardize_module_data(module_to_kos)

    # Get all KO lists
    print(f"Loading KO lists from {ko_lists_dir}...")
    ko_lists = ko_manager.get_ko_lists(ko_lists_dir)
    if not ko_lists:
        print(f"No files found in {ko_lists_dir}")
        return 1
    print(f"Found {len(ko_lists)} KO list files to process")
    
    # Calculate completeness for each KO list using standardized data
    all_results = {}
    for file_name, ko_set in ko_lists.items():
        print(f"Processing {file_name}...")
        module_results = calculator.calculate_all_modules(standardized_module_data, ko_set)
        all_results[file_name] = module_results
    
    # Get all module IDs with completeness > 0
    all_module_ids = set()
    for file_results in all_results.values():
        all_module_ids.update(file_results.keys())
    
    # Fetch module information
    module_info_df = kegg_manager.get_module_info(list(all_module_ids))
    
    # Generate reports using standardized data structure
    results_df = report_generator.generate_comparison_report(all_results, module_info_df)
    report_generator.generate_individual_reports(all_results, module_info_df)
    report_generator.generate_detailed_report(all_results, standardized_module_data, module_info_df, ko_lists)
    
    print("Analysis complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
