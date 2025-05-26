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
import logging
from tqdm import tqdm
from kegg_module_completeness.ko_manager import KoListManager
from kegg_module_completeness.kegg_manager import KeggModuleManager
from kegg_module_completeness.completeness_calculator import CompletenessCalculator
from kegg_module_completeness.report_generator import ReportGenerator
import argparse

def setup_logging(output_dir, level=logging.INFO):
    """Setup logging to both file and console"""
    # Ensure output directory exists before creating log file
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    log_file = os.path.join(output_dir, f"kegg_analysis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="KEGG Module Completeness Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py ko_lists/ output/
  python main.py ko_lists/ output/ --mapping custom_mapping.tsv
  python main.py ko_lists/ output/ --parallel --verbose
        """
    )
    
    parser.add_argument('ko_lists_dir', help='Directory containing KO list files')
    parser.add_argument('output_dir', help='Output directory for reports')
    parser.add_argument('--mapping', help='Custom module-KO mapping file')
    parser.add_argument('--parallel', action='store_true', help='Use parallel processing')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    parser.add_argument('--config', help='Configuration file path')
    
    return parser.parse_args()

def print_analysis_summary(all_results, logger):
    """Print summary statistics of the analysis"""
    total_files = len(all_results)
    total_modules = len(set().union(*[results.keys() for results in all_results.values()]))
    
    logger.info(f"Analysis Summary:")
    logger.info(f"  - Processed {total_files} KO list files")
    logger.info(f"  - Found {total_modules} modules with completeness > 0")
    
    # Average completeness statistics
    all_completeness = []
    for results in all_results.values():
        all_completeness.extend(results.values())
    
    if all_completeness:
        avg_completeness = sum(all_completeness) / len(all_completeness)
        logger.info(f"  - Average module completeness: {avg_completeness:.2f}")

def main():
    # Parse command line arguments
    args = parse_arguments()

    ko_lists_dir = args.ko_lists_dir
    output_dir = args.output_dir
    mapping_file = args.mapping

    # Setup logging (this will create output_dir if needed)
    logger = setup_logging(output_dir)
    logger.info("Starting KEGG module completeness analysis")
    
    # This line is now redundant since setup_logging creates the directory
    # if not os.path.exists(output_dir):
    #     os.makedirs(output_dir)

    # Initialize components
    ko_manager = KoListManager()
    kegg_manager = KeggModuleManager(output_dir)  # Still pass output_dir for other caching
    calculator = CompletenessCalculator()
    report_generator = ReportGenerator(output_dir)

    # Load module to KO mapping
    logger.info("Loading module to KO mapping...")
    if mapping_file:
        # Use provided mapping file
        module_to_kos = kegg_manager.load_module_to_ko_mapping(mapping_file)
    else:
        # Use root directory for pickle files
        pickle_filename = "kegg_module_to_kos.pickle"
        pickle_path = os.path.join("pickled_data", pickle_filename)  # Root directory path
        
        if (os.path.exists(pickle_path) and 
            (datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(pickle_path))).days < 30):
            logger.info("Using cached KEGG module mapping...")
            module_to_kos = kegg_manager.load_pickled_mapping(pickle_path)
        else:
            logger.info("Cached mapping not found or outdated. Downloading fresh KEGG module data...")
            module_to_kos = kegg_manager.download_and_pickle_mapping(pickle_path)

    # Standardize module data structure - ensure all components use consistent format
    # This eliminates the need for redundant transformations later
    standardized_module_data = kegg_manager.standardize_module_data(module_to_kos)

    # Get all KO lists
    logger.info(f"Loading KO lists from {ko_lists_dir}...")
    ko_lists = ko_manager.get_ko_lists(ko_lists_dir)
    if not ko_lists:
        logger.error(f"No files found in {ko_lists_dir}")
        return 1
    logger.info(f"Found {len(ko_lists)} KO list files to process")
    
    # Calculate completeness for each KO list using standardized data
    all_results = {}
    with tqdm(total=len(ko_lists), desc="Processing KO lists") as pbar:
        for file_name, ko_set in ko_lists.items():
            logger.info(f"Processing {file_name}...")
            module_results = calculator.calculate_all_modules(standardized_module_data, ko_set)
            all_results[file_name] = module_results
            pbar.update(1)
    
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
    
    # Print analysis summary
    print_analysis_summary(all_results, logger)
    
    logger.info("Analysis complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
