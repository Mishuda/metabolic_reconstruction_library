"""
KEGG Module Completeness Analysis Package

This package provides tools for analyzing the completeness of KEGG modules
based on sets of KO identifiers.
"""

# Make key classes available at the package level for convenience
from .ko_manager import KoListManager
from .kegg_manager import KeggModuleManager
from .completeness_calculator import CompletenessCalculator
from .report_generator import ReportGenerator
