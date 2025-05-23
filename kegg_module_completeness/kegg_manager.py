import os
import pickle
import pandas as pd
from typing import Dict, Set, List, Optional, Any, Union
from .kegg_repository import KeggRepository

class KeggModuleManager:
    """Manages KEGG module data using the repository pattern."""
    
    def __init__(self, cache_dir: str):
        """Initialize the KEGG module manager.
        
        Args:
            cache_dir: Directory to store cached module information
        """
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        # Create pickled_data directory
        self.pickled_data_dir = os.path.join(cache_dir, "pickled_data")
        if not os.path.exists(self.pickled_data_dir):
            os.makedirs(self.pickled_data_dir)
            
        # Initialize the repository
        self.repository = KeggRepository(cache_dir)
    
    def load_module_to_ko_mapping(self, mapping_file: str) -> Dict[str, Dict[str, Union[Set[str], str]]]:
        """Load module to KO mapping from file.
        
        Args:
            mapping_file: Path to the mapping file
            
        Returns:
            Dictionary mapping module IDs to their data
        """
        module_to_kos = {}
        
        with open(mapping_file, "r") as f:
            for line in f:
                mod, ko = line.strip().split()
                mod = mod.replace("module:", "")
                ko = ko.replace("ko:", "")
                
                if mod not in module_to_kos:
                    module_to_kos[mod] = {'ko_set': set(), 'definition': ''}
                    
                module_to_kos[mod]['ko_set'].add(ko)
        
        # For each module, get its definition from the repository if available
        for module_id in list(module_to_kos.keys()):
            definition = self.repository.get_module_definition(module_id)
            if definition:
                module_to_kos[module_id]['definition'] = definition
        
        return module_to_kos
    
    def load_pickled_mapping(self, pickle_filename):
        """
        Load module to KO mapping from a pickle file in the pickled_data directory.
        
        Args:
            pickle_filename (str): Filename of the pickle file
            
        Returns:
            dict: A dictionary mapping module IDs to their KO requirements
        """
        pickle_path = os.path.join(self.pickled_data_dir, pickle_filename)
        with open(pickle_path, 'rb') as f:
            return pickle.load(f)
    
    def download_and_pickle_mapping(self, pickle_filename):
        """
        Download fresh KEGG module data and save it to a pickle file.
        
        Args:
            pickle_filename (str): Filename for the pickle file
            
        Returns:
            dict: A dictionary mapping module IDs to their KO requirements
        """
        # Create the pickle path in the pickled_data directory
        pickle_path = os.path.join(self.pickled_data_dir, pickle_filename)
        
        # Download the latest KEGG module data using the repository
        module_to_kos = self.repository.get_all_modules_data()
        
        # Save to pickle
        with open(pickle_path, 'wb') as f:
            pickle.dump(module_to_kos, f)
        
        return module_to_kos
    
    def get_module_info(self, module_ids: List[str]) -> pd.DataFrame:
        """Fetch KEGG module information for a list of module IDs.
        
        Args:
            module_ids: List of module IDs
            
        Returns:
            DataFrame containing module information
        """
        return self.repository.get_module_info_dataframe(module_ids)
