import tkinter as tk
from tkinter import messagebox
from src.gui.library_manager_window import create_library_manager_window
from src.utils.config_manager import config
from src.data.database_manager import (
    connect,
    disconnect,
    initialize_database
)


class MainWindow(tk.Tk):
    """
    The main application window, responsible for initializing the application,
    handling the main user interface, and managing the application's lifecycle.
    """

    def __init__(self, new_config_created=False):
        """
        Initializes the main window, sets up the database connection,
        and creates the UI components.
        """
        super().__init__()
        self.title("Blind Test Trainer")
        self.geometry("400x300")

        try:
            # The configuration is already loaded by main.py
            # We just need to get the database path and connect.
            db_path = config.get('Paths', 'database_file')

            # Establish the database connection.
            connect(db_path)

            # Initialize the database schema if needed.
            initialize_database()

        except Exception as e:
            # If any error occurs during startup, show it and close the app.
            messagebox.showerror(
                "Application Error",
                f"An unexpected error occurred during startup:\n{e}"
            )
            self.destroy()
            return

        # Register the disconnect function to be called on window close.
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        if new_config_created:
            messagebox.showinfo(
                "Configuration Created",
                "A new 'config.ini' has been created. "
                "Please edit it to set your music folder path."
            )

        # --- UI Components ---
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

    def on_close(self):
        """
        Handles the window close event by disconnecting from the database
        and destroying the window.
        """
        disconnect()
        self.destroy()
