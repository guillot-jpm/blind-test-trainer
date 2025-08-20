import sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, ttk

from src.gui.main_menu_frame import MainMenuFrame
from src.gui.quiz_view_frame import QuizView
from src.gui.library_management_frame import LibraryManagementFrame
from src.data.database_manager import (
    connect,
    disconnect,
    initialize_database,
)
from src.utils.config_manager import config


class MainWindow(tk.Tk):
    """
    The main application window, responsible for initializing the application,
    handling the main user interface, and managing the application's lifecycle.
    It acts as a controller to switch between different frames (views).
    """

    def __init__(self, new_config_created=False):
        """
        Initializes the main window, sets up the database connection,
        and creates the main container for frames.
        """
        super().__init__()
        self.title("Blind Test Trainer")
        self.geometry("550x550")

        # --- Style and Font configuration ---
        self.style = ttk.Style(self)
        self.title_font = ("Ubuntu", 18, "bold")
        self.body_font = ("Ubuntu", 12)
        self.button_font = ("Ubuntu", 12, "bold")

        # Configure ttk styles
        self.style.configure("MainMenu.TButton", font=self.button_font)
        self.style.configure("Stats.TLabel", font=self.body_font)

        db_path = config.get("Paths", "database_file")
        try:
            connect(db_path)
            initialize_database()
        except sqlite3.Error:
            messagebox.showerror(
                "Fatal Error",
                f"Fatal Error: Could not connect to the database at {db_path}. "
                "Please check the file's integrity and permissions."
            )
            self.destroy()
            sys.exit(1)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        if new_config_created:
            messagebox.showinfo(
                "Configuration Created",
                "A new 'config.ini' has been created. "
                "Please edit it to set your music folder path.",
            )

        # Main container to hold all frames
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.container = container

        self.frames = {}

        for F in (MainMenuFrame, QuizView, LibraryManagementFrame):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("MainMenuFrame")

    def show_frame(self, page_name):
        """
        Raises the specified frame to the top of the stacking order.
        If the target frame is the MainMenuFrame, its statistics are refreshed.
        """
        frame = self.frames[page_name]

        # Refresh stats if we are showing the main menu
        if page_name == "MainMenuFrame":
            frame.update_statistics()

        frame.tkraise()

    def on_close(self):
        """
        Handles the window close event by disconnecting from the database
        and destroying the window.
        """
        disconnect()
        self.destroy()
