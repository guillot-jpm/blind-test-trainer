# src/utils/config_manager.py

"""
This module handles loading and accessing the application configuration
from the config.ini file.
"""

import configparser
import os

# Initialize a ConfigParser object
config = configparser.ConfigParser()

def load_config():
    """
    Loads configuration from config.ini located in the project root.
    """
    # Assuming the script is run from the project root, or the CWD is the project root.
    # A more robust solution might involve finding the project root dynamically.
    config_path = 'config.ini'
    if os.path.exists(config_path):
        config.read(config_path)
    else:
        # A simple way to handle missing config: raise an error.
        # Alternatively, you could log a warning and use default values.
        raise FileNotFoundError(f"Configuration file not found at: {os.path.abspath(config_path)}")

# Load the configuration when the module is first imported.
load_config()

# For easy access to integer values, we can create a helper or modify the structure.
# The acceptance criteria asks for getint() to be used, which happens at the point of access.
# Let's add a note about this.
# Example of how to use it in other modules:
# from src.utils.config_manager import config
# duration = config.getint('Settings', 'snippet_duration_seconds')
