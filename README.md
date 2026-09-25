# Metabolic Reconstruction Library

Python workflow for calculating **KEGG module completeness from KEGG Orthology (KO) profiles**.

This repository was developed during my M1 research internship in comparative genomics and metabolic reconstruction of **Thermococcales**. Its purpose is to take KO sets produced by functional annotation and evaluate how completely KEGG metabolic modules are represented in each genome.

## What the workflow does

1. Load KO profiles produced by tools such as KofamScan.
2. Retrieve or load KEGG module definitions and KO mappings.
3. Parse module logic, including nested alternatives and optional components.
4. Calculate module-completeness scores for each KO set.
5. Export tables that can be compared across organisms and visualized downstream.

## Main components

| Path | Purpose |
| --- | --- |
| `main.py` | Main analysis entry point |
| `kegg_module_completeness/completeness_calculator.py` | Parse KEGG module logic and calculate completeness |
| `kegg_module_completeness/kegg_repository.py` | Retrieve, parse and cache module definitions |
| `kegg_module_completeness/kegg_manager.py` | Module/KO mapping utilities |
| `kegg_module_completeness/ko_manager.py` | Load and manage KO profiles |
| `kegg_module_completeness/report_generator.py` | Generate result tables and summaries |
| `kofam_output_processor.py` | Convert significant KofamScan hits into KO lists |
| `debug_scripts/` | Development checks for parser and module-logic edge cases |

## Research context

The library was used as part of a broader workflow analysing **122 Thermococcales genomes**. That project combined pangenome analysis, functional annotation and metabolic reconstruction to compare conserved and lineage-specific metabolic capabilities.

The visualization component used for comparative heatmaps is maintained separately in [`heatmapper-scripts`](https://github.com/Mishuda/heatmapper-scripts).

## Running the workflow

Place one or more KO lists in the expected input location and run:

```bash
python main.py
```

The codebase was developed as research software rather than a packaged Python library, so paths and input conventions may need adaptation for a new dataset.

## Notes on KEGG data

The workflow uses KEGG module definitions and KO mappings for academic research. Some directories in this repository contain development-time or derived material used during the internship. Users should obtain KEGG resources through the appropriate KEGG access route and follow KEGG's licensing terms for their own use.

## Development status

This repository preserves the working analysis code used during the internship, including debugging utilities and manual handling of module-definition edge cases. It is useful as a record of the computational methodology, but it is not presented as a production-grade general-purpose package.
