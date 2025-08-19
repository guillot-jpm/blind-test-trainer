import tkinter as tk
from tkinter import ttk, messagebox
import os
from src.services import spotify_service
from src.services.spotify_service import SpotifyAPIError
from src.utils.config_manager import config
from src.data.song_library import add_song, DuplicateSongError


def create_library_manager_window(parent):
    """
    Creates the Library Manager window, which allows users to add new songs
    to their library by providing song details and searching for a local file.
    """
    window = tk.Toplevel(parent)
    window.title("Library Manager")
    window.geometry("600x400")  # Adjusted size for better layout

    # Create a main frame to hold all widgets
    main_frame = ttk.Frame(window, padding="10")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=1)

    # --- Input Fields ---
    # Row 0: Local Filename (Required)
    ttk.Label(main_frame, text="Local Filename:").grid(row=0, column=0, sticky=tk.W, pady=2)
    local_filename_entry = ttk.Entry(main_frame, width=40)
    local_filename_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)

    # Row 1: Song Title
    ttk.Label(main_frame, text="Song Title:").grid(row=1, column=0, sticky=tk.W, pady=2)
    song_title_entry = ttk.Entry(main_frame, width=40)
    song_title_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)

    # Row 2: Artist (Initially Hidden)
    artist_label = ttk.Label(main_frame, text="Artist:")
    artist_entry = ttk.Entry(main_frame, width=40)

    # Row 3: Spotify Track ID (Initially Hidden)
    spotify_id_label = ttk.Label(main_frame, text="Spotify Track ID:")
    spotify_id_entry = ttk.Entry(main_frame, width=40)

    # --- UI Management for Progressive Disclosure ---
    # Store widgets that can be hidden/shown
    window.progressive_widgets = {
        'artist': (artist_label, artist_entry),
        'spotify_id': (spotify_id_label, spotify_id_entry)
    }

    # Hide them initially
    artist_label.grid_remove()
    artist_entry.grid_remove()
    spotify_id_label.grid_remove()
    spotify_id_entry.grid_remove()

    # Place them in the grid layout for later
    artist_label.grid(row=2, column=0, sticky=tk.W, pady=2)
    artist_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)
    spotify_id_label.grid(row=3, column=0, sticky=tk.W, pady=2)
    spotify_id_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2)


    # --- Buttons ---
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky=tk.E)

    search_button = ttk.Button(
        button_frame,
        text="Search",
        command=lambda: search_and_preview(
            window,
            song_title_entry,
            artist_entry,
            spotify_id_entry,
            local_filename_entry,
            preview_area,
            add_button
        )
    )
    search_button.pack(side=tk.LEFT, padx=5)

    add_button = ttk.Button(
        button_frame,
        text="Add to Library",
        state="disabled",
        command=lambda: add_to_library(
            window,
            add_button,
            preview_area,
            song_title_entry,
            artist_entry,
            local_filename_entry,
            spotify_id_entry
        )
    )
    add_button.pack(side=tk.LEFT)

    main_frame.columnconfigure(1, weight=1) # Makes the entry widgets expandable

    # --- Preview Area ---
    preview_label = ttk.Label(main_frame, text="Preview:")
    preview_label.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))

    preview_area = tk.Text(main_frame, height=10, state="disabled", bg="#f0f0f0")
    preview_area.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

    main_frame.rowconfigure(6, weight=1) # Makes the preview area expandable

def search_and_preview(window, song_title_entry, artist_entry, spotify_id_entry, local_filename_entry, preview_area, add_button):
    """
    Handles the multi-level search process.
    """
    # --- 1. Get current input values ---
    filename = local_filename_entry.get().strip()
    title = song_title_entry.get().strip()
    artist = artist_entry.get().strip()
    spotify_id = spotify_id_entry.get().strip()

    # --- 2. Input Validation ---
    if not filename:
        messagebox.showwarning("Missing Information", "Local Filename is required.")
        return
    if not title and not spotify_id:
        messagebox.showwarning("Missing Information", "Please provide a Song Title or a Spotify Track ID.")
        return

    # --- 3. File Existence Check ---
    music_folder = config.get('Paths', 'music_folder')
    file_path = os.path.join(music_folder, filename)
    if not os.path.exists(file_path):
        _update_preview_area(preview_area, f"Error: File '{filename}' not found.", is_error=True)
        add_button.config(state="disabled")
        return

    # --- 4. Determine Search Level and Execute ---
    _update_preview_area(preview_area, "Searching...")
    window.update_idletasks()

    try:
        match = None
        # Level 3: Spotify ID search (highest priority)
        if spotify_id:
            match = spotify_service.get_track_by_id(spotify_id)
        # Level 2: Title and Artist search
        elif artist_entry.winfo_viewable():
            match = spotify_service.search_by_title_and_artist(title, artist)
        # Level 1: Title-only search
        else:
            match = spotify_service.search_by_title(title)

        # --- 5. Process Results ---
        if match:
            _handle_successful_search(
                window, match, filename, preview_area, add_button,
                song_title_entry, artist_entry, spotify_id_entry
            )
        else:
            _update_preview_area(preview_area, "No match found.", is_error=True)
            add_button.config(state="disabled")

    except SpotifyAPIError as e:
        _update_preview_area(preview_area, f"API Error: {e}", is_error=True)
        add_button.config(state="disabled")


