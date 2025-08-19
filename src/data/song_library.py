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


def _create_srs_record(song_id, cursor):
    """
    Creates the initial spaced repetition record for a new song.

    This is an internal function and should be called within a transaction
    when a new song is added.

    Args:
        song_id (int): The ID of the new song.
        cursor: The database cursor to use for the operation.
    """
    # The `spaced_repetition` table has defaults for interval and ease factor.
    # We only need to provide the song_id and the initial next_review_date.
    cursor.execute("""
        INSERT INTO spaced_repetition (song_id, next_review_date)
        VALUES (?, ?)
    """, (song_id, date.today()))


def add_song(title, artist, release_year, local_filename, spotify_id=None):
    """
    Adds a new song to the database and initializes its spaced repetition data.

    Args:
        title (str): The title of the song.
        artist (str): The artist of the song.
        release_year (int): The release year of the song.
        local_filename (str): The local filename of the song file.
        spotify_id (str, optional): The Spotify Track ID. Defaults to None.

    Returns:
        int: The song_id of the newly added song.

    Raises:
        DuplicateSongError: If a song with the same local_filename or Spotify ID already exists.
    """
    try:
        cursor = get_cursor()
        cursor.execute("""
            INSERT INTO songs (title, artist, release_year, local_filename, spotify_id)
            VALUES (?, ?, ?, ?, ?)
        """, (title, artist, release_year, local_filename, spotify_id))

        song_id = cursor.lastrowid

        # Initialize spaced repetition data
        _create_srs_record(song_id, cursor)

        cursor.connection.commit()
        return song_id
    except sqlite3.IntegrityError:
        cursor.connection.rollback()
        raise DuplicateSongError("A song with the same local filename or Spotify ID already exists.")

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


def get_srs_data(song_id):
    """
    Retrieves the spaced repetition data for a specific song.

    Args:
        song_id (int): The ID of the song.

    Returns:
        tuple: A tuple containing the SRS data, or None if not found.
    """
    cursor = get_cursor()
    cursor.execute("SELECT * FROM spaced_repetition WHERE song_id = ?", (song_id,))
    return cursor.fetchone()


def update_srs_data(song_id, new_interval, new_ease_factor, next_review_date):
    """
    Updates the spaced repetition data for a song.

    Args:
        song_id (int): The ID of the song to update.
        new_interval (int): The new interval in days.
        new_ease_factor (float): The new ease factor.
        next_review_date (date): The next review date.
    """
    try:
        cursor = get_cursor()
        cursor.execute("""
            UPDATE spaced_repetition
            SET current_interval_days = ?, ease_factor = ?, next_review_date = ?
            WHERE song_id = ?
        """, (new_interval, new_ease_factor, next_review_date, song_id))
        cursor.connection.commit()
    except sqlite3.Error as e:
        print(f"Failed to update SRS data: {e}")
        cursor.connection.rollback()
        raise


def get_due_songs():
    """
    Retrieves a list of song_ids for all songs that are due for review.

    A song is considered due if its next_review_date is on or before
    the current date.

    Returns:
        list: A list of song_id integers that are due for review.
    """
    cursor = get_cursor()
    cursor.execute("""
        SELECT song_id FROM spaced_repetition WHERE next_review_date <= ?
    """, (date.today(),))
    # fetchall() returns a list of tuples, e.g., [(1,), (2,)].
    # We use a list comprehension to flatten it into [1, 2].
    return [item[0] for item in cursor.fetchall()]
