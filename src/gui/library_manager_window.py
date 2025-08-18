import tkinter as tk
from tkinter import ttk

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

    search_button = ttk.Button(button_frame, text="Search & Preview")
    search_button.pack(side=tk.LEFT, padx=5)

    add_button = ttk.Button(button_frame, text="Add to Library", state="disabled")
    add_button.pack(side=tk.LEFT)

    main_frame.columnconfigure(1, weight=1) # Makes the entry widgets expandable

    # --- Preview Area ---
    preview_label = ttk.Label(main_frame, text="Preview:")
    preview_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))

    preview_area = tk.Text(main_frame, height=10, state="disabled", bg="#f0f0f0")
    preview_area.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

    main_frame.rowconfigure(5, weight=1) # Makes the preview area expandable