def _handle_successful_search(window, match, filename, preview_area, add_button,
                              song_title_entry, artist_entry, spotify_id_entry):
    """Helper to handle the UI updates after a successful search."""
    # Store data for the 'Add to Library' action
    window.preview_data = match
    window.preview_data['local_filename'] = filename

    # Update the preview text
    display_text = (
        f"Title: {match['title']}\n"
        f"Artist: {match['artist']}\n"
        f"Release Year: {match['release_year']}\n"
        f"Spotify ID: {match['spotify_id']}"
    )
    _update_preview_area(preview_area, display_text)

    # --- Progressive UI Updates ---
    # Update title and artist fields to reflect the match
    song_title_entry.delete(0, tk.END)
    song_title_entry.insert(0, match['title'])
    artist_entry.delete(0, tk.END)
    artist_entry.insert(0, match['artist'])

    # Show artist field if it was hidden
    if not window.progressive_widgets['artist'][0].winfo_viewable():
        window.progressive_widgets['artist'][0].grid()
        window.progressive_widgets['artist'][1].grid()

    # Show Spotify ID field if it was hidden
    if not window.progressive_widgets['spotify_id'][0].winfo_viewable():
        window.progressive_widgets['spotify_id'][0].grid()
        window.progressive_widgets['spotify_id'][1].grid()

    # Update the spotify id field as well
    spotify_id_entry.delete(0, tk.END)
    spotify_id_entry.insert(0, match['spotify_id'])

    add_button.config(state="normal")


def _update_preview_area(preview_area, text, is_error=False):
    """Helper function to update the text in the preview area."""
    preview_area.config(state="normal")
    preview_area.delete("1.0", tk.END)
    preview_area.insert("1.0", text)
    preview_area.config(
        state="disabled",
        foreground="red" if is_error else "black"
    )

def add_to_library(window, add_button, preview_area, title_entry, artist_entry, filename_entry, spotify_id_entry):
    """
    Handles adding the previewed song to the library and resetting the UI.
    """
    if not hasattr(window, 'preview_data') or not window.preview_data:
        messagebox.showerror("Error", "No song data available. Please search for a song first.")
        return

    data = window.preview_data
    try:
        add_song(
            title=data['title'],
            artist=data['artist'],
            release_year=data['release_year'],
            spotify_id=data['spotify_id'],
            local_filename=data['local_filename']
        )
        messagebox.showinfo("Success", f"Added '{data['title']}' to the library.")

        # --- Reset UI to initial state ---
        reset_library_manager_ui(window, add_button, preview_area, title_entry, artist_entry, filename_entry, spotify_id_entry)

    except DuplicateSongError:
        messagebox.showerror("Duplicate Song", "This song already exists in the library.")
    except Exception as e:
        messagebox.showerror("Database Error", f"An unexpected error occurred: {e}")


def reset_library_manager_ui(window, add_button, preview_area, title_entry, artist_entry, filename_entry, spotify_id_entry):
    """Resets the Library Manager window to its initial state."""
    # Clear all text entries
    title_entry.delete(0, tk.END)
    artist_entry.delete(0, tk.END)
    filename_entry.delete(0, tk.END)
    spotify_id_entry.delete(0, tk.END)

    # Hide progressive widgets
    window.progressive_widgets['artist'][0].grid_remove()
    window.progressive_widgets['artist'][1].grid_remove()
    window.progressive_widgets['spotify_id'][0].grid_remove()
    window.progressive_widgets['spotify_id'][1].grid_remove()

    # Clear the preview area
    _update_preview_area(preview_area, "")

    # Disable the add button
    add_button.config(state="disabled")

    # Delete the temporary preview data
    if hasattr(window, 'preview_data'):
        del window.preview_data
