import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
from src.services import spotify_service
from src.services.spotify_service import SpotifyAPIError
from src.utils.config_manager import config
from src.data.song_library import (
    add_song,
    DuplicateSongError,
    get_all_songs_for_view,
    delete_songs_by_id,
    update_song_spotify_id,
)


class LibraryManagementFrame(tk.Frame):
    """
    A frame for managing the song library, including adding, viewing,
    searching, editing, and deleting songs.
    """

    def __init__(self, parent, controller):
        """
        Initializes the LibraryManagementFrame.
        """
        super().__init__(parent)
        self.controller = controller
        self.preview_data = {}

        # --- Main Layout ---
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)

        # --- Top Bar ---
        top_bar = ttk.Frame(self, padding="10 0 10 10")
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")

        back_button = ttk.Button(
            top_bar,
            text="< Back to Main Menu",
            command=lambda: controller.show_frame("MainMenuFrame"),
        )
        back_button.pack(side="left")

        # --- Library View (Left Side) ---
        library_frame = ttk.LabelFrame(
            self, text="My Library", padding="10"
        )
        library_frame.grid(
            row=1, column=0, sticky="nsew", padx=(10, 5), pady=10
        )
        library_frame.grid_rowconfigure(1, weight=1)
        library_frame.grid_columnconfigure(0, weight=1)

        # Search bar for the library
        search_bar_frame = ttk.Frame(library_frame)
        search_bar_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        search_bar_frame.grid_columnconfigure(0, weight=1)

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_bar_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=0, sticky="ew")
        search_button = ttk.Button(search_bar_frame, text="Search", command=self._search_library)
        search_button.grid(row=0, column=1, padx=(5, 0))
        self.search_var.trace_add("write", lambda *args: self._search_library())


        # Treeview to display songs
        columns = ("title", "artist", "release_year", "next_review_date")
        self.tree = ttk.Treeview(
            library_frame, columns=columns, show="headings"
        )
        self.tree.grid(row=1, column=0, sticky="nsew")

        # Define headings and add sorting command
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title(),
                              command=lambda _col=col: self._sort_column(_col, False))

        # Add a scrollbar
        scrollbar = ttk.Scrollbar(
            library_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky="ns")

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # Action buttons for the library
        action_button_frame = ttk.Frame(library_frame)
        action_button_frame.grid(row=2, column=0, columnspan=2, sticky="e", pady=(10, 0))

        self.edit_button = ttk.Button(
            action_button_frame, text="Edit Selected", state="disabled", command=self._edit_selected_song
        )
        self.edit_button.pack(side="left", padx=5)

        self.delete_button = ttk.Button(
            action_button_frame, text="Delete Selected", state="disabled", command=self._delete_selected_songs
        )
        self.delete_button.pack(side="left")

        # --- Add Song Form (Right Side) ---
        add_song_frame = ttk.LabelFrame(
            self, text="Add New Song", padding="10"
        )
        add_song_frame.grid(
            row=1, column=1, sticky="nsew", padx=(5, 10), pady=10
        )
        add_song_frame.grid_columnconfigure(1, weight=1)

        # Input fields
        ttk.Label(add_song_frame, text="Local Filename:").grid(row=0, column=0, sticky="w", pady=2)
        self.local_filename_entry = ttk.Entry(add_song_frame)
        self.local_filename_entry.grid(row=0, column=1, sticky="ew", pady=2)

        ttk.Label(add_song_frame, text="Song Title:").grid(row=1, column=0, sticky="w", pady=2)
        self.song_title_entry = ttk.Entry(add_song_frame)
        self.song_title_entry.grid(row=1, column=1, sticky="ew", pady=2)

        ttk.Label(add_song_frame, text="Artist:").grid(row=2, column=0, sticky="w", pady=2)
        self.artist_entry = ttk.Entry(add_song_frame)
        self.artist_entry.grid(row=2, column=1, sticky="ew", pady=2)

        # Search and Add buttons for the form
        add_form_button_frame = ttk.Frame(add_song_frame)
        add_form_button_frame.grid(row=3, column=0, columnspan=2, sticky="e", pady=10)

        search_preview_button = ttk.Button(add_form_button_frame, text="Search & Preview", command=self._search_and_preview)
        search_preview_button.pack(side="left", padx=5)

        self.add_to_library_button = ttk.Button(add_form_button_frame, text="Add to Library", state="disabled", command=self._add_to_library)
        self.add_to_library_button.pack(side="left")

        # Preview Area
        preview_label = ttk.Label(add_song_frame, text="Preview:")
        preview_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 0))

        self.preview_area = tk.Text(add_song_frame, height=8, state="disabled", bg="#f0f0f0")
        self.preview_area.grid(row=5, column=0, columnspan=2, sticky="nsew")
        add_song_frame.grid_rowconfigure(5, weight=1)

        # Store all songs to filter locally
        self.all_songs = []

        # Populate the treeview on initialization
        self._populate_treeview()

    def _populate_treeview(self, songs_to_display=None):
        """
        Populates the treeview with song data.
        If songs_to_display is None, it fetches all songs from the database.
        Otherwise, it displays the provided list of songs.
        """
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # If no specific list is provided, fetch all songs
        if songs_to_display is None:
            self.all_songs = get_all_songs_for_view()
            songs_to_display = self.all_songs

        # Insert new items
        for song in songs_to_display:
            values = (
                song["title"],
                song["artist"],
                song["release_year"],
                song["next_review_date"],
            )
            # Store the song_id in the item's id
            self.tree.insert("", tk.END, iid=song["song_id"], values=values)

    def _search_library(self, *args):
        """
        Filters the treeview based on the search query.
        The search is case-insensitive and checks both title and artist.
        """
        query = self.search_var.get().lower()
        if not query:
            self._populate_treeview(self.all_songs)
            return

        filtered_songs = [
            song for song in self.all_songs
            if query in song["title"].lower() or query in song["artist"].lower()
        ]
        self._populate_treeview(filtered_songs)

    def _on_tree_select(self, event):
        """
        Enables or disables the edit/delete buttons based on the number of
        selected items in the treeview.
        """
        selected_items = self.tree.selection()
        num_selected = len(selected_items)

        if num_selected == 0:
            self.edit_button.config(state="disabled")
            self.delete_button.config(state="disabled")
        elif num_selected == 1:
            self.edit_button.config(state="normal")
            self.delete_button.config(state="normal")
        else: # More than 1 selected
            self.edit_button.config(state="disabled")
            self.delete_button.config(state="normal")

    def _sort_column(self, col, reverse):
        """Sorts the treeview column when a heading is clicked."""
        # Get data from the treeview
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]

        # Sort the data
        # The data is sorted case-insensitively if it's a string
        data.sort(key=lambda t: (t[0].lower() if isinstance(t[0], str) else t[0]), reverse=reverse)

        for index, (val, child) in enumerate(data):
            self.tree.move(child, '', index)

        # Toggle the sort direction for the next click
        self.tree.heading(col, command=lambda: self._sort_column(col, not reverse))

    def _edit_selected_song(self):
        """
        Opens a dialog to edit the Spotify ID of the selected song.
        """
        selected_items = self.tree.selection()
        if not selected_items:
            return

        song_id = selected_items[0]

        # Get current spotify ID to show in prompt
        selected_song_data = next((song for song in self.all_songs if str(song['song_id']) == song_id), None)
        current_spotify_id = selected_song_data.get('spotify_id', '') if selected_song_data else ''

        new_spotify_id = simpledialog.askstring(
            "Edit Spotify ID",
            "Enter the correct Spotify Track ID:",
            initialvalue=current_spotify_id,
            parent=self
        )

        if new_spotify_id and new_spotify_id.strip():
            try:
                update_song_spotify_id(int(song_id), new_spotify_id.strip())
                self._populate_treeview() # Refresh the view
                messagebox.showinfo("Success", "Spotify ID updated successfully.")
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to update Spotify ID: {e}")

    def _delete_selected_songs(self):
        """
        Deletes the selected song(s) from the library after confirmation.
        """
        selected_items = self.tree.selection()
        if not selected_items:
            return

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete {len(selected_items)} song(s)?\n"
            "This action cannot be undone."
        )

        if confirm:
            try:
                song_ids_to_delete = [int(item_id) for item_id in selected_items]
                delete_songs_by_id(song_ids_to_delete)
                self._populate_treeview() # Refresh the view
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to delete songs: {e}")

    def _search_and_preview(self):
        """
        Searches for a track on Spotify based on user input and displays a preview.
        """
        title = self.song_title_entry.get().strip()
        artist = self.artist_entry.get().strip()
        filename = self.local_filename_entry.get().strip()

        if not filename:
            messagebox.showwarning("Missing Information", "Local Filename is required.")
            return
        if not title:
            messagebox.showwarning("Missing Information", "Song Title is required for searching.")
            return

        music_folder = config.get('Paths', 'music_folder', fallback='.')
        file_path = os.path.join(music_folder, filename)
        if not os.path.exists(file_path):
            self._update_preview_area(f"Error: File '{filename}' not found in music folder.", is_error=True)
            self.add_to_library_button.config(state="disabled")
            return

        self._update_preview_area("Searching...")
        self.update_idletasks()

        try:
            match = spotify_service.search_by_title_and_artist(title, artist) if artist else spotify_service.search_by_title(title)

            if match:
                self.preview_data = match
                self.preview_data['local_filename'] = filename

                display_text = (
                    f"Title: {match['title']}\n"
                    f"Artist: {match['artist']}\n"
                    f"Release Year: {match['release_year']}\n"
                    f"Spotify ID: {match['spotify_id']}"
                )
                self._update_preview_area(display_text)
                self.add_to_library_button.config(state="normal")
            else:
                self._update_preview_area("No match found on Spotify.", is_error=True)
                self.add_to_library_button.config(state="disabled")

        except SpotifyAPIError as e:
            self._update_preview_area(f"API Error: {e}", is_error=True)
            self.add_to_library_button.config(state="disabled")


    def _add_to_library(self):
        """
        Adds the previewed song to the library and resets the UI.
        """
        if not self.preview_data:
            messagebox.showerror("Error", "No song data to add. Please search first.")
            return

        try:
            add_song(
                title=self.preview_data['title'],
                artist=self.preview_data['artist'],
                release_year=self.preview_data['release_year'],
                spotify_id=self.preview_data['spotify_id'],
                local_filename=self.preview_data['local_filename']
            )

            # Refresh treeview to show the new song
            self._populate_treeview()

            # Provide feedback and reset the form
            self._update_preview_area(f"Successfully added '{self.preview_data['title']}'.")
            self.add_to_library_button.config(state="disabled")
            self.local_filename_entry.delete(0, tk.END)
            self.song_title_entry.delete(0, tk.END)
            self.artist_entry.delete(0, tk.END)
            self.preview_data = {}

        except DuplicateSongError:
            messagebox.showerror("Duplicate Song", "This song already exists in the library.")
        except Exception as e:
            messagebox.showerror("Database Error", f"An unexpected error occurred: {e}")

    def _update_preview_area(self, text, is_error=False):
        """Helper function to update the text in the preview area."""
        self.preview_area.config(state="normal")
        self.preview_area.delete("1.0", tk.END)
        self.preview_area.insert("1.0", text)
        self.preview_area.config(
            state="disabled",
            foreground="red" if is_error else "black"
        )
