import tkinter as tk
from tkinter import ttk


class MainMenuFrame(tk.Frame):
    """
    The main menu frame, serving as a dashboard with key statistics and navigation.
    """

    def __init__(self, parent, controller):
        """
        Initializes the MainMenuFrame.

        Args:
            parent (tk.Widget): The parent widget.
            controller (tk.Tk): The main application window (controller).
        """
        super().__init__(parent)
        self.controller = controller

        # --- Main Container ---
        main_container = tk.Frame(self)
        main_container.pack(expand=True)

        # --- Statistics Section (Placeholder) ---
        stats_frame = ttk.LabelFrame(main_container, text="Summary Statistics", padding="10")
        stats_frame.pack(pady=20, padx=20, fill="x")

        stats_label = tk.Label(
            stats_frame,
            text="Detailed summary statistics will be displayed here.\n(As per US 6.2)",
            justify="center",
            pady=10
        )
        stats_label.pack()

        # --- Session Buttons ---
        start_standard_button = ttk.Button(
            main_container,
            text="Start Standard Session",
            command=self.start_standard_session,
            width=30
        )
        start_standard_button.pack(pady=10)

        start_challenge_button = ttk.Button(
            main_container,
            text="Start Challenge Session",
            command=self.start_challenge_session,
            width=30
        )
        start_challenge_button.pack(pady=10)

        # --- Library Management Button ---
        manage_library_button = ttk.Button(
            main_container,
            text="Manage My Library",
            command=self.manage_library,
            width=30
        )
        manage_library_button.pack(pady=20)

    def start_standard_session(self):
        """
        Starts a new standard quiz session.
        """
        self._start_session("Standard")

    def start_challenge_session(self):
        """
        Starts a new challenge quiz session.
        """
        self._start_session("Challenge")

    def _start_session(self, mode):
        """
        Starts a new quiz with the specified mode.
        """
        quiz_view = self.controller.frames["QuizView"]
        quiz_view.start_new_quiz(mode=mode)

        # The start_new_quiz method will handle showing the main menu
        # if there are no songs due.
        if quiz_view.session:
            self.controller.show_frame("QuizView")

    def manage_library(self):
        """
        Switches to the Library Management frame.
        """
        self.controller.show_frame("LibraryManagementFrame")
