import requests
import time
import os
import pandas as pd
import re

def fetch_module_definition(module_id):
    """
    Fetch a module definition from the KEGG API.
    
    Args:
        module_id (str): KEGG module ID
        
    Returns:
        str: Module definition string or empty string if not found
    """
    # Clean up the module ID format
    if module_id.startswith('md:'):
        query_id = module_id[3:]
    else:
        query_id = module_id
    
    url = f"https://rest.kegg.jp/get/{query_id}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            content = response.text
            
            # Extract the definition
            definition = ""
            for line in content.split('\n'):
                if line.startswith('DEFINITION'):
                    definition = line.replace('DEFINITION', '').strip()
                elif definition and line.startswith(' '):
                    definition += ' ' + line.strip()
                elif definition:
                    # We've finished reading the definition
                    break
            
            return definition
    except Exception as e:
        print(f"Error fetching definition for {module_id}: {e}")
    
    return ""

def update_completeness_calculator(calculator, module_ids):
    """
    Update the completeness calculator with actual module definitions.
    
    Args:
        calculator (CompletenessCalculator): The calculator to update
        module_ids (list): List of module IDs to fetch definitions for
        
    Returns:
        dict: Dictionary mapping module IDs to their definitions
    """
    module_definitions = {}
    
    for module_id in module_ids:
        definition = fetch_module_definition(module_id)
        if definition:
            module_definitions[module_id] = definition
            # Be nice to the KEGG API
            time.sleep(0.5)
    
    return module_definitions
