#!/usr/bin/env python3
"""
Pre-Analysis Validation Script

This script should be run before any metabolic reconstruction analysis
to ensure the system is properly configured and all modules are available.

Usage: python pre_analysis_check.py [--regenerate-cache]
"""

import os
import sys
import argparse
import pandas as pd
from datetime import datetime
from kegg_module_completeness.kegg_repository import KeggRepository

def check_system_health():
    """Perform a quick system health check."""
    print("🔍 System Health Check")
    print("-" * 30)
    
    # Check critical files exist
    critical_files = [
        'kegg_info/list_kegg_module',
        'kegg_info/module_ko_mapping.tsv',
        'pickled_data/kegg_module_info.csv'
    ]
    
    missing_files = []
    for file_path in critical_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing critical files: {missing_files}")
        return False
    else:
        print("✅ All critical files present")
    
    # Check cache validity
    repo = KeggRepository('pickled_data')
    if repo.validate_module_cache():
        print("✅ Module cache is valid and complete")
        
        # Quick module count check
        cache_file = os.path.join('pickled_data', 'kegg_module_info.csv')
        cache_df = pd.read_csv(cache_file, index_col='Module_ID')
        print(f"✅ Cache contains {len(cache_df)} modules")
        
        return True
    else:
        print("❌ Module cache validation failed")
        return False

def check_important_modules():
    """Check that critical modules for common analyses are present."""
    print("\n🔍 Important Modules Check")
    print("-" * 30)
    
    # Define modules commonly needed for metabolic reconstruction
    important_modules = {
        'M00986': 'Sulfur reduction, sulfur => sulfide',
        'M00001': 'Glycolysis (Embden-Meyerhof pathway)',
        'M00002': 'Glycolysis, core module',
        'M00003': 'Gluconeogenesis',
        'M00004': 'Pentose phosphate pathway',
        'M00005': 'PRPP biosynthesis',
        'M00006': 'Pentose phosphate pathway, oxidative phase',
        'M00007': 'Pentose phosphate pathway, non-oxidative phase',
        'M00008': 'Entner-Doudoroff pathway',
        'M00009': 'Citrate cycle (TCA cycle)',
        'M00010': 'Citrate cycle, first carbon oxidation',
        'M00011': 'Citrate cycle, second carbon oxidation',
        'M00987': 'Sulfur oxidation pathway',
        'M00988': 'Sulfur cycle pathway'
    }
    
    cache_file = os.path.join('pickled_data', 'kegg_module_info.csv')
    cache_df = pd.read_csv(cache_file, index_col='Module_ID')
    
    missing_modules = []
    for module_id, description in important_modules.items():
        if module_id in cache_df.index:
            print(f"✅ {module_id}: {description}")
        else:
            print(f"❌ MISSING: {module_id}: {description}")
            missing_modules.append(module_id)
    
    if missing_modules:
        print(f"\n⚠️ WARNING: {len(missing_modules)} important modules are missing!")
        return False
    else:
        print("\n✅ All important modules are present")
        return True

def check_ko_mapping_sample():
    """Check a sample of KO → Module mappings."""
    print("\n🔍 KO → Module Mapping Check")
    print("-" * 30)
    
    # Test critical mappings
    test_mappings = [
        ('K18367', 'M00986', 'Sulfur reduction'),
        ('K00844', 'M00001', 'Glycolysis'),
        ('K01810', 'M00001', 'Glycolysis'),
        ('K00134', 'M00009', 'TCA cycle')
    ]
    
    repo = KeggRepository('pickled_data')
    
    all_good = True
    for ko_id, expected_module, pathway in test_mappings:
        try:
            module_kos = repo.get_module_kos(expected_module)
            if ko_id in module_kos:
                print(f"✅ {ko_id} → {expected_module} ({pathway})")
            else:
                print(f"❌ {ko_id} NOT found in {expected_module} ({pathway})")
                all_good = False
        except Exception as e:
            print(f"❌ Error testing {ko_id} → {expected_module}: {e}")
            all_good = False
    
    return all_good

def regenerate_cache_if_needed(force_regenerate=False):
    """Regenerate cache if needed or forced."""
    print("\n🔄 Cache Management")
    print("-" * 30)
    
    repo = KeggRepository('pickled_data')
    
    if force_regenerate:
        print("🔄 Forcing cache regeneration...")
        # Remove existing cache to force regeneration
        cache_file = os.path.join('pickled_data', 'kegg_module_info.csv')
        if os.path.exists(cache_file):
            os.remove(cache_file)
        
        # Trigger regeneration
        all_modules = repo.get_module_list()
        df = repo.get_module_info_dataframe(all_modules)
        print(f"✅ Cache regenerated with {len(df)} modules")
        return True
    
    elif not repo.validate_module_cache():
        print("🔄 Cache validation failed - regenerating...")
        all_modules = repo.get_module_list()
        df = repo.get_module_info_dataframe(all_modules)
        print(f"✅ Cache regenerated with {len(df)} modules")
        return True
    
    else:
        print("✅ Cache is valid - no regeneration needed")
        return True

def main():
    """Main function to run pre-analysis checks."""
    parser = argparse.ArgumentParser(description="Pre-analysis validation for metabolic reconstruction")
    parser.add_argument('--regenerate-cache', action='store_true', 
                       help='Force regeneration of module cache')
    
    args = parser.parse_args()
    
    print("🚀 Pre-Analysis Validation")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Change to correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Run all checks
    checks = [
        ("System Health", check_system_health),
        ("Important Modules", check_important_modules),
        ("KO→Module Mapping", check_ko_mapping_sample),
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            if not check_func():
                all_passed = False
        except Exception as e:
            print(f"❌ {check_name} failed with error: {e}")
            all_passed = False
    
    # Handle cache regeneration
    if not regenerate_cache_if_needed(args.regenerate_cache):
        all_passed = False
    
    # Final summary
    print("\n" + "=" * 50)
    print("🏁 PRE-ANALYSIS VALIDATION SUMMARY")
    print("=" * 50)
    
    if all_passed:
        print("✅ ALL CHECKS PASSED - System ready for analysis!")
        print("\n💡 You can now run your metabolic reconstruction analysis with confidence.")
        return 0
    else:
        print("❌ Some checks failed - please address issues before analysis")
        print("\n💡 Try running with --regenerate-cache flag to fix cache issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())
