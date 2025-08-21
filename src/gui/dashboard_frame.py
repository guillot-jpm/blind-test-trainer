import tkinter as tk
from tkinter import ttk


class DashboardFrame(ttk.Frame):
    """
    A frame dedicated to displaying advanced statistics and visualizations.
    """

    def __init__(self, parent, controller):
        """
        Initializes the DashboardFrame.
        """
        super().__init__(parent, style="TFrame")
        self.controller = controller

        # --- Main Container ---
        main_container = ttk.Frame(self, style="TFrame", padding="20 10")
        main_container.pack(expand=True, fill="both")
        main_container.grid_rowconfigure(1, weight=1)
        main_container.grid_rowconfigure(2, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_columnconfigure(1, weight=1)

        # --- Header ---
        header_frame = ttk.Frame(main_container, style="TFrame")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")

        title_label = ttk.Label(
            header_frame,
            text="Statistics Dashboard",
            style="Title.TLabel"
        )
        title_label.pack(side="left", fill="x", expand=True)

        back_button = ttk.Button(
            header_frame,
            text="Back to Main Menu",
            command=lambda: self.controller.show_frame("MainMenuFrame"),
            style="Back.TButton"
        )
        back_button.pack(side="right")

        # --- Placeholder Frames for Charts ---
        # Top Row
        mastery_chart_frame = ttk.LabelFrame(
            main_container,
            text="Mastery Chart",
            style="TLabelframe"
        )
        mastery_chart_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        ttk.Label(mastery_chart_frame, text="[Mastery Chart Placeholder]").pack(padx=5, pady=5)

        problem_songs_frame = ttk.LabelFrame(
            main_container,
            text="Problem Songs",
            style="TLabelframe"
        )
        problem_songs_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        ttk.Label(problem_songs_frame, text="[Problem Songs List Placeholder]").pack(padx=5, pady=5)

        # Bottom Row
        history_chart_frame = ttk.LabelFrame(
            main_container,
            text="Practice History",
            style="TLabelframe"
        )
        history_chart_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        ttk.Label(history_chart_frame, text="[Practice History Chart Placeholder]").pack(padx=5, pady=5)
