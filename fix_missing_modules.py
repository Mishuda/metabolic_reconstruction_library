#!/usr/bin/env python3
"""
Fix missing modules in kegg_module_info.csv

This script regenerates the kegg_module_info.csv file to include all modules,
including missing ones like M00986.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from kegg_module_completeness.kegg_repository import KeggRepository

def main():
    # Initialize repository
    cache_dir = "pickled_data"
    repository = KeggRepository(cache_dir)
    
    print("Getting complete list of KEGG modules...")
    
    # Get all modules from KEGG
    all_module_ids = repository.get_module_list()
    print(f"Found {len(all_module_ids)} total modules")
    
    # Check if M00986 is in the list
    if "M00986" in all_module_ids:
        print("✓ M00986 is in the module list")
    else:
        print("✗ M00986 is NOT in the module list")
        return 1
    
    # Remove existing cache file to force regeneration
    cache_file = os.path.join(cache_dir, "kegg_module_info.csv")
    if os.path.exists(cache_file):
        print(f"Removing existing cache file: {cache_file}")
        os.remove(cache_file)
    
    # Force regeneration of module info dataframe for ALL modules
    print("Regenerating complete module information dataframe...")
    print("This may take several minutes as it needs to fetch data for all modules...")
    
    module_info_df = repository.get_module_info_dataframe(all_module_ids)
    
    print(f"Successfully created module info dataframe with {len(module_info_df)} modules")
      # Check if M00986 is now included
    if "M00986" in module_info_df.index:
        print("✓ M00986 is now in the module info dataframe")
        m00986_info = module_info_df.loc["M00986"]
        print("  Name:", m00986_info['Name'])
        print("  Definition:", m00986_info['Definition'])
        print("  Class:", m00986_info['Class'])
    else:
        print("✗ M00986 is still NOT in the module info dataframe")
        return 1
    
    print("Module information cache has been successfully regenerated!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
