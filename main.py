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
        # Create pickled_data directory if it doesn't exist
        pickle_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pickled_data")
        if not os.path.exists(pickle_dir):
            os.makedirs(pickle_dir)
        
        # Update pickle_path to use the new directory
        pickle_path = os.path.join(pickle_dir, "kegg_module_to_kos.pickle")
        
        if (os.path.exists(pickle_path) and 
            (datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(pickle_path))).days < 30):
            print("Using cached KEGG module mapping...")
            module_to_kos = kegg_manager.load_pickled_mapping(pickle_path)
        else:
            print("Cached mapping not found or outdated. Downloading fresh KEGG module data...")
            module_to_kos = kegg_manager.download_and_pickle_mapping(pickle_path)

    # Prepare a simple module-to-kos dict for the report generator
    simple_module_to_kos = {}
    for module_id, module_data in module_to_kos.items():
        if isinstance(module_data, dict) and 'ko_set' in module_data:
            simple_module_to_kos[module_id] = module_data['ko_set']
        else:
            simple_module_to_kos[module_id] = module_data

    # Get all KO lists
    print(f"Loading KO lists from {ko_lists_dir}...")
    ko_lists = ko_manager.get_ko_lists(ko_lists_dir)
    if not ko_lists:
        print(f"No files found in {ko_lists_dir}")
        return 1
    print(f"Found {len(ko_lists)} KO list files to process")
    
    # Calculate completeness for each KO list
    all_results = {}
    for file_name, ko_set in ko_lists.items():
        print(f"Processing {file_name}...")
        module_results = calculator.calculate_all_modules(module_to_kos, ko_set)
        all_results[file_name] = module_results
    
    # Get all module IDs with completeness > 0
    all_module_ids = set()
    for file_results in all_results.values():
        all_module_ids.update(file_results.keys())
    
    # Fetch module information
    module_info_df = kegg_manager.get_module_info(list(all_module_ids))
    
    # Generate reports
    results_df = report_generator.generate_comparison_report(all_results, module_info_df)
    report_generator.generate_individual_reports(all_results, module_info_df)
    report_generator.generate_detailed_report(all_results, simple_module_to_kos, module_info_df, ko_lists)
    
    print("Analysis complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
