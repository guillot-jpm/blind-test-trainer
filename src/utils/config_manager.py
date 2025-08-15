# src/utils/config_manager.py

"""
This module handles loading and accessing the application configuration
from the config.ini file.
"""

import configparser
import os
import shutil

# Initialize a ConfigParser object
config = configparser.ConfigParser()

def load_config():
    """
    Loads configuration from config.ini. If it doesn't exist, creates it from
    the template and returns True. Otherwise, loads the config and returns False.
    """
    config_path = 'config.ini'
    if not os.path.exists(config_path):
        template_path = 'config.ini.template'
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Critical error: '{config_path}' and '{template_path}' not found.")

        shutil.copy(template_path, config_path)
        config.read(config_path)
        return True

    config.read(config_path)
    return False


# Configuration is no longer loaded on module import.
# It must be explicitly loaded by the application's main entry point.

# For easy access to integer values, we can create a helper or modify the structure.
# The acceptance criteria asks for getint() to be used, which happens at the point of access.
# Let's add a note about this.
# Example of how to use it in other modules:
# from src.utils.config_manager import config
# duration = config.getint('Settings', 'snippet_duration_seconds')
