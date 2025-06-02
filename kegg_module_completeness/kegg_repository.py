import os
import re
import time
import pickle
import requests
import pandas as pd
from typing import Dict, Set, List, Optional, Any
from datetime import datetime

class KeggRepository:
    """Repository for KEGG data access, providing caching and standardized API interactions."""
    
    def __init__(self, cache_dir: str):
        """Initialize the KEGG repository.
        
        Args:
            cache_dir: Directory to store cached data
        """
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            
        # Use root directory for pickle data instead of cache subdirectory
        self.pickle_dir = "pickled_data"
        if not os.path.exists(self.pickle_dir):
            os.makedirs(self.pickle_dir)
        
        # Initialize caches
        self.module_info_cache = {}
        self.module_definition_cache = {}
        self.module_ko_cache = {}
        
        # API rate limiting parameters
        self.last_request_time = 0
        self.request_delay = 0.2  # seconds between requests
        
    def _make_api_request(self, url: str) -> str:
        """Make a rate-limited API request to KEGG.
        
        Args:
            url: API URL to request
            
        Returns:
            Response text from the API
            
        Raises:
            Exception: If the API request fails
        """
        # Apply rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        
        # Make the request
        response = requests.get(url)
        self.last_request_time = time.time()
        
        if response.status_code != 200:
            raise Exception(f"KEGG API request failed: {url}, status: {response.status_code}")
            
        return response.text
    
    def get_module_list(self) -> List[str]:
        """Get a list of all KEGG modules.
        
        Returns:
            List of module IDs
        """
        cache_path = os.path.join(self.pickle_dir, "module_list.pickle")
        
        # Check for cached data
        if os.path.exists(cache_path):
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        
        # Request from API
        response = self._make_api_request("https://rest.kegg.jp/list/module")
        
        # Parse module IDs
        module_ids = []
        for line in response.strip().split("\n"):
            if line:
                module_id = line.split("\t")[0].replace("md:", "")
                module_ids.append(module_id)
        
        # Cache the result
        with open(cache_path, 'wb') as f:
            pickle.dump(module_ids, f)
            
        return module_ids
    
    def get_module_info(self, module_id: str) -> Dict[str, str]:
        """Get information for a KEGG module.
        
        Args:
            module_id: Module ID
            
        Returns:
            Dictionary with module information
        """
        # Check memory cache
        if module_id in self.module_info_cache:
            return self.module_info_cache[module_id]
        
        # Normalize module ID
        if not module_id.startswith(('md:', 'M')):
            query_id = f"md:{module_id}"
        else:
            query_id = module_id
        
        # Remove md: prefix if it exists for the API call
        if query_id.startswith('md:'):
            query_id = query_id[3:]
            
        # Make API request
        try:
            url = f"https://rest.kegg.jp/get/{query_id}"
            content = self._make_api_request(url)
            
            # Parse module information
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
            
            # Cache the result
            self.module_info_cache[module_id] = result
            return result
            
        except Exception as e:
            print(f"Error fetching info for {module_id}: {e}")
            
        # Return empty result on error
        empty_result = {
            "Name": "",
            "Definition": "",
            "Class": "",
            "Pathway": ""
        }
        self.module_info_cache[module_id] = empty_result
        return empty_result
    
    def get_module_definition(self, module_id: str) -> str:
        """Get the definition string for a KEGG module.
        
        Args:
            module_id: Module ID
            
        Returns:
            Module definition string or empty string if not found
        """
        # Check memory cache
        if module_id in self.module_definition_cache:
            return self.module_definition_cache[module_id]
            
        # Get full module info and extract definition
        module_info = self.get_module_info(module_id)
        definition = module_info.get("Definition", "")
        
        # Cache and return the definition
        self.module_definition_cache[module_id] = definition
        return definition
    
    def get_module_kos(self, module_id: str) -> Set[str]:
        """Get the set of KOs for a KEGG module.
        
        Args:
            module_id: Module ID
            
        Returns:
            Set of KO IDs in the module
        """
        # Check memory cache
        if module_id in self.module_ko_cache:
            return self.module_ko_cache[module_id]
            
        # Get the definition and parse KOs
        definition = self.get_module_definition(module_id)
        ko_set = self._parse_definition_to_kos(definition)
        
        # Cache and return the KO set
        self.module_ko_cache[module_id] = ko_set
        return ko_set
    
    def _parse_definition_to_kos(self, definition: str) -> Set[str]:
        """Parse a module definition to extract KO IDs.
        
        Args:
            definition: Module definition string
            
        Returns:
            Set of KO IDs
        """
        if not definition:
            return set()
            
        # Extract all KO numbers
        ko_ids = set()
        ko_pattern = re.compile(r"K\d{5}")
        matches = ko_pattern.findall(definition)
        
        for ko in matches:
            ko_ids.add(ko)
            
        return ko_ids
    
    def get_all_modules_data(self) -> Dict[str, Dict[str, Any]]:
        """Get data for all KEGG modules.
        
        Returns:
            Dictionary mapping module IDs to their data (definition and KO set)
        """
        # Check for cached data
        cache_path = os.path.join(self.pickle_dir, "all_modules_data.pickle")
        
        if os.path.exists(cache_path):
            with open(cache_path, 'rb') as f:
                modules_data = pickle.load(f)
                print(f"Loaded module data from cache: {cache_path}")
                return modules_data
        
        # Get list of all modules
        module_ids = self.get_module_list()
        print(f"Found {len(module_ids)} KEGG modules")
        
        # Collect data for each module
        modules_data = {}
        for i, module_id in enumerate(module_ids):
            if i % 50 == 0:
                print(f"Processing module {i+1}/{len(module_ids)}")
                
            try:
                definition = self.get_module_definition(module_id)
                ko_set = self._parse_definition_to_kos(definition)
                
                modules_data[module_id] = {
                    'definition': definition,
                    'ko_set': ko_set
                }
            except Exception as e:
                print(f"Error processing module {module_id}: {e}")
          # Cache the results
        with open(cache_path, 'wb') as f:
            pickle.dump(modules_data, f)
        
        return modules_data
    
    def get_module_info_dataframe(self, module_ids: List[str]) -> pd.DataFrame:
        """Get a DataFrame with information for multiple modules.
        
        Args:
            module_ids: List of module IDs
            
        Returns:
            DataFrame with module information
        """
        cache_file = os.path.join(self.pickle_dir, "kegg_module_info.csv")
        
        # Check for cached dataframe
        if os.path.exists(cache_file):
            try:
                module_info_df = pd.read_csv(cache_file, index_col="Module_ID")
                print(f"Loaded module info dataframe from cache: {cache_file}")
                
                # PREVENTION: Check if cache is complete by comparing with all available modules
                all_module_ids = self.get_module_list()
                missing_modules = set(all_module_ids) - set(module_info_df.index)
                
                if missing_modules:
                    print(f"WARNING: Cache is incomplete! Missing {len(missing_modules)} modules.")
                    print(f"Examples of missing modules: {list(missing_modules)[:5]}")
                    print("Regenerating complete cache...")
                    # Force regeneration with ALL modules                    return self._generate_complete_module_cache(cache_file)
                
                return module_info_df
            except Exception as e:
                print(f"Error reading cache: {e}")
        
        # PREVENTION: Always generate complete cache with ALL modules
        return self._generate_complete_module_cache(cache_file)
    
    def _generate_complete_module_cache(self, cache_file: str) -> pd.DataFrame:
        """Generate a complete module information cache with ALL available modules.
        
        Args:
            cache_file: Path to the cache file
            
        Returns:
            Complete DataFrame with all module information
        """
        # Get ALL available modules
        all_module_ids = self.get_module_list()
        print(f"Generating complete cache for {len(all_module_ids)} modules...")
        
        # Collect information for all modules
        module_info = {}
        print("Fetching KEGG module information...")
        for module_id in all_module_ids:
            module_info[module_id] = self.get_module_info(module_id)
        
        # Convert to DataFrame and save cache
        module_info_df = pd.DataFrame.from_dict(module_info, orient='index')
        module_info_df.index.name = "Module_ID"
        module_info_df.to_csv(cache_file)
        print(f"Complete module cache saved with {len(module_info_df)} modules")
        return module_info_df
    
    def validate_module_cache(self) -> bool:
        """Validate that the module info cache is complete and up-to-date.
        
        Returns:
            True if cache is valid, False if it needs regeneration
        """
        cache_file = os.path.join(self.pickle_dir, "kegg_module_info.csv")
        
        if not os.path.exists(cache_file):
            print("Module info cache does not exist")
            return False
        
        # Check cache age (regenerate if older than 30 days)
        cache_age_days = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))).days
        if cache_age_days > 30:
            print(f"Module info cache is {cache_age_days} days old (> 30 days)")
            return False
        
        try:
            # Check cache completeness
            module_info_df = pd.read_csv(cache_file, index_col="Module_ID")
            all_module_ids = self.get_module_list()
            missing_modules = set(all_module_ids) - set(module_info_df.index)
            
            if missing_modules:
                print(f"Module info cache is incomplete - missing {len(missing_modules)} modules")
                return False
            
            print(f"Module info cache is valid ({len(module_info_df)} modules)")
            return True
            
        except Exception as e:
            print(f"Error validating cache: {e}")
            return False
