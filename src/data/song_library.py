# src/data/song_library.py

"""
This module provides functions for managing the song library in the database.
It includes functions for adding, retrieving, and listing songs.
"""

import sqlite3
from datetime import date
from src.data.database_manager import get_cursor

class DuplicateSongError(Exception):
    """Exception raised when trying to add a song that already exists."""
    pass

def add_song(title, artist, release_year, language, genre, local_filename, musicbrainz_id=None):
    """
    Adds a new song to the database and initializes its spaced repetition data.

    Args:
        title (str): The title of the song.
        artist (str): The artist of the song.
        release_year (int): The release year of the song.
        language (str): The language of the song.
        genre (str): The genre of the song.
        local_filename (str): The local filename of the song file.
        musicbrainz_id (str, optional): The MusicBrainz ID of the song. Defaults to None.

    Returns:
        int: The song_id of the newly added song.

    Raises:
        DuplicateSongError: If a song with the same local_filename or musicbrainz_id already exists.
    """
    try:
        cursor = get_cursor()
        cursor.execute("""
            INSERT INTO songs (title, artist, release_year, language, genre, local_filename, musicbrainz_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (title, artist, release_year, language, genre, local_filename, musicbrainz_id))

        song_id = cursor.lastrowid

        # Initialize spaced repetition data
        cursor.execute("""
            INSERT INTO spaced_repetition (song_id, next_review_date)
            VALUES (?, ?)
        """, (song_id, date.today()))

        cursor.connection.commit()
        return song_id
    except sqlite3.IntegrityError:
        cursor.connection.rollback()
        raise DuplicateSongError("A song with the same local filename or MusicBrainz ID already exists.")

def get_song_by_id(song_id):
    """
    Retrieves a single song's complete record by its song_id.

    Args:
        song_id (int): The ID of the song to retrieve.

    Returns:
        tuple: A tuple representing the song record, or None if not found.
    """
    cursor = get_cursor()
    cursor.execute("SELECT * FROM songs WHERE song_id = ?", (song_id,))
    return cursor.fetchone()

def get_all_songs():
    """
    Retrieves a list of all songs from the library.

    Returns:
        list: A list of tuples, where each tuple represents a song record.
    """
    cursor = get_cursor()
    cursor.execute("SELECT * FROM songs")
    return cursor.fetchall()
