import tkinter as tk
from tkinter import ttk
from collections import Counter

from src.data.database_manager import (
    get_total_song_count,
    get_all_release_years,
    get_all_srs_intervals,
)


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

        # --- Style Configuration ---
        style = ttk.Style()
        style.configure(
            "MainMenu.TButton",
            font=self.controller.button_font,
            padding=10
        )
        style.configure("Stats.TLabel", font=self.controller.body_font, anchor="w")

        # --- Main Container ---
        main_container = tk.Frame(self)
        main_container.pack(expand=True)

        # --- Title ---
        title_label = tk.Label(
            main_container,
            text="Blind Test Trainer",
            font=self.controller.title_font
        )
        title_label.pack(pady=(20, 10))

        # --- Statistics Section ---
        stats_frame = ttk.LabelFrame(main_container, text="Summary Statistics", padding="10")
        stats_frame.pack(pady=10, padx=20, fill="x")
        stats_frame.columnconfigure(0, weight=1)

        self.total_songs_label = ttk.Label(stats_frame, text="Total Songs: ...", style="Stats.TLabel")
        self.total_songs_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)

        self.decades_label = ttk.Label(stats_frame, text="Decades: ...", style="Stats.TLabel")
        self.decades_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)

        self.mastery_label = ttk.Label(stats_frame, text="Mastery: ...", style="Stats.TLabel")
        self.mastery_label.grid(row=2, column=0, sticky="w", padx=5, pady=2)

        self.update_statistics()

        # --- Session Buttons ---
        start_standard_button = ttk.Button(
            main_container,
            text="Start Standard Session",
            command=self.start_standard_session,
            style="MainMenu.TButton",
            width=30
        )
        start_standard_button.pack(pady=10)

        start_challenge_button = ttk.Button(
            main_container,
            text="Start Challenge Session",
            command=self.start_challenge_session,
            style="MainMenu.TButton",
            width=30
        )
        start_challenge_button.pack(pady=10)

        # --- Library Management Button ---
        manage_library_button = ttk.Button(
            main_container,
            text="Manage My Library",
            command=self.manage_library,
            style="MainMenu.TButton",
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

    def update_statistics(self):
        """
        Fetches and displays summary statistics for the music library.
        """
        # 1. Get Total Songs
        total_songs = get_total_song_count()
        self.total_songs_label.config(text=f"Total Songs: {total_songs}")

        if total_songs == 0:
            self.decades_label.config(text="Decades: N/A")
            self.mastery_label.config(text="Mastery: N/A")
            return

        # 2. Get and Calculate Decade Distribution
        years = get_all_release_years()
        if not years:
            self.decades_label.config(text="Decades: N/A")
        else:
            decades = [f"{(year // 10) * 10}s" for year in years]
            decade_counts = Counter(decades)
            total_decades = len(decades)

            # Get top 3 decades
            top_3_decades = decade_counts.most_common(3)

            decade_str_parts = []
            for decade, count in top_3_decades:
                percentage = (count / total_decades) * 100
                decade_str_parts.append(f"{decade} ({percentage:.0f}%)")
            self.decades_label.config(text="Decades: " + ", ".join(decade_str_parts))

        # 3. Get and Calculate Mastery Breakdown
        intervals = get_all_srs_intervals()
        if not intervals:
            self.mastery_label.config(text="Mastery: N/A")
        else:
            mastery_counts = {
                "Not Yet Learned": 0,
                "Learning": 0,
                "Mastered": 0
            }
            for interval in intervals:
                if interval < 7:
                    mastery_counts["Not Yet Learned"] += 1
                elif 7 <= interval < 30:
                    mastery_counts["Learning"] += 1
                else:
                    mastery_counts["Mastered"] += 1

            mastery_str = (
                f"Mastery: Not Yet Learned ({mastery_counts['Not Yet Learned']}), "
                f"Learning ({mastery_counts['Learning']}), "
                f"Mastered ({mastery_counts['Mastered']})"
            )
            self.mastery_label.config(text=mastery_str)
