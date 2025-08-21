# src/data/song_library.py

"""
This module provides functions for managing the song library in the database.
It includes functions for adding, retrieving, and listing songs.
"""

import sqlite3
from datetime import date
import logging
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
        logging.info(
            f"Song '{title} by {artist}' successfully added to library."
        )
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


def get_all_song_ids():
    """
    Retrieves a list of all song_ids from the library.

    Returns:
        list: A list of all song_id integers.
    """
    cursor = get_cursor()
    cursor.execute("SELECT song_id FROM songs")
    return [item[0] for item in cursor.fetchall()]


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


def get_all_songs_for_view():
    """
    Retrieves a detailed list of all songs for the library management view.

    This function joins the 'songs' and 'spaced_repetition' tables to
    include the next review date for each song.

    Returns:
        list: A list of dictionaries, where each dictionary represents a song
              with its details.
    """
    cursor = get_cursor()
    cursor.execute("""
        SELECT
            s.song_id,
            s.title,
            s.artist,
            s.release_year,
            s.local_filename,
            sr.next_review_date
        FROM songs s
        LEFT JOIN spaced_repetition sr ON s.song_id = sr.song_id
        ORDER BY s.artist, s.title
    """)

    # Fetch all results and convert them into a list of dictionaries
    rows = cursor.fetchall()
    songs_list = []
    # Get column names from the cursor description
    column_names = [description[0] for description in cursor.description]
    for row in rows:
        songs_list.append(dict(zip(column_names, row)))

    return songs_list


def delete_songs_by_id(song_ids):
    """
    Deletes one or more songs from the database.

    This function removes records from 'songs', 'play_history', and
    'spaced_repetition' tables in a single transaction.

    Args:
        song_ids (list): A list of song_id integers to be deleted.
    """
    if not song_ids:
        return

    try:
        cursor = get_cursor()

        # The '?' placeholder syntax varies depending on the number of items
        placeholders = ', '.join('?' for _ in song_ids)

        # Note: Foreign key constraints with ON DELETE CASCADE handle this automatically
        # if the database schema is set up that way. If not, we must delete manually.
        # Assuming ON DELETE CASCADE is NOT set, for robustness.

        cursor.execute(f"DELETE FROM play_history WHERE song_id IN ({placeholders})", song_ids)
        cursor.execute(f"DELETE FROM spaced_repetition WHERE song_id IN ({placeholders})", song_ids)
        cursor.execute(f"DELETE FROM songs WHERE song_id IN ({placeholders})", song_ids)

        cursor.connection.commit()
    except sqlite3.Error as e:
        print(f"Failed to delete songs: {e}")
        cursor.connection.rollback()
        raise

def update_song_details(song_id, title, artist, release_year, spotify_id):
    """
    Updates the details for a specific song.

    Args:
        song_id (int): The ID of the song to update.
        title (str): The new title.
        artist (str): The new artist.
        release_year (int): The new release year.
        spotify_id (str): The new Spotify ID.
    """
    try:
        cursor = get_cursor()
        cursor.execute("""
            UPDATE songs
            SET title = ?,
                artist = ?,
                release_year = ?,
                spotify_id = ?
            WHERE song_id = ?
        """, (title, artist, release_year, spotify_id, song_id))
        cursor.connection.commit()
    except sqlite3.Error as e:
        print(f"Failed to update song details: {e}")
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
