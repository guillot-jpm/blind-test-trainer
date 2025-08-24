import tkinter as tk
from tkinter import ttk

class EditSongDialog(tk.Toplevel):
    """
    A dialog window for editing the details of a song.
    """
    def __init__(self, parent, song_data):
        """
        Initializes the EditSongDialog.

        Args:
            parent: The parent window.
            song_data (dict): A dictionary containing the current details of the song.
        """
        super().__init__(parent)
        self.transient(parent)
        self.title("Edit Song Details")
        self.parent = parent
        self.result = None

        # --- Data ---
        self.song_data = song_data
        self.title_var = tk.StringVar(value=song_data.get('title', ''))
        self.artist_var = tk.StringVar(value=song_data.get('artist', ''))
        self.year_var = tk.StringVar(value=song_data.get('release_year', ''))
        self.spotify_id_var = tk.StringVar(value=song_data.get('spotify_id', ''))

        # --- Widgets ---
        form_frame = ttk.Frame(self, padding="10")
        form_frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(form_frame, text="Title:").grid(row=0, column=0, sticky="w", pady=5)
        title_entry = ttk.Entry(form_frame, textvariable=self.title_var, width=40)
        title_entry.grid(row=0, column=1, sticky="ew")

        ttk.Label(form_frame, text="Artist:").grid(row=1, column=0, sticky="w", pady=5)
        artist_entry = ttk.Entry(form_frame, textvariable=self.artist_var)
        artist_entry.grid(row=1, column=1, sticky="ew")

        ttk.Label(form_frame, text="Release Year:").grid(row=2, column=0, sticky="w", pady=5)
        year_entry = ttk.Entry(form_frame, textvariable=self.year_var)
        year_entry.grid(row=2, column=1, sticky="ew")

        ttk.Label(form_frame, text="Spotify ID:").grid(row=3, column=0, sticky="w", pady=5)
        spotify_id_entry = ttk.Entry(form_frame, textvariable=self.spotify_id_var)
        spotify_id_entry.grid(row=3, column=1, sticky="ew")

        button_frame = ttk.Frame(self, padding="10")
        button_frame.grid(row=1, column=0, sticky="e")

        save_button = ttk.Button(button_frame, text="Save", command=self._on_save)
        save_button.pack(side="left", padx=(0, 5))

        cancel_button = ttk.Button(button_frame, text="Cancel", command=self._on_cancel)
        cancel_button.pack(side="left")

        # --- Configuration ---
        self.grid_columnconfigure(0, weight=1)
        form_frame.grid_columnconfigure(1, weight=1)

        # Center the dialog on the parent window
        self.geometry(f"+{parent.winfo_rootx()+50}+{parent.winfo_rooty()+50}")

        # Make the dialog modal
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.grab_set()
        self.wait_window(self)

    def _on_save(self):
        """
        Handles the Save button click. Stores the new data and closes the dialog.
        """
        self.result = {
            'title': self.title_var.get(),
            'artist': self.artist_var.get(),
            'release_year': self.year_var.get(),
            'spotify_id': self.spotify_id_var.get()
        }
        self.destroy()

    def _on_cancel(self):
        """
        Handles the Cancel button click or window close. Closes the dialog.
        """
        self.result = None
        self.destroy()
