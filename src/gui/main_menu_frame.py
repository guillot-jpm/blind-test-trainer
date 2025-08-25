import tkinter as tk
from tkinter import ttk
import logging


class MainMenuFrame(ttk.Frame):
    """
    The main menu frame, serving as a dashboard with key statistics and navigation.
    """

    def __init__(self, parent, controller):
        """
        Initializes the MainMenuFrame.
        """
        super().__init__(parent, style="TFrame")
        self.controller = controller

        # --- Main Container ---
        main_container = ttk.Frame(self, style="TFrame")
        main_container.pack(expand=True, fill="both", padx=20, pady=10)

        # --- Title ---
        title_label = ttk.Label(
            main_container,
            text="Blind Test Trainer",
            style="Title.TLabel"
        )
        title_label.pack(fill="x", pady=20)

        # --- Buttons Frame ---
        buttons_frame = ttk.Frame(main_container, style="TFrame")
        buttons_frame.pack(pady=10, fill="x", padx=20)
        buttons_frame.columnconfigure(0, weight=1)

        # --- Session Buttons ---
        start_standard_button = ttk.Button(
            buttons_frame,
            text="Start Standard Session",
            command=self.start_standard_session,
            style="TButton"
        )
        start_standard_button.grid(row=0, column=0, sticky="ew", pady=5)

        start_challenge_button = ttk.Button(
            buttons_frame,
            text="Start Challenge Session",
            command=self.start_challenge_session,
            style="TButton"
        )
        start_challenge_button.grid(row=1, column=0, sticky="ew", pady=5)

        start_gauntlet_button = ttk.Button(
            buttons_frame,
            text="Start Gauntlet Mode",
            command=self.start_gauntlet_session,
            style="TButton"
        )
        start_gauntlet_button.grid(row=2, column=0, sticky="ew", pady=5)

        learning_lab_button = ttk.Button(
            buttons_frame,
            text="Enter Learning Lab",
            command=lambda: self.controller.show_frame("LearningLabView"),
            style="TButton"
        )
        learning_lab_button.grid(row=3, column=0, sticky="ew", pady=5)

        # --- Dashboard Button ---
        view_dashboard_button = ttk.Button(
            buttons_frame,
            text="View Dashboard",
            command=lambda: self.controller.show_frame("DashboardFrame"),
            style="TButton"
        )
        view_dashboard_button.grid(row=4, column=0, sticky="ew", pady=5)

        # --- Library Management Button ---
        manage_library_button = ttk.Button(
            buttons_frame,
            text="Manage My Library",
            command=self.manage_library,
            style="TButton"
        )
        manage_library_button.grid(row=5, column=0, sticky="ew", pady=(15, 5))

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

    def start_gauntlet_session(self):
        """
        Starts a new gauntlet quiz session.
        """
        self._start_session("Gauntlet")

    def _start_session(self, mode):
        """
        Starts a new quiz with the specified mode.
        """
        logging.info(f"User starts a \"{mode} Session\".")
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
