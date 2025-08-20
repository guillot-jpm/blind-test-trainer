import tkinter as tk
from tkinter import ttk
from collections import Counter

from src.data.database_manager import (
    get_total_song_count,
    get_all_release_years,
    get_all_srs_intervals,
)


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
        title_label.pack(fill="x")

        # --- Statistics Section ---
        stats_frame = ttk.LabelFrame(
            main_container,
            text="Summary Statistics",
            style="TLabelframe"
        )
        stats_frame.pack(pady=20, padx=20, fill="x")
        stats_frame.columnconfigure(0, weight=1)

        self.total_songs_label = ttk.Label(stats_frame, text="Total Songs: ...")
        self.total_songs_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)

        self.decades_label = ttk.Label(stats_frame, text="Decades: ...")
        self.decades_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)

        self.mastery_label = ttk.Label(stats_frame, text="Mastery: ...")
        self.mastery_label.grid(row=2, column=0, sticky="w", padx=5, pady=2)

        self.update_statistics()

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

        # --- Library Management Button ---
        manage_library_button = ttk.Button(
            buttons_frame,
            text="Manage My Library",
            command=self.manage_library,
            style="TButton"
        )
        manage_library_button.grid(row=2, column=0, sticky="ew", pady=(15, 5))

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
