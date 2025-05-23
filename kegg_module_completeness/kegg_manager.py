import os
import time
import pandas as pd
import requests
import pickle
from typing import Dict, Set, List, Optional

class KeggModuleManager:
    """Manages KEGG module data and API interactions."""
    
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
            
        self.module_info_cache = {}
    
    def load_module_to_ko_mapping(self, mapping_file: str) -> Dict[str, Set[str]]:
        """Load module to KO mapping from file.
        
        Args:
            mapping_file: Path to the mapping file
            
        Returns:
            Dictionary mapping module IDs to sets of KO IDs
        """
        module_to_kos = {}
        
        with open(mapping_file, "r") as f:
            for line in f:
                mod, ko = line.strip().split()
                mod = mod.replace("module:", "")
                ko = ko.replace("ko:", "")
                
                if mod not in module_to_kos:
                    module_to_kos[mod] = set()
                    
                module_to_kos[mod].add(ko)
        
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
        
        # Download the latest KEGG module data
        module_to_kos = self._download_kegg_module_data()
        
        # Save to pickle
        with open(pickle_path, 'wb') as f:
            pickle.dump(module_to_kos, f)
        
        return module_to_kos
    
    def _download_kegg_module_data(self):
        """
        Download KEGG module data from the KEGG API.
        
        Returns:
            dict: A dictionary mapping module IDs to sets of KO IDs
        """
        print("Downloading KEGG module data...")
        module_to_kos = {}
        
        # Get a list of all modules
        response = requests.get("https://rest.kegg.jp/list/module")
        if response.status_code != 200:
            raise Exception(f"Failed to download module list: {response.status_code}")
        
        # Parse module IDs
        module_ids = []
        for line in response.text.strip().split("\n"):
            if line:
                module_id = line.split("\t")[0].replace("md:", "")
                module_ids.append(module_id)
        
        print(f"Found {len(module_ids)} KEGG modules")
        
        # For each module, get its KO definitions
        total = len(module_ids)
        for i, module_id in enumerate(module_ids):
            if i % 50 == 0:
                print(f"Processing module {i+1}/{total}")
                
            try:
                url = f"https://rest.kegg.jp/get/{module_id}"
                response = requests.get(url)
                if response.status_code == 200:
                    raw_definition = self._extract_definition(response.text)
                    if raw_definition:
                        ko_set = self._parse_module_definition(raw_definition)
                        module_to_kos[module_id] = ko_set
                
                # Be nice to KEGG API
                time.sleep(0.2)
            except Exception as e:
                print(f"Error processing module {module_id}: {e}")
                
        return module_to_kos
    
    def _extract_definition(self, module_text):
        """Extract the definition line from a KEGG module entry.
        
        Args:
            module_text: Raw text from KEGG API
            
        Returns:
            Definition string or None if not found
        """
        definition = None
        for line in module_text.split("\n"):
            if line.startswith("DEFINITION"):
                definition = line.replace("DEFINITION", "").strip()
            elif definition and line.startswith(" "):
                # Continuation of definition line
                definition += " " + line.strip()
            elif definition:
                # End of definition section
                break
                
        return definition
    
    def _parse_module_definition(self, definition):
        """
        Parse KEGG module definition to extract KO IDs.
        
        KEGG module definitions use a complex syntax with Boolean operations:
        - Spaces indicate AND relationships
        - Commas indicate OR relationships
        - Parentheses are used for grouping
        
        Args:
            definition (str): Module definition from KEGG
            
        Returns:
            set: A set of all KO IDs in the module
        """
        if not definition:
            return set()
            
        # Remove optional indicators (represented by -)
        definition = definition.replace("-", "")
        
        # Extract all KO numbers
        ko_ids = set()
        
        # Regular expression to find K numbers: K followed by 5 digits
        import re
        ko_pattern = re.compile(r"K\d{5}")
        matches = ko_pattern.findall(definition)
        
        for ko in matches:
            ko_ids.add(ko)
            
        return ko_ids
    
    def get_module_info(self, module_ids: List[str]) -> pd.DataFrame:
        """Fetch KEGG module information for a list of module IDs.
        
        Args:
            module_ids: List of module IDs
            
        Returns:
            DataFrame containing module information
        """
        cache_file = os.path.join(self.pickled_data_dir, "kegg_module_info.csv")
        
        # Check if we have a cached version of the data
        if os.path.exists(cache_file):
            try:
                module_info_df = pd.read_csv(cache_file, index_col="Module_ID")
                print(f"Loaded module info from cache: {cache_file}")
                return module_info_df
            except Exception as e:
                print(f"Error reading cache: {e}")
        
        # If no cache, fetch data from KEGG
        module_info = {}
        print("Fetching KEGG module information...")
        for module_id in module_ids:
            module_info[module_id] = self._fetch_module_info(module_id)
        
        # Convert to DataFrame and save cache
        module_info_df = pd.DataFrame.from_dict(module_info, orient='index')
        module_info_df.index.name = "Module_ID"
        module_info_df.to_csv(cache_file)
        return module_info_df
    
    def _fetch_module_info(self, module_id: str) -> Dict[str, str]:
        """Fetch information for a single KEGG module.
        
        Args:
            module_id: Module ID
            
        Returns:
            Dictionary containing module information
        """
        try:
            # Ensure proper module ID format (add 'md:' prefix if needed)
            if not module_id.startswith(('md:', 'M')):
                query_id = f"md:{module_id}"
            else:
                query_id = module_id
            
            # Remove md: prefix if it exists for the API call
            if query_id.startswith('md:'):
                query_id = query_id[3:]
                
            url = f"https://rest.kegg.jp/get/{query_id}"
            response = requests.get(url)
            
            if response.status_code == 200:
                content = response.text
                
                # Parse the module name/description and other details
                name = description = class_info = pathway = ""
                current_field = None
                
                for line in content.split("\n"):
                    if line.startswith("NAME"):
                        current_field = "NAME"
                        name = line.replace("NAME", "").strip()
                    elif line.startswith("DEFINITION"):
                        current_field = "DEFINITION"
                        description = line.replace("DEFINITION", "").strip()
                    elif line.startswith("CLASS"):
                        current_field = "CLASS"
                        class_info = line.replace("CLASS", "").strip()
                    elif line.startswith("PATHWAY"):
                        current_field = "PATHWAY"
                        pathway = line.replace("PATHWAY", "").strip()
                    elif line.strip() and line[0].isspace() and current_field:
                        # Handle continuation lines for multi-line fields
                        if current_field == "NAME":
                            name += " " + line.strip()
                        elif current_field == "DEFINITION":
                            description += " " + line.strip()
                        elif current_field == "CLASS":
                            class_info += " " + line.strip()
                        elif current_field == "PATHWAY":
                            pathway += " " + line.strip()
                
                result = {
                    "Name": name,
                    "Definition": description,
                    "Class": class_info,
                    "Pathway": pathway
                }
                
                # Be nice to the KEGG API - don't overwhelm it
                time.sleep(0.5)
                return result
                
        except Exception as e:
            print(f"Error fetching info for {module_id}: {e}")
        
        return {
            "Name": "",
            "Definition": "",
            "Class": "",
            "Pathway": ""
        }
