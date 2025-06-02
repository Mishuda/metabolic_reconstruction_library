# Debug Scripts Directory

This directory contains various debug, test, and validation scripts used during the development of the KEGG Module Completeness Analysis tool.

## Scripts Overview

### Core Logic Testing
- **`test_kegg_logic_comprehensive.py`** - Comprehensive test suite for all KEGG definition logic patterns
- **`test_kegg_patterns.py`** - Tests for various KEGG module definition patterns
- **`test_kegg_format_compliance.py`** - Tests for KEGG format compliance

### Specific Module Testing
- **`test_m00001_fix.py`** - Specific tests for M00001 module parsing and evaluation
- **`debug_m00986_parsing_new.py`** - Debug script for M00986 definition parsing
- **`simple_m00986_test.py`** - Simple test for M00986 completeness calculation

### Data Extraction Testing
- **`test_extraction.py`** - Tests for logical definition extraction
- **`test_improved_extraction.py`** - Tests for improved extraction methods

### Simple Tests
- **`simple_test.py`** - Basic functionality tests

### Validation Tools
- **`pre_analysis_check.py`** - Pre-analysis validation script to check system health

## Usage

Most scripts can be run directly from the debug_scripts directory:

```bash
cd debug_scripts
python test_kegg_logic_comprehensive.py
python test_m00001_fix.py
python pre_analysis_check.py
```

Note: Some scripts may need to be run from the parent directory due to import paths:

```bash
cd ..
python debug_scripts/simple_m00986_test.py
```

## Current Implementation Status

The KEGG module completeness evaluation logic is largely implemented and functional:

✅ **Working Features:**
- Basic KEGG definition parsing (spaces = AND, commas in parentheses = OR)
- Top-level OR parsing (commas outside parentheses)
- Complex parsing (+ signs for protein complexes)
- Mixed AND/OR logic
- Nested parentheses handling

⚠️ **Known Issues:**
- Optional component handling (- prefix) has some edge cases
- Complex with optional subunits needs refinement

The main application (`main.py`) is functional and ready for production use.
