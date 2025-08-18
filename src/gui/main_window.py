import tkinter as tk
from tkinter import messagebox
from src.gui.library_manager_window import create_library_manager_window
from src.utils.config_manager import load_config, config
from src.data.database_manager import initialize_database

class MainWindow(tk.Tk):
    """
    This class represents the Main window.
    """
    def __init__(self):
        """
        Initializes the Main window.
        """
        new_config_created = load_config()
        db_path = config.get('Paths', 'database_file')
        initialize_database(db_path)

        super().__init__()
        self.title("Main Window")

        if new_config_created:
            messagebox.showinfo(
                "Configuration Created",
                "Configuration file not found. A new 'config.ini' has been created for you. "
                "Please edit this file to set your music folder path before adding songs to the library."
            )

        self.geometry("400x300")

        self.launch_button = tk.Button(
            self,
            text="Launch Library Manager",
            command=self.launch_library_manager
        )
        self.launch_button.pack(pady=20)

    def launch_library_manager(self):
        """
        Launches the Library Manager window.
        """
        create_library_manager_window(self)
