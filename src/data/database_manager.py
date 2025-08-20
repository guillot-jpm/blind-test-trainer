# src/data/database_manager.py

"""
This module handles the connection to the SQLite database, ensuring that
a single, consistent connection is used throughout the application.
"""

import sqlite3
import datetime
import logging
from src.data.schema import ALL_TABLES

# This will hold the single, application-wide database connection.
_connection = None


def adapt_date_iso(val):
    """Adapt datetime.date to ISO 8601 string."""
    return val.isoformat()


def convert_date(val):
    """Convert ISO 8601 string to datetime.date object."""
    return datetime.date.fromisoformat(val.decode())


def connect(db_path):
    """
    Establishes a connection to the SQLite database.

    This function should be called once when the application starts.
    It handles connection errors gracefully by printing an error and
    ensuring the internal connection state is clean.
    """
    global _connection
    if _connection is not None:
        # Avoid creating a new connection if one already exists.
        return

    try:
        # Register the adapter and converter for date objects
        sqlite3.register_adapter(datetime.date, adapt_date_iso)
        sqlite3.register_converter("date", convert_date)

        # Using check_same_thread=False is a common practice for SQLite in
        # multi-threaded applications, like those with a separate GUI thread.
        # The `detect_types` flag allows using the registered converters.
        _connection = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES,
            check_same_thread=False
        )
    except sqlite3.Error as e:
        # In a real application, this should be logged to a file or a
        # dedicated logging service.
        logging.error(f"Database connection error: {e}")
        _connection = None  # Ensure connection is reset on failure.
        raise  # Re-raise the exception to be handled by the caller.


def disconnect():
    """
    Closes the database connection if it's currently open.

    This function should be called when the application is shutting down
    to ensure a clean exit.
    """
    global _connection
    if _connection:
        _connection.close()
        _connection = None


def get_cursor():
    """
    Returns a cursor from the current database connection.

    Raises:
        RuntimeError: If the database connection has not been established
                      by calling `connect()` first.
    """
    if _connection is None:
        raise RuntimeError(
            "Database connection is not established. Call connect() first."
        )
    return _connection.cursor()


def initialize_database():
    """
    Initializes the database by creating all necessary tables if they
    don't already exist.

    This function relies on an existing database connection, so `connect()`
    must be called before this function is invoked.
    """
    try:
        cursor = get_cursor()
        for table_query in ALL_TABLES:
            cursor.execute(table_query)
        _connection.commit()
    except (sqlite3.Error, RuntimeError) as e:
        # This will catch both SQL errors and errors from get_cursor()
        # if the connection isn't open.
        logging.error(f"Database initialization error: {e}")
        raise # Re-raise to let the caller know initialization failed.


def record_play_history(song_id, was_correct, reaction_time):
    """
    Records the outcome of a single play instance in the play_history table.

    Args:
        song_id (int): The ID of the song that was played.
        was_correct (bool): Whether the user's guess was correct.
        reaction_time (float): The time in seconds it took the user to react.
    """
    try:
        cursor = get_cursor()
        cursor.execute("""
            INSERT INTO play_history (song_id, play_timestamp, was_correct, reaction_time_seconds)
            VALUES (?, datetime('now'), ?, ?)
        """, (song_id, was_correct, reaction_time))
        cursor.connection.commit()
    except sqlite3.Error as e:
        logging.error(f"Failed to record play history: {e}")
        # Depending on the application's needs, you might want to rollback,
        # but for a single INSERT, it's less critical.
        cursor.connection.rollback()
        raise


def get_total_song_count():
    """
    Retrieves the total number of songs in the library.

    Returns:
        int: The total count of songs, or 0 if an error occurs.
    """
    try:
        cursor = get_cursor()
        cursor.execute("SELECT COUNT(*) FROM songs")
        # fetchone() will return a tuple, e.g., (15,)
        result = cursor.fetchone()
        return result[0] if result else 0
    except sqlite3.Error as e:
        logging.error(f"Failed to get total song count: {e}")
        return 0


def get_all_release_years():
    """
    Fetches all non-null release years from the songs table.

    Returns:
        list[int]: A list of release years. Returns an empty list on error.
    """
    try:
        cursor = get_cursor()
        cursor.execute("SELECT release_year FROM songs WHERE release_year IS NOT NULL")
        # fetchall() returns a list of tuples, e.g., [(1990,), (2004,)]
        return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logging.error(f"Failed to get release years: {e}")
        return []


def get_all_srs_intervals():
    """
    Fetches all current SRS interval days from the spaced_repetition table.

    Returns:
        list[int]: A list of interval days. Returns an empty list on error.
    """
    try:
        cursor = get_cursor()
        cursor.execute("SELECT current_interval_days FROM spaced_repetition")
        return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logging.error(f"Failed to get SRS intervals: {e}")
        return []
