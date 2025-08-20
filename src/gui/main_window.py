import sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, ttk
import logging

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
        self.geometry("650x600") # Increased size for better layout

        # --- Style and Font configuration ---
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            print("'clam' theme not available, using default.")

        # Define fonts
        self.title_font = ("Arial", 18, "bold")
        self.header_font = ("Arial", 14, "bold")
        self.body_font = ("Arial", 12)
        self.button_font = ("Arial", 11, "bold")
        self.small_font = ("Arial", 10)

        # --- Configure widget styles ---
        background_color = "#f0f0f0"
        self.configure(background=background_color)

        # General Label Style
        self.style.configure("TLabel",
                             font=self.body_font,
                             background=background_color)
        # Title Label Style
        self.style.configure("Title.TLabel",
                             font=self.title_font,
                             padding="10 10 10 20",
                             anchor="center",
                             background=background_color)
        # Header Label Style
        self.style.configure("Header.TLabel",
                             font=self.header_font,
                             background=background_color)

        # General Button Style
        self.style.configure("TButton",
                             font=self.button_font,
                             padding="10 5",
                             anchor="center")
        # Back/Navigation Button Style
        self.style.configure("Back.TButton",
                             font=self.small_font,
                             padding="5 2")

        # LabelFrame Style
        self.style.configure("TLabelframe",
                             labelmargins="10 0",
                             padding="10 10",
                             background=background_color)
        self.style.configure("TLabelframe.Label",
                             font=self.header_font,
                             background=background_color)

        db_path = config.get("Paths", "database_file")
        try:
            connect(db_path)
            initialize_database()
        except sqlite3.Error as e:
            logging.critical(
                "Failure to connect to the local database on startup. "
                f"Reason: {e}"
            )
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
        container = ttk.Frame(self, padding="10")
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

        # Special handling for frames that need refreshing
        if page_name == "MainMenuFrame":
            frame.update_statistics()
        elif page_name == "LibraryManagementFrame":
            frame.on_show()

        frame.tkraise()

    def on_close(self):
        """
        Handles the window close event by disconnecting from the database
        and destroying the window.
        """
        logging.info("Application closed cleanly.")
        disconnect()
        self.destroy()
