import tkinter as tk
from tkinter import ttk, messagebox
import os
from src.services import musicbrainz_service
from src.services.musicbrainz_service import MusicBrainzAPIError
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
    # Song Title
    ttk.Label(main_frame, text="Song Title:").grid(row=0, column=0, sticky=tk.W, pady=2)
    song_title_entry = ttk.Entry(main_frame, width=40)
    song_title_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)

    # Artist
    ttk.Label(main_frame, text="Artist:").grid(row=1, column=0, sticky=tk.W, pady=2)
    artist_entry = ttk.Entry(main_frame, width=40)
    artist_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)

    # Local Filename
    ttk.Label(main_frame, text="Local Filename:").grid(row=2, column=0, sticky=tk.W, pady=2)
    local_filename_entry = ttk.Entry(main_frame, width=40)
    local_filename_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)

    # --- Buttons ---
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky=tk.E)

    search_button = ttk.Button(
        button_frame,
        text="Search & Preview",
        command=lambda: search_and_preview(
            song_title_entry.get(),
            artist_entry.get(),
            local_filename_entry.get(),
            preview_area,
            add_button,
            window
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
            local_filename_entry
        )
    )
    add_button.pack(side=tk.LEFT)

    main_frame.columnconfigure(1, weight=1) # Makes the entry widgets expandable

    # --- Preview Area ---
    preview_label = ttk.Label(main_frame, text="Preview:")
    preview_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))

    preview_area = tk.Text(main_frame, height=10, state="disabled", bg="#f0f0f0")
    preview_area.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

    main_frame.rowconfigure(5, weight=1) # Makes the preview area expandable

def search_and_preview(title, artist, filename, preview_area, add_button, window):
    """
    Handles the "Search & Preview" button click event.
    """
    # --- 1. Input Validation ---
    if not all([title, artist, filename]):
        messagebox.showwarning("Missing Information", "Please fill in all title, artist, and filename fields.")
        return

    # --- 2. File Existence Check ---
    music_folder = config.get('Paths', 'music_folder')
    file_path = os.path.join(music_folder, filename)

    if not os.path.exists(file_path):
        # If the file doesn't exist, display an error in the preview area.
        error_message = f"Error: File '{filename}' not found in your music folder."
        preview_area.config(state="normal")
        preview_area.delete("1.0", tk.END)
        preview_area.insert("1.0", error_message)
        preview_area.config(state="disabled")
        add_button.config(state="disabled")
        return

    # --- 3. API Search ---
    # Show a temporary message while searching; this will be replaced by results or an error.
    preview_area.config(state="normal")
    preview_area.delete("1.0", tk.END)
    preview_area.insert("1.0", "Searching for song metadata on MusicBrainz...")
    preview_area.config(state="disabled")
    window.update_idletasks()  # Force the UI to update

    try:
        match = musicbrainz_service.find_best_match(title, artist)

        # --- 4. Update Preview Area ---
        if match:
            # Store the full metadata in a hidden attribute for later use
            window.preview_data = match
            window.preview_data['local_filename'] = filename # Add filename for convenience

            # Format for display
            display_text = (
                f"Title: {match['title']}\n"
                f"Artist: {match['artist']}\n"
                f"Primary Artist: {match['primary_artist']}\n"
                f"Release Year: {match['release_year']}\n\n"
                f"--- MusicBrainz ID ---\n"
                f"Release Group ID: {match['release_group_id']}"
            )

            preview_area.config(state="normal")
            preview_area.delete("1.0", tk.END)
            preview_area.insert("1.0", display_text)
            preview_area.config(state="disabled")

            add_button.config(state="normal") # Enable the "Add" button
        else:
            # If no match is found, display a message in the preview area.
            error_message = "No match found. Please check the title and artist."
            preview_area.config(state="normal")
            preview_area.delete("1.0", tk.END)
            preview_area.insert("1.0", error_message)
            preview_area.config(state="disabled")
            add_button.config(state="disabled")

    except MusicBrainzAPIError as e:
        messagebox.showerror("API Connection Error", str(e))
        # Also clear the preview area and disable the add button
        preview_area.config(state="normal")
        preview_area.delete("1.0", tk.END)
        preview_area.insert("1.0", "API request failed.")
        preview_area.config(state="disabled")
        add_button.config(state="disabled")


def add_to_library(window, add_button, preview_area, title_entry, artist_entry, filename_entry):
    """
    Handles the "Add to Library" button click event.
    """
    if not hasattr(window, 'preview_data') or not window.preview_data:
        messagebox.showerror("Error", "No song data to add. Please search for a song first.")
        return

    data = window.preview_data
    try:
        add_song(
            title=data['title'],
            artist=data['artist'],
            release_year=data['release_year'],
            local_filename=data['local_filename'],
            musicbrainz_release_group_id=data['release_group_id']
        )
        messagebox.showinfo(
            "Success",
            f"'{data['title']}' by {data['artist']} has been added successfully!"
        )

        # --- Reset UI ---
        # Clear entry fields
        title_entry.delete(0, tk.END)
        artist_entry.delete(0, tk.END)
        filename_entry.delete(0, tk.END)

        # Clear preview area
        preview_area.config(state="normal")
        preview_area.delete("1.0", tk.END)
        preview_area.config(state="disabled")

        # Disable "Add" button
        add_button.config(state="disabled")

        # Clear the stored data
        del window.preview_data

    except DuplicateSongError:
        messagebox.showerror("Duplicate Song", "This song already exists in the library.")
    except Exception as e:
        messagebox.showerror("Database Error", f"An unexpected error occurred: {e}")
