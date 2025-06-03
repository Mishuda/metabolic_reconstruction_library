# Metabolic Reconstruction Library

This library provides a robust pipeline for calculating KEGG module completeness for various organisms based on their KO (KEGG Orthology) profiles. It is designed for flexibility, transparency, and extensibility, with a focus on accurate parsing of KEGG module logic and support for manual curation of problematic modules.

## Directory Structure

- **main.py**: Entry point for the main analysis pipeline. Runs the full workflow from KO input to completeness output.
- **fix_missing_modules.py**: Utility script to patch or fix missing modules in the output or cache.
- **kofam_output_processor.py**: Processes raw KofamScan output into KO lists suitable for the pipeline.
- **kegg_module_completeness/**: Core library package containing all main logic and classes:
  - **completeness_calculator.py**: Contains the logic for parsing KEGG module definitions (including nested AND/OR logic) and calculating module completeness given a set of KOs.
  - **kegg_repository.py**: Handles retrieval, parsing, and caching of KEGG module definitions and metadata. Implements robust logic extraction and supports manual overrides for problematic modules.
  - **kegg_manager.py**: Manages mapping between modules and KOs, and provides utilities for module/KO relationships.
  - **ko_manager.py**: Handles loading, filtering, and management of KO lists.
  - **report_generator.py**: Generates output reports and files, including completeness tables and summaries.
- **debug_scripts/**: Contains test and debug scripts for validating logic, parser behavior, and pipeline correctness. Examples:
  - **debug_m00002_main_pipeline.py**: Debugs the main pipeline logic for module M00002.
  - **test_kegg_logic_comprehensive.py**: Comprehensive tests for KEGG logic parsing and completeness calculation.
  - **test_extraction.py**, **test_improved_extraction.py**: Test scripts for logic extraction routines.
- **input_files/**, **input_ko_lists/**, **tkoda_input/**: Input KO lists for various organisms or datasets.
- **tkoda_output/**: Output directory for processed completeness tables, logs, and reports.
- **kegg_info/**: Contains static KEGG data files (e.g., module-to-KO mappings).
- **pickled_data/**: Stores cached data (pickled Python objects, CSVs) to speed up repeated runs.
- **uml_diagrams/**: UML diagrams of the codebase for documentation and architecture reference.

## Pipeline Logic Flow

1. **Input Preparation**
   - KO lists for each organism are prepared (e.g., from KofamScan or other annotation tools) and placed in the appropriate input directory.

2. **Module and KO Data Loading**
   - The pipeline loads KEGG module definitions and KO mappings, using local cache if available or fetching from KEGG if not.
   - Definitions are parsed to extract only the logical part (AND/OR/optional logic), with manual overrides for problematic modules (e.g., M00002).

3. **Completeness Calculation**
   - For each module, the logic is parsed into a tree structure.
   - The presence of required KOs in the organism's KO set is evaluated according to the module logic (including nested AND/OR/optional groups).
   - Completeness is calculated as the fraction of the module logic satisfied by the KO set.

4. **Reporting**
   - Results are written to output files (TSV, Excel), including completeness scores, module names, classes, and the logic used.
   - Logs and debug information are saved for traceability.

5. **Debugging and Manual Curation**
   - Debug scripts can be used to test specific modules or logic patterns.
   - Manual overrides in `kegg_repository.py` allow for curation of modules with ambiguous or problematic definitions.

## Key Features

- **Robust KEGG Logic Parsing**: Handles complex/nested AND/OR logic, optional components, and edge cases in module definitions.
- **Manual Override Support**: Easily patch problematic modules by adding to the `manual_logic_overrides` dictionary in `kegg_repository.py`.
- **Caching**: All major data (module info, KO mappings, results) is cached for fast repeated runs.
- **Extensive Debugging Tools**: Debug scripts and test cases for validating every step of the logic.
- **Modular Design**: Each component (KO management, module logic, reporting) is separated for clarity and extensibility.

## How to Run the Pipeline

1. Place your KO list(s) in the appropriate input directory (e.g., `tkoda_input/`).
2. Run the main pipeline:
   ```pwsh
   python main.py
   ```
3. Output files will be generated in `tkoda_output/` (or the relevant output directory).
4. If you update module logic or fix a bug, clear the cache in `pickled_data/` and rerun the pipeline to ensure changes are picked up.

## Troubleshooting
- If a module is missing or has incorrect completeness, check the logic extraction in `kegg_repository.py` and add a manual override if needed.
- Use debug scripts in `debug_scripts/` to test specific modules or logic patterns.
- Clear the cache if changes are not reflected in the output.

## Contact
For questions, suggestions, or bug reports, please contact the maintainer or open an issue in your version control system.
