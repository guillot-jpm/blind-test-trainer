import configparser
import sys
import tkinter as tk
from tkinter import messagebox

import logging
import pygame
from src.gui.main_window import MainWindow
from src.utils.config_manager import load_config
from src.services.spotify_service import initialize_spotify_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s]: %(message)s",
    filename="app.log",
    filemode="a",  # 'a' for append
)


if __name__ == "__main__":
    logging.info("Application started.")
    try:
        # 1. Load application configuration
        new_config_created = load_config()
    except configparser.Error:
        # Use a hidden Tk root window to show the error message
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Configuration Error",
            "Error: Configuration file 'config.ini' is corrupt or unreadable."
        )
        sys.exit(1)

    # 2. Initialize external services
    initialize_spotify_service()

    # Initialize Pygame Mixer
    pygame.mixer.init()
    logging.info("Pygame mixer initialized.")

    # 3. Create and run the main application window
    app = MainWindow(new_config_created=new_config_created)
    app.mainloop()
