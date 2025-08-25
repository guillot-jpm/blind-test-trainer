import tkinter as tk
from tkinter import ttk

class LearningLabView(ttk.Frame):
    """
    A view dedicated to the Learning Lab for passive listening and song discovery.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- Main container ---
        main_container = ttk.Frame(self)
        main_container.pack(expand=True, fill="both", padx=20, pady=10)
        main_container.column_configure(0, weight=1)

        # --- Title ---
        title_label = ttk.Label(main_container, text="Learning Lab", style="Title.TLabel")
        title_label.grid(row=0, column=0, columnspan=3, pady=20)

        # --- Album Art Placeholder ---
        album_art_frame = ttk.Frame(main_container, width=300, height=300, style="TFrame")
        album_art_frame.grid(row=1, column=0, columnspan=3, pady=20)
        # You can add a placeholder label or image here
        placeholder_label = ttk.Label(album_art_frame, text="Album Art", style="TLabel")
        placeholder_label.pack(expand=True)


        # --- Song Info ---
        song_title_label = ttk.Label(main_container, text="Song Title", style="Header.TLabel")
        song_title_label.grid(row=2, column=0, columnspan=3, pady=(10, 0))

        artist_name_label = ttk.Label(main_container, text="Artist Name", style="TLabel")
        artist_name_label.grid(row=3, column=0, columnspan=3, pady=(0, 20))

        # --- Controls ---
        controls_frame = ttk.Frame(main_container)
        controls_frame.grid(row=4, column=0, columnspan=3)

        prev_button = ttk.Button(controls_frame, text="Previous Track", style="TButton")
        prev_button.grid(row=0, column=0, padx=5)

        play_pause_button = ttk.Button(controls_frame, text="Play/Pause", style="TButton")
        play_pause_button.grid(row=0, column=1, padx=5)

        next_button = ttk.Button(controls_frame, text="Next Track", style="TButton")
        next_button.grid(row=0, column=2, padx=5)

        # --- Back Button ---
        back_button = ttk.Button(
            main_container,
            text="Back to Main Menu",
            command=lambda: controller.show_frame("MainMenuFrame"),
            style="Back.TButton"
        )
        back_button.grid(row=5, column=0, columnspan=3, pady=(20, 0))
