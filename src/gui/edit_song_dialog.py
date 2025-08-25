import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from src.services import spotify_service
from src.services.spotify_service import SpotifyAPIError


class EditSongDialog(tk.Toplevel):
    """
    A dialog window for editing the details of a song, with an option to
    fetch metadata from Spotify.
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
        self.new_album_art_blob = None # To store art fetched during this session

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
        title_entry.grid(row=0, column=1, columnspan=2, sticky="ew")

        ttk.Label(form_frame, text="Artist:").grid(row=1, column=0, sticky="w", pady=5)
        artist_entry = ttk.Entry(form_frame, textvariable=self.artist_var)
        artist_entry.grid(row=1, column=1, columnspan=2, sticky="ew")

        ttk.Label(form_frame, text="Release Year:").grid(row=2, column=0, sticky="w", pady=5)
        year_entry = ttk.Entry(form_frame, textvariable=self.year_var)
        year_entry.grid(row=2, column=1, columnspan=2, sticky="ew")

        # --- Spotify ID Row ---
        ttk.Label(form_frame, text="Spotify ID:").grid(row=3, column=0, sticky="w", pady=5)
        spotify_id_entry = ttk.Entry(form_frame, textvariable=self.spotify_id_var)
        spotify_id_entry.grid(row=3, column=1, sticky="ew", padx=(0, 5))

        spotify_search_button = ttk.Button(
            form_frame, text="Search", command=self._on_spotify_search
        )
        spotify_search_button.grid(row=3, column=2, sticky="w")


        # --- Status Label ---
        self.status_var = tk.StringVar()
        status_label = ttk.Label(form_frame, textvariable=self.status_var, foreground="grey")
        status_label.grid(row=4, column=0, columnspan=3, sticky="w", pady=(10, 0))


        # --- Main Buttons ---
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

    def _on_spotify_search(self):
        """
        Initiates a background search for song details on Spotify.
        """
        spotify_id = self.spotify_id_var.get().strip()
        if not spotify_id:
            messagebox.showwarning("Missing ID", "Please enter a Spotify ID to search.", parent=self)
            return

        self.status_var.set("Searching on Spotify...")
        self.new_album_art_blob = None  # Reset on new search

        thread = threading.Thread(
            target=self._spotify_search_worker,
            args=(spotify_id,),
            daemon=True
        )
        thread.start()

    def _spotify_search_worker(self, spotify_id):
        """
        Worker function to fetch data from Spotify in a background thread.
        """
        try:
            track_data = spotify_service.get_track_by_id(spotify_id)
            if not track_data:
                self.after(0, self.status_var.set, f"Spotify ID '{spotify_id}' not found.")
                return

            # Fetch album art if a URL is present
            if track_data.get('album_art_url'):
                try:
                    self.new_album_art_blob = spotify_service.fetch_album_art_data(spotify_id)
                except Exception as art_exc:
                    logging.error(f"Failed to download album art: {art_exc}")
                    self.new_album_art_blob = None # Ensure it's reset on failure

            # Schedule the UI update on the main thread
            self.after(0, self._populate_from_spotify, track_data)

        except SpotifyAPIError as e:
            self.after(0, self.status_var.set, f"Spotify Error: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred during Spotify search: {e}")
            self.after(0, self.status_var.set, "An unexpected error occurred.")

    def _populate_from_spotify(self, track_data):
        """
        Populates the dialog's fields with data fetched from Spotify.
        This method is called from the main thread.
        """
        self.title_var.set(track_data.get('title', ''))
        self.artist_var.set(track_data.get('artist', ''))
        self.year_var.set(track_data.get('release_year', ''))
        self.status_var.set("Spotify data populated. You can now edit and save.")

    def _on_save(self):
        """
        Handles the Save button click. Stores the new data and closes the dialog.
        """
        self.result = {
            'title': self.title_var.get(),
            'artist': self.artist_var.get(),
            'release_year': self.year_var.get(),
            'spotify_id': self.spotify_id_var.get(),
            'new_album_art_blob': self.new_album_art_blob
        }
        self.destroy()

    def _on_cancel(self):
        """
        Handles the Cancel button click or window close. Closes the dialog.
        """
        self.result = None
        self.destroy()
