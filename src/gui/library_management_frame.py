import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import unicodedata
from src.services import spotify_service
from src.services.file_discovery import find_new_songs
from src.services.spotify_service import SpotifyAPIError
from src.utils.config_manager import config
from src.data.song_library import (
    add_song,
    DuplicateSongError,
    get_all_songs_for_view,
    delete_songs_by_id,
    update_song_details,
)


class LibraryManagementFrame(ttk.Frame):
    """
    A frame for managing the song library, including adding, viewing,
    searching, editing, and deleting songs.
    """

    def __init__(self, parent, controller):
        """
        Initializes the LibraryManagementFrame.
        """
        super().__init__(parent, style="TFrame")
        self.controller = controller
        self.preview_data = {}
        self.import_session_files = []
        self.current_import_index = -1
        self.songs_added_in_session = 0

        # --- Style for preview text area ---
        self.controller.style.configure("Preview.TText",
                                        border=2,
                                        relief="solid",
                                        font=self.controller.small_font,
                                        padding=5)
        self.preview_area_feedback_id = None

        # --- Main Layout ---
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)

        # --- Top Bar ---
        top_bar = ttk.Frame(self, style="TFrame", padding="0 0 0 5")
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")

        back_button = ttk.Button(
            top_bar,
            text="< Back to Main Menu",
            command=lambda: controller.show_frame("MainMenuFrame"),
            style="Back.TButton",
        )
        back_button.pack(side="left", pady=(5, 0))

        # --- Library View (Left Side) ---
        self.library_frame = ttk.LabelFrame(self, text="My Library")
        self.library_frame.grid(
            row=1, column=0, sticky="nsew", padx=(10, 5), pady=10
        )
        self.library_frame.grid_rowconfigure(1, weight=1)
        self.library_frame.grid_columnconfigure(0, weight=1)

        # --- Import Mode Widgets (initially hidden) ---
        self.import_status_label = ttk.Label(
            self.library_frame, text="", style="Status.TLabel"
        )

        # Search bar for the library
        self.search_bar_frame = ttk.Frame(self.library_frame, style="TFrame")
        self.search_bar_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.search_bar_frame.grid_columnconfigure(0, weight=1)

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(self.search_bar_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=0, sticky="ew")
        search_button = ttk.Button(
            self.search_bar_frame, text="Search", command=self._search_library, style="TButton"
        )
        search_button.grid(row=0, column=1, padx=(5, 0))
        self.search_var.trace_add("write", lambda *args: self._search_library())


        # Treeview to display songs
        columns = ("title", "artist", "release_year", "next_review_date")
        self.tree = ttk.Treeview(
            self.library_frame, columns=columns, show="headings"
        )
        self.tree.grid(row=1, column=0, sticky="nsew")

        # Define headings and add sorting command
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title(),
                              command=lambda _col=col: self._sort_column(_col, False))

        # Add a scrollbar
        self.tree_scrollbar = ttk.Scrollbar(
            self.library_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscroll=self.tree_scrollbar.set)
        self.tree_scrollbar.grid(row=1, column=1, sticky="ns")

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # Action buttons for the library
        action_button_frame = ttk.Frame(self.library_frame, style="TFrame")
        action_button_frame.grid(row=2, column=0, columnspan=2, sticky="e", pady=(10, 0))

        add_from_folder_button = ttk.Button(
            action_button_frame, text="Add from Folder",
            command=self._start_import_session, style="TButton"
        )
        add_from_folder_button.pack(side="left", padx=(0, 10))

        self.edit_button = ttk.Button(
            action_button_frame, text="Edit Selected", state="disabled",
            command=self._edit_selected_song, style="TButton"
        )
        self.edit_button.pack(side="left", padx=5)

        self.delete_button = ttk.Button(
            action_button_frame, text="Delete Selected", state="disabled",
            command=self._delete_selected_songs, style="TButton"
        )
        self.delete_button.pack(side="left")

        # --- Add Song Form (Right Side) ---
        self.add_song_frame = ttk.LabelFrame(self, text="Add New Song")
        self.add_song_frame.grid(
            row=1, column=1, sticky="nsew", padx=(5, 10), pady=10
        )
        self.add_song_frame.grid_columnconfigure(1, weight=1)

        # Input fields
        ttk.Label(self.add_song_frame, text="Local Filename:").grid(
            row=0, column=0, sticky="w", pady=2
        )
        self.local_filename_entry = ttk.Entry(self.add_song_frame)
        self.local_filename_entry.grid(row=0, column=1, sticky="ew", pady=2)

        ttk.Label(self.add_song_frame, text="Song Title:").grid(
            row=1, column=0, sticky="w", pady=2
        )
        self.song_title_entry = ttk.Entry(self.add_song_frame)
        self.song_title_entry.grid(row=1, column=1, sticky="ew", pady=2)

        ttk.Label(self.add_song_frame, text="Artist:").grid(
            row=2, column=0, sticky="w", pady=2
        )
        self.artist_entry = ttk.Entry(self.add_song_frame)
        self.artist_entry.grid(row=2, column=1, sticky="ew", pady=2)

        # Search and Add buttons for the form
        self.add_form_button_frame = ttk.Frame(self.add_song_frame, style="TFrame")
        self.add_form_button_frame.grid(
            row=3, column=0, columnspan=2, sticky="e", pady=10
        )

        self.search_preview_button = ttk.Button(
            self.add_form_button_frame, text="Search & Preview",
            command=self._search_and_preview, style="TButton"
        )
        self.search_preview_button.pack(side="left", padx=5)

        self.add_to_library_button = ttk.Button(
            self.add_form_button_frame, text="Add to Library", state="disabled",
            command=self._add_to_library, style="TButton"
        )
        self.add_to_library_button.pack(side="left")

        # --- Import Mode Buttons (initially hidden) ---
        self.skip_button = ttk.Button(
            self.add_form_button_frame, text="Skip File",
            command=self._skip_file, style="TButton"
        )
        # self.skip_button is packed when import mode starts

        self.stop_button = ttk.Button(
            self.add_form_button_frame, text="Stop & Exit",
            command=self._stop_import, style="TButton"
        )
        # self.stop_button is packed when import mode starts

        # Preview Area
        preview_label = ttk.Label(self.add_song_frame, text="Preview:")
        preview_label.grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(10, 2)
        )

        preview_text_frame = ttk.Frame(
            self.add_song_frame, style="Preview.TFrame", height=120
        )
        preview_text_frame.grid(
            row=5, column=0, columnspan=2, sticky="nsew"
        )
        preview_text_frame.grid_rowconfigure(0, weight=1)
        preview_text_frame.grid_columnconfigure(0, weight=1)
        # Prevent the frame from shrinking to fit the label inside
        preview_text_frame.grid_propagate(False)


        self.preview_area = ttk.Label(
            preview_text_frame,
            text="",
            wraplength=220,
            anchor="nw",
            justify="left",
            style="TLabel"
        )
        self.preview_area.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.add_song_frame.grid_rowconfigure(5, weight=1)

        # Store all songs to filter locally
        self.all_songs = []

    def on_show(self):
        """
        Called when the frame is shown. Refreshes the library view.
        """
        # Ensure the UI is in the default state and not in an import session.
        # This prevents the frame from being "stuck" in import mode.
        self._stop_import()

        self._populate_treeview()
        # Reset selection and button states
        self.tree.selection_set()
        self._on_tree_select(None)


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
        Opens a dialog to edit the selected song by providing a new Spotify ID.
        Fetches new metadata from Spotify and updates the local database.
        """
        selected_items = self.tree.selection()
        if not selected_items:
            return

        song_id_str = selected_items[0]
        song_id = int(song_id_str)

        # Find the current Spotify ID to pre-fill the dialog
        selected_song = next((s for s in self.all_songs if s['song_id'] == song_id), None)
        current_spotify_id = selected_song.get('spotify_id', '') if selected_song else ''

        new_spotify_id = simpledialog.askstring(
            "Edit Song via Spotify ID",
            "Enter the correct Spotify Track ID:",
            initialvalue=current_spotify_id,
            parent=self
        )

        if not new_spotify_id or not new_spotify_id.strip():
            return

        try:
            # Fetch new track details from Spotify
            self._update_preview_area("Fetching new song data from Spotify...")
            self.update_idletasks()

            new_track_info = spotify_service.get_track_by_id(new_spotify_id.strip())

            if not new_track_info:
                messagebox.showerror("Not Found", f"Could not find a track with ID: {new_spotify_id}")
                self._update_preview_area("") # Clear preview area
                return

            # Update the database with the new details
            update_song_details(
                song_id=song_id,
                title=new_track_info['title'],
                artist=new_track_info['artist'],
                release_year=new_track_info['release_year'],
                spotify_id=new_track_info['spotify_id']
            )

            self._populate_treeview() # Refresh the view
            self._update_preview_area("") # Clear preview area
            messagebox.showinfo("Success", "Song details updated successfully.")

        except SpotifyAPIError as e:
            messagebox.showerror("API Error", f"Could not fetch data from Spotify: {e}")
            self._update_preview_area("")
        except Exception as e:
            messagebox.showerror("Update Error", f"An unexpected error occurred: {e}")
            self._update_preview_area("")

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
        Adds the previewed song to the library.
        If in an import session, it automatically loads the next song.
        Otherwise, it resets the UI for manual entry.
        """
        if not self.preview_data:
            messagebox.showerror("Error", "No song data to add. Please search first.")
            return

        is_import_mode = self.current_import_index != -1
        song_added_successfully = False

        try:
            add_song(
                title=self.preview_data['title'],
                artist=self.preview_data['artist'],
                release_year=self.preview_data['release_year'],
                spotify_id=self.preview_data['spotify_id'],
                local_filename=self.preview_data['local_filename']
            )
            # If the above line doesn't raise an exception, the song was added.
            song_added_successfully = True
            if is_import_mode:
                self.songs_added_in_session += 1

        except DuplicateSongError:
            messagebox.showerror("Duplicate Song", "This song already exists in the library.")
            # In import mode, we just show the error and proceed to the next song.
            # In manual mode, we do nothing further.
            pass
        except Exception as e:
            messagebox.showerror("Database Error", f"An unexpected error occurred: {e}")
            # For any other database error, we stop and don't proceed.
            return

        # --- Post-Add Logic ---
        if is_import_mode:
            # For both success and duplicate errors, we advance to the next file.
            self.current_import_index += 1
            self._load_song_for_import()
        elif song_added_successfully:
            # In manual mode, we only reset the form upon a successful add.
            self._populate_treeview()
            self._update_preview_area(
                f"Success! Added '{self.preview_data['title']}'.",
                is_error=False,
                is_temporary=True
            )
            self.add_to_library_button.config(state="disabled")
            self.local_filename_entry.delete(0, tk.END)
            self.song_title_entry.delete(0, tk.END)
            self.artist_entry.delete(0, tk.END)
            self.preview_data = {}

    def _start_import_session(self):
        """
        Initiates the process of importing songs from a folder.
        Finds new songs and transitions the UI to import mode.
        """
        music_folder = config.get('Paths', 'music_folder', fallback=None)
        if not music_folder or not os.path.isdir(music_folder):
            messagebox.showerror("Configuration Error",
                                 "Music folder not set or not found. "
                                 "Please configure it in 'config.ini'.")
            return

        # Ensure self.all_songs is up-to-date to get all existing filenames
        self._populate_treeview()
        # Normalize and lowercase for a case-insensitive, robust comparison
        existing_filenames = {
            unicodedata.normalize('NFC', song['local_filename'].lower())
            for song in self.all_songs if 'local_filename' in song and song['local_filename']
        }

        # Find new songs by comparing against the library
        new_files = find_new_songs(music_folder, existing_filenames)

        if not new_files:
            messagebox.showinfo("No New Songs", "No new songs found in your music folder.")
            return

        # --- Enter Import Mode ---
        self.import_session_files = new_files
        self.current_import_index = 0
        self.songs_added_in_session = 0

        # --- Update UI for Import Mode ---
        # Hide normal view widgets
        self.search_bar_frame.grid_remove()
        self.tree.grid_remove()
        self.tree_scrollbar.grid_remove()
        self.edit_button.pack_forget()
        self.delete_button.pack_forget()

        # Re-configure the 'Add Song' form buttons for import
        self.search_preview_button.pack_forget()
        self.add_to_library_button.pack_forget()

        # Show import-specific widgets
        self.import_status_label.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Add buttons in the new order for import mode
        self.search_preview_button.pack(side="left", padx=5)
        self.add_to_library_button.pack(side="left")
        self.skip_button.pack(side="left", padx=5)
        self.stop_button.pack(side="left")

        # Load the first song to be imported
        self._load_song_for_import()

    def _load_song_for_import(self):
        """
        Loads the current song from the import session into the 'Add New Song' form.
        It updates the status label and pre-fills the entry fields.
        """
        if self.current_import_index >= len(self.import_session_files):
            self._stop_import()
            messagebox.showinfo(
                "Import Complete",
                f"Import complete! Added {self.songs_added_in_session} new songs."
            )
            return

        # Update status label
        total_files = len(self.import_session_files)
        current_num = self.current_import_index + 1
        self.import_status_label.config(
            text=f"Importing file {current_num} of {total_files}."
        )

        # Get file path and pre-fill form
        full_path = self.import_session_files[self.current_import_index]
        filename = os.path.basename(full_path)

        # Reset fields and preview area for the new song
        self.local_filename_entry.delete(0, tk.END)
        self.local_filename_entry.insert(0, filename)

        self.song_title_entry.delete(0, tk.END)
        self.artist_entry.delete(0, tk.END)
        self._update_preview_area("")
        self.add_to_library_button.config(state="disabled")

    def _skip_file(self):
        """
        Skips the current file and loads the next one in the import session.
        """
        self.current_import_index += 1
        self._load_song_for_import()

    def _stop_import(self):
        """
        Stops the import session and restores the normal library view.
        """
        # --- Exit Import Mode ---
        self.import_session_files = []
        self.current_import_index = -1

        # --- Restore UI to Normal View ---
        # Hide import-specific widgets
        self.import_status_label.grid_remove()
        self.skip_button.pack_forget()
        self.stop_button.pack_forget()
        self.add_to_library_button.pack_forget() # Temporarily remove to re-order

        # Restore normal view widgets
        self.search_bar_frame.grid()
        self.tree.grid()
        self.tree_scrollbar.grid()

        # Restore buttons to their original positions and order
        self.edit_button.pack(side="left", padx=5)
        self.delete_button.pack(side="left")

        self.search_preview_button.pack(side="left", padx=5)
        self.add_to_library_button.pack(side="left")

        # Refresh the library view to show any newly added songs
        self._populate_treeview()

        # Reset form fields
        self.local_filename_entry.delete(0, tk.END)
        self.song_title_entry.delete(0, tk.END)
        self.artist_entry.delete(0, tk.END)
        self._update_preview_area("")
        self.add_to_library_button.config(state="disabled")

    def _update_preview_area(self, text, is_error=False, is_temporary=False):
        """
        Helper function to update the text in the preview area.
        - `is_error`: Displays the text in red.
        - `is_temporary`: The message disappears after a few seconds.
        """
        # Cancel any pending feedback message reset
        if self.preview_area_feedback_id:
            self.after_cancel(self.preview_area_feedback_id)
            self.preview_area_feedback_id = None

        self.preview_area.config(
            text=text,
            foreground="red" if is_error else "green" if is_temporary else "black"
        )

        # If the message is temporary, schedule it to be cleared
        if is_temporary:
            self.preview_area_feedback_id = self.after(
                4000, lambda: self._update_preview_area("")
            )
