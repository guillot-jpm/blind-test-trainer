# src/services/file_discovery.py

"""
This module provides functions for discovering new audio files in the user's music library.
"""

import os
import unicodedata

def find_new_songs(music_folder_path, existing_filenames):
    """
    Recursively scans a folder for new audio files not present in the database.

    Args:
        music_folder_path (str): The absolute path to the user's music folder.
        existing_filenames (set): A set of basenames (e.g., 'song.mp3') of songs
                                  already in the database.

    Returns:
        list: A list of full, absolute file paths for new songs found.
    """
    new_song_paths = []
    audio_extensions = {".mp3", ".wav", ".flac", ".m4a", ".ogg"}

    if not os.path.isdir(music_folder_path):
        # Or raise an error, depending on desired behavior for invalid paths
        return []

    print(f"\n[DEBUG] Starting file discovery in: {music_folder_path}")
    print(f"[DEBUG] Number of existing filenames in database: {len(existing_filenames)}")

    for root, _, files in os.walk(music_folder_path):
        for filename in files:
            print(f"\n[DEBUG] Checking file: {filename}")

            # Check if the file has a recognized audio extension
            is_audio = any(filename.lower().endswith(ext) for ext in audio_extensions)
            if not is_audio:
                print(f"[DEBUG] -> Skipped: Not a recognized audio file extension.")
                continue

            # Normalize and lowercase the filename for comparison
            normalized_filename = unicodedata.normalize('NFC', filename.lower())
            print(f"[DEBUG] -> Is audio file. Normalized name: '{normalized_filename}'")

            # Compare the basename against the existing filenames
            if normalized_filename not in existing_filenames:
                print(f"[DEBUG] -> Added for import: Normalized name not found in existing files.")
                full_path = os.path.join(root, filename)
                new_song_paths.append(os.path.abspath(full_path))
            else:
                print(f"[DEBUG] -> Skipped: Normalized name found in existing files.")

    print(f"\n[DEBUG] File discovery complete. Found {len(new_song_paths)} new songs.")
    return new_song_paths
