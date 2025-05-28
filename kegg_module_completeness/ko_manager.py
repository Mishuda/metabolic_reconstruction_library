import os
from typing import Dict, Set

class KoListManager:
    """
    Class to handle parsing and management of KO ID lists.
    """
    
    def __init__(self):
        """Initialize the KO list manager."""
        pass
    
    def parse_ko_list(self, file_path):
        """
        Parse a file containing KO IDs.
        
        Args:
            file_path (str): Path to the file with KO IDs
            
        Returns:
            set: Set of KO identifiers
        """
        with open(file_path, "r") as f:
            ko_set = set(line.strip().upper() for line in f if line.strip())
            
        return ko_set
    
    def get_ko_lists(self, directory: str) -> Dict[str, Set[str]]:
        """Get KO lists from all files in a directory.
        
        Args:
            directory: Directory containing KO list files
            
        Returns:
            Dictionary mapping file names to sets of KO IDs
        """
        ko_lists = {}
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        
        for file_name in files:
            file_path = os.path.join(directory, file_name)
            ko_lists[file_name] = self.parse_ko_list(file_path)
        
        return ko_lists
